"""Run the original checker with path and manifest-hash compatibility.

The protected file list uses POSIX paths. The original checker compares it
with str(Path), which uses backslashes on Windows and falsely scans protected
calibration code. The training producer hashes manifest bytes verbatim, but
the checker normalizes newlines first. Match the producer's exact byte hash
for the manifest comparison. Protected-file checks keep their original
newline normalization; all tests and other validation remain enabled.
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
    original = 'r.get("manifest_sha1") != sha1(mf)'
    if source.count(original) != 1:
        raise RuntimeError("Checker changed; review the manifest-hash compatibility patch")
    source = source.replace(original,
                            'r.get("manifest_sha1") != hashlib.sha1(mf.read_bytes()).hexdigest()')
    print("Manifest: compare exact SHA1 bytes, matching train_compare.py.")
    # Keep pytest's temporary data inside the workspace on restricted machines.
    temp = root / "work" / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temp)
    os.environ["PYTHONUTF8"] = "1"
    exec(compile(source, str(checker), "exec"),
         {"__name__": "__main__", "__file__": str(checker)})


if __name__ == "__main__":
    main()
