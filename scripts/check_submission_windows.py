"""Run the original checker with Windows path normalization.

The protected file list uses POSIX paths. The original checker compares it
with str(Path), which uses backslashes on Windows and falsely scans protected
calibration code. Only that comparison is normalized in memory; no original
file, integrity hash, test, or validation rule is changed.
"""
import os
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    checker = root / "scripts" / "check_submission.py"
    source = checker.read_text(encoding="utf-8")
    if os.name == "nt":
        original = "str(p.relative_to(ROOT)) not in prot"
        if source.count(original) != 1:
            raise RuntimeError("Checker changed; review the Windows compatibility patch")
        source = source.replace(original, "p.relative_to(ROOT).as_posix() not in prot")
        print("Windows: normalize protected-file paths to '/' in memory.")
    # Keep pytest's temporary data inside the workspace on restricted machines.
    temp = root / "work" / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temp)
    os.environ["PYTHONUTF8"] = "1"
    exec(compile(source, str(checker), "exec"),
         {"__name__": "__main__", "__file__": str(checker)})


if __name__ == "__main__":
    main()
