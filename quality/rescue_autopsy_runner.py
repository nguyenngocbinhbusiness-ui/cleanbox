"""
Rescue autopsy report generator.

This reconstructs rune-rescue health artifacts from:
- coverage json
- radon cc json
- bandit json

Scoring model is inferred from existing rescue artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Inferred constants (fit against existing rescue_autopsy_final.json)
WEIGHT_COVERAGE = 0.5625174783611014
WEIGHT_LOC = 0.20413401276883908
WEIGHT_COMPLEXITY = 0.23334850887005948
LOC_DIVISOR = 10.960979643755959
COMPLEXITY_MULTIPLIER = 6.584493256460363
ISSUE_PENALTY = 2.0572635514632847
MODEL_BIAS = 2.439451298221762


@dataclass(frozen=True)
class ModuleStats:
    name: str
    loc: int
    cyclomatic_complexity: int
    test_coverage: float
    issue_count: int
    health: float


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def _module_name_from_file(path: str) -> str | None:
    p = _normalize_path(path)
    if p == "src/app.py":
        return "app"
    if p == "src/main.py":
        return "main"
    if p == "src/__init__.py":
        return "__init__"
    if p == "src/features/__init__.py":
        return "features.__init__.py"
    if p == "src/ui/__init__.py":
        return "ui.__init__.py"
    if p == "src/ui/main_window.py":
        return "ui.main_window.py"
    if p == "src/ui/tray_icon.py":
        return "ui.tray_icon.py"
    if p.startswith("src/features/"):
        parts = p.split("/")
        if len(parts) >= 4:
            return f"features.{parts[2]}.{Path(p).stem}"
        if len(parts) >= 3:
            return f"features.{parts[2]}"
    if p.startswith("src/shared/"):
        parts = p.split("/")
        if len(parts) >= 4:
            return f"shared.{parts[2]}"
        return "shared.core"
    if p.startswith("src/ui/views/"):
        return f"ui.views.{Path(p).stem}"
    if p.startswith("src/ui/storage/"):
        return f"ui.storage.{Path(p).stem}"
    if p.startswith("src/ui/components/"):
        return "ui.components"
    return None


def _iter_source_files() -> Iterable[Path]:
    src_dir = PROJECT_ROOT / "src"
    yield from sorted(src_dir.rglob("*.py"))


def _compute_loc_by_module() -> Dict[str, int]:
    module_loc: Dict[str, int] = {}
    for file_path in _iter_source_files():
        rel = file_path.relative_to(PROJECT_ROOT).as_posix()
        module = _module_name_from_file(rel)
        if module is None:
            continue
        loc = len(file_path.read_text(encoding="utf-8").splitlines())
        module_loc[module] = module_loc.get(module, 0) + loc
    return module_loc


def _compute_coverage_by_module(coverage_json: Path) -> Dict[str, float]:
    data = json.loads(coverage_json.read_text(encoding="utf-8"))
    file_entries = data.get("files", {})
    covered_by_module: Dict[str, float] = {}
    statements_by_module: Dict[str, float] = {}

    for raw_path, file_data in file_entries.items():
        rel = _normalize_path(raw_path)
        module = _module_name_from_file(rel)
        if module is None:
            continue

        summary = file_data.get("summary", {})
        statements = float(summary.get("num_statements", 0) or 0)
        covered = float(summary.get("covered_lines", 0) or 0)

        statements_by_module[module] = statements_by_module.get(module, 0.0) + statements
        covered_by_module[module] = covered_by_module.get(module, 0.0) + covered

    coverage_by_module: Dict[str, float] = {}
    for module, total_statements in statements_by_module.items():
        if total_statements <= 0:
            coverage_by_module[module] = 100.0
            continue
        coverage_by_module[module] = (covered_by_module[module] / total_statements) * 100.0
    return coverage_by_module


def _compute_max_complexity_by_module(radon_json: Path) -> Dict[str, int]:
    data = json.loads(radon_json.read_text(encoding="utf-8"))
    result: Dict[str, int] = {}

    for raw_path, entries in data.items():
        rel = _normalize_path(raw_path)
        module = _module_name_from_file(rel)
        if module is None:
            continue
        max_cc = 0
        for item in entries or []:
            complexity = int(item.get("complexity", 0) or 0)
            if complexity > max_cc:
                max_cc = complexity
        current = result.get(module, 0)
        if max_cc > current:
            result[module] = max_cc
    return result


def _compute_issue_count_by_module(bandit_json: Path) -> Dict[str, int]:
    data = json.loads(bandit_json.read_text(encoding="utf-8"))
    issue_counts: Dict[str, int] = {}
    for finding in data.get("results", []):
        rel = _normalize_path(finding.get("filename", ""))
        module = _module_name_from_file(rel)
        if module is None:
            continue
        issue_counts[module] = issue_counts.get(module, 0) + 1
    return issue_counts


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _compute_module_health(
    coverage: float, loc: int, max_cc: int, issue_count: int
) -> float:
    loc_score = _clamp(100.0 - (loc / LOC_DIVISOR))
    complexity_score = _clamp(100.0 - (max_cc * COMPLEXITY_MULTIPLIER))
    health = (
        (WEIGHT_COVERAGE * coverage)
        + (WEIGHT_LOC * loc_score)
        + (WEIGHT_COMPLEXITY * complexity_score)
        - (ISSUE_PENALTY * issue_count)
        + MODEL_BIAS
    )
    return round(_clamp(health), 2)


def _score_pattern(module: ModuleStats) -> str:
    if module.loc > 500:
        return "Strangler Fig"
    if module.cyclomatic_complexity > 10:
        return "Extract & Simplify"
    if module.cyclomatic_complexity > 6:
        return "Branch by Abstraction"
    return "Expand-Migrate-Contract"


def _build_modules(
    coverage_json: Path, radon_json: Path, bandit_json: Path
) -> List[ModuleStats]:
    loc_by_module = _compute_loc_by_module()
    coverage_by_module = _compute_coverage_by_module(coverage_json)
    max_cc_by_module = _compute_max_complexity_by_module(radon_json)
    issue_count_by_module = _compute_issue_count_by_module(bandit_json)

    all_modules = sorted(set(loc_by_module) | set(coverage_by_module) | set(max_cc_by_module))
    modules: List[ModuleStats] = []

    for module_name in all_modules:
        loc = int(loc_by_module.get(module_name, 0))
        coverage = float(coverage_by_module.get(module_name, 100.0))
        max_cc = int(max_cc_by_module.get(module_name, 0))
        issue_count = int(issue_count_by_module.get(module_name, 0))
        health = _compute_module_health(
            coverage=coverage,
            loc=loc,
            max_cc=max_cc,
            issue_count=issue_count,
        )
        modules.append(
            ModuleStats(
                name=module_name,
                loc=loc,
                cyclomatic_complexity=max_cc,
                test_coverage=round(coverage, 2),
                issue_count=issue_count,
                health=health,
            )
        )
    return sorted(modules, key=lambda m: m.health)


def _compute_overall_health(modules: List[ModuleStats]) -> float:
    total_loc = sum(m.loc for m in modules)
    if total_loc <= 0:
        return 0.0
    weighted = sum(m.health * m.loc for m in modules)
    return round(weighted / total_loc, 2)


def _to_json_payload(
    modules: List[ModuleStats], overall_health: float, coverage_json: Path, radon_json: Path, bandit_json: Path
) -> Dict[str, object]:
    return {
        "health_score": overall_health,
        "modules": [
            {
                "name": m.name,
                "loc": m.loc,
                "cyclomatic_complexity": m.cyclomatic_complexity,
                "test_coverage": m.test_coverage,
                "health": m.health,
            }
            for m in modules
        ],
        "inputs": {
            "coverage_file": str(coverage_json.as_posix()),
            "radon_file": str(radon_json.as_posix()),
            "bandit_file": str(bandit_json.as_posix()),
        },
        "model": {
            "coverage_weight": WEIGHT_COVERAGE,
            "loc_weight": WEIGHT_LOC,
            "complexity_weight": WEIGHT_COMPLEXITY,
            "loc_divisor": LOC_DIVISOR,
            "complexity_multiplier": COMPLEXITY_MULTIPLIER,
            "issue_penalty": ISSUE_PENALTY,
            "bias": MODEL_BIAS,
            "overall_aggregation": "loc_weighted_average",
        },
    }


def _format_markdown_report(modules: List[ModuleStats], overall_health: float) -> str:
    lines = [
        "# Rescue Autopsy Report",
        "",
        f"- Health score: **{overall_health:.2f} / 100**",
        f"- Modules analyzed: **{len(modules)}**",
        "",
        "## Weakest Modules",
        "",
        "| Module | LOC | Max CC | Coverage | Issues | Health | Pattern |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for module in modules[:8]:
        lines.append(
            "| "
            f"{module.name} | {module.loc} | {module.cyclomatic_complexity} | "
            f"{module.test_coverage:.2f}% | {module.issue_count} | {module.health:.2f} | "
            f"{_score_pattern(module)} |"
        )
    return "\n".join(lines) + "\n"


def _compare_with_reference(modules: List[ModuleStats], reference_json: Path) -> Tuple[float, float]:
    reference = json.loads(reference_json.read_text(encoding="utf-8"))
    expected = {item["name"]: float(item["health"]) for item in reference.get("modules", [])}
    errors: List[float] = []
    for module in modules:
        if module.name not in expected:
            continue
        errors.append(module.health - expected[module.name])
    if not errors:
        return 0.0, 0.0
    mse = sum(err * err for err in errors) / len(errors)
    rmse = mse ** 0.5
    max_abs_error = max(abs(err) for err in errors)
    return rmse, max_abs_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate rescue autopsy artifacts.")
    parser.add_argument(
        "--coverage-json",
        type=Path,
        default=Path("quality/reports/rescue_coverage_final.json"),
    )
    parser.add_argument(
        "--radon-json",
        type=Path,
        default=Path("quality/reports/rescue_radon_final.json"),
    )
    parser.add_argument(
        "--bandit-json",
        type=Path,
        default=Path("quality/reports/rescue_bandit_final.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("quality/reports/rescue_autopsy_final.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("quality/reports/rescue_autopsy_final.md"),
    )
    parser.add_argument(
        "--fit-reference-json",
        type=Path,
        default=Path("quality/reports/rescue_autopsy_final.json"),
        help="Optional: compare generated module health against an existing artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    reference_payload = None
    if args.fit_reference_json.exists():
        reference_payload = json.loads(args.fit_reference_json.read_text(encoding="utf-8"))

    modules = _build_modules(
        coverage_json=args.coverage_json,
        radon_json=args.radon_json,
        bandit_json=args.bandit_json,
    )
    overall_health = _compute_overall_health(modules)

    output_payload = _to_json_payload(
        modules=modules,
        overall_health=overall_health,
        coverage_json=args.coverage_json,
        radon_json=args.radon_json,
        bandit_json=args.bandit_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")
    args.output_md.write_text(
        _format_markdown_report(modules=modules, overall_health=overall_health),
        encoding="utf-8",
    )

    print(f"rescue_health_score={overall_health:.2f}")
    print(f"modules={len(modules)}")
    print(f"wrote_json={args.output_json.as_posix()}")
    print(f"wrote_md={args.output_md.as_posix()}")

    if reference_payload is not None:
        tmp_reference = args.output_json.parent / ".tmp-rescue-fit-reference.json"
        tmp_reference.write_text(json.dumps(reference_payload), encoding="utf-8")
        rmse, max_abs = _compare_with_reference(modules=modules, reference_json=tmp_reference)
        tmp_reference.unlink(missing_ok=True)
        print(f"fit_rmse={rmse:.4f}")
        print(f"fit_max_abs_error={max_abs:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
