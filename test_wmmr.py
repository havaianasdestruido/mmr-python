"""Legacy single-file entry point, preserved for backward compatibility.

The full suite now lives in the ``wmmr`` package.  This module keeps the
old ``test_wmmr.main([dll_dir])`` entry point working so pre-existing
scripts/CI that imported it do not break; the 16 original checks are part
of the new framework under their original names.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wmmr import runner  # noqa: E402

DEFAULT_DLL_DIR = r"C:\Users\mcmco\Desktop\WMMR\build_clean\bin\Debug"


def run_all(dll_dir):
    checks, passed, failed = runner.run_all(dll_dir)
    for c in checks:
        print("%s %s%s" % (
            "PASS" if c.ok else "FAIL", c.name,
            " -- %s" % c.detail if c.detail else ""), flush=True)
    print("SUMMARY PASS=%d FAIL=%d" % (passed, failed))
    return 0 if failed == 0 else 1


def main(argv):
    dll_dir = argv[0] if argv else os.environ.get("WMMR_DLL_DIR") or DEFAULT_DLL_DIR
    if not os.path.isdir(dll_dir):
        print("error: DLL directory does not exist: %s" % dll_dir)
        return 2
    return run_all(dll_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
