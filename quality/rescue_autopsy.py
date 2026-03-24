"""Generate rescue autopsy score artifacts from coverage/radon/bandit reports.

This implements the canonical formula recovered from the original rescue run
session logs and reproduces `rescue_autopsy_final.json` format.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _norm(path_str: str) -> str:
    return path_str.replace("\\", "/").lstrip("./")


def _module_of(rel: str) -> str:
    rel = _norm(rel)
    if rel.startswith("src/"):
        rel = rel[4:]
    parts = rel.split("/")
    if len(parts) == 1:
        return parts[0].replace(".py", "")
    if parts[0] in {"features", "ui"}:
        return f"{parts[0]}.{parts[1]}"
    return parts[0]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def generate_autopsy(
    root: Path,
    coverage_file: Path,
    radon_file: Path,
    bandit_file: Path,
    out_json: Path,
    out_md: Path,
    baseline_file: Path | None = None,
) -> float:
    coverage = _read_json(coverage_file)
    radon = _read_json(radon_file)
    bandit = _read_json(bandit_file)

    py_files = [p for p in (root / "src").rglob("*.py")]
    module_files: dict[str, list[str]] = defaultdict(list)
    for pyf in py_files:
        rel = _norm(str(pyf.relative_to(root)))
        module_files[_module_of(rel)].append(rel)

    coverage_files = coverage.get("files", {})
    coverage_map: dict[str, float] = {}
    for path_str, data in coverage_files.items():
        path_norm = _norm(path_str)
        summary = data.get("summary", {})
        num_statements = summary.get("num_statements", 0) or 0
        covered_lines = summary.get("covered_lines", 0) or 0
        cov = (covered_lines / num_statements * 100.0) if num_statements else 100.0
        coverage_map[path_norm] = cov

    radon_map: dict[str, int] = {}
    for path_str, entries in radon.items():
        path_norm = _norm(path_str)
        max_cc = 0
        for entry in entries or []:
            max_cc = max(max_cc, int(entry.get("complexity", 0) or 0))
        radon_map[path_norm] = max_cc

    bandit_results = bandit.get("results", [])
    bandit_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in bandit_results:
        fname = _norm(result.get("filename", ""))
        bandit_by_file[fname].append(
            {
                "severity": result.get("issue_severity", "LOW"),
            }
        )

    module_rows: list[dict[str, Any]] = []
    for module, files in sorted(module_files.items()):
        loc = 0
        cov_num = 0.0
        cov_den = 0
        max_cc = 0
        sec_penalty = 0

        for rel in files:
            file_path = root / rel
            try:
                lines = sum(1 for _ in file_path.open("r", encoding="utf-8"))
            except UnicodeDecodeError:
                lines = sum(
                    1 for _ in file_path.open("r", encoding="utf-8", errors="ignore")
                )

            loc += lines
            file_cov = coverage_map.get(rel, 0.0)
            cov_num += file_cov * lines
            cov_den += lines
            max_cc = max(max_cc, radon_map.get(rel, 0))

            for issue in bandit_by_file.get(rel, []):
                sev = (issue.get("severity") or "LOW").upper()
                if sev == "HIGH":
                    sec_penalty += 12
                elif sev == "MEDIUM":
                    sec_penalty += 6
                else:
                    sec_penalty += 2

        coverage_pct = (cov_num / cov_den) if cov_den else 100.0
        complexity_score = max(0.0, 100.0 - (max_cc * 5.0))
        size_score = max(0.0, 100.0 - max(0.0, loc - 120) / 8.0)

        health = max(
            0.0,
            min(
                100.0,
                0.55 * coverage_pct
                + 0.30 * complexity_score
                + 0.15 * size_score
                - sec_penalty,
            ),
        )

        module_rows.append(
            {
                "name": module,
                "loc": int(loc),
                "cyclomatic_complexity": int(max_cc),
                "test_coverage": round(coverage_pct, 2),
                "health": round(health, 2),
            }
        )

    sum_loc = sum(module["loc"] for module in module_rows) or 1
    overall = sum(module["health"] * module["loc"] for module in module_rows) / sum_loc

    out = {
        "health_score": round(overall, 2),
        "modules": sorted(module_rows, key=lambda module: module["health"]),
        "inputs": {
            "coverage_file": str(coverage_file.relative_to(root)).replace("\\", "/"),
            "radon_file": str(radon_file.relative_to(root)).replace("\\", "/"),
            "bandit_file": str(bandit_file.relative_to(root)).replace("\\", "/"),
        },
    }
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    baseline_score = 0.0
    if baseline_file and baseline_file.exists():
        baseline_score = float(_read_json(baseline_file).get("health_score", 0))

    md_lines: list[str] = [
        "# Rescue Final Autopsy Report",
        "",
        f"- Baseline health: **{baseline_score} / 100**",
        f"- Final health: **{out['health_score']} / 100**",
        f"- Improvement: **{round(out['health_score'] - baseline_score, 2)}** points",
        "",
        "## Weakest Modules (Final)",
        "",
        "| Module | LOC | Max CC | Coverage | Health |",
        "|---|---:|---:|---:|---:|",
    ]
    for module in out["modules"][:8]:
        md_lines.append(
            "| {name} | {loc} | {cc} | {cov}% | {health} |".format(
                name=module["name"],
                loc=module["loc"],
                cc=module["cyclomatic_complexity"],
                cov=module["test_coverage"],
                health=module["health"],
            )
        )
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return float(out["health_score"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(".").resolve())
    parser.add_argument(
        "--coverage",
        type=Path,
        default=Path("quality/reports/rescue_coverage_final.json"),
    )
    parser.add_argument(
        "--radon",
        type=Path,
        default=Path("quality/reports/rescue_radon_final.json"),
    )
    parser.add_argument(
        "--bandit",
        type=Path,
        default=Path("quality/reports/rescue_bandit_final.json"),
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("quality/reports/rescue_autopsy_final.json"),
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("quality/reports/rescue_autopsy_final.md"),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("quality/reports/rescue_autopsy.json"),
    )

    args = parser.parse_args()
    root = args.root.resolve()
    score = generate_autopsy(
        root=root,
        coverage_file=(root / args.coverage).resolve(),
        radon_file=(root / args.radon).resolve(),
        bandit_file=(root / args.bandit).resolve(),
        out_json=(root / args.out_json).resolve(),
        out_md=(root / args.out_md).resolve(),
        baseline_file=(root / args.baseline).resolve(),
    )
    print(f"rescue_health_score={score:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
