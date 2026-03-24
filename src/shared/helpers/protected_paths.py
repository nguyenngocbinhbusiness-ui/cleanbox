"""Protected path set construction for Windows system safety checks."""
import os


def build_protected_path_sets() -> tuple[frozenset, frozenset]:
    """Build exact and prefix protected path sets from environment + static roots."""
    exact_paths = set()
    protected_prefixes = set()

    env_vars = [
        "WINDIR",
        "SYSTEMROOT",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMDATA",
        "APPDATA",
        "LOCALAPPDATA",
        "USERPROFILE",
        "SYSTEMDRIVE",
        "HOMEDRIVE",
        "COMMONPROGRAMFILES",
        "COMMONPROGRAMFILES(X86)",
    ]
    recursive_env_vars = {
        "WINDIR",
        "SYSTEMROOT",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMDATA",
        "COMMONPROGRAMFILES",
        "COMMONPROGRAMFILES(X86)",
    }
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            normalized = os.path.normcase(os.path.realpath(value))
            exact_paths.add(normalized)
            if var in recursive_env_vars:
                protected_prefixes.add(normalized)

    windir = os.environ.get("WINDIR", r"C:\Windows")
    sys_drive = os.environ.get("SYSTEMDRIVE", "C:")
    static_paths = [
        os.path.join(windir, "System32"),
        os.path.join(windir, "SysWOW64"),
        os.path.join(windir, "WinSxS"),
        sys_drive + os.sep,
        sys_drive + os.sep + "Recovery",
        sys_drive + os.sep + "$Recycle.Bin",
        sys_drive + os.sep + "System Volume Information",
        sys_drive + os.sep + "Users",
    ]
    for candidate in static_paths:
        normalized = os.path.normcase(os.path.realpath(candidate))
        exact_paths.add(normalized)
        if candidate.endswith(os.sep):
            continue
        if candidate == os.path.join(windir, "System32"):
            protected_prefixes.add(normalized)
        elif candidate == os.path.join(windir, "SysWOW64"):
            protected_prefixes.add(normalized)
        elif candidate == os.path.join(windir, "WinSxS"):
            protected_prefixes.add(normalized)
        elif candidate == sys_drive + os.sep + "Recovery":
            protected_prefixes.add(normalized)
        elif candidate == sys_drive + os.sep + "$Recycle.Bin":
            protected_prefixes.add(normalized)
        elif candidate == sys_drive + os.sep + "System Volume Information":
            protected_prefixes.add(normalized)

    return frozenset(exact_paths), frozenset(protected_prefixes)
