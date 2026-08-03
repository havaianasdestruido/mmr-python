"""Entry point for the WMMR ctypes test suite.

Usage:
    python32\\python.exe run_tests.py [DLL-DIR] [options]

Options:
    --list                list every registered test and exit
    --filter PATTERN      run only tests whose group/dll/name contains PATTERN
                          (repeatable; OR across patterns)
    --skip PATTERN        skip tests matching PATTERN (repeatable)
    --retries N           re-run a failing test function up to N times
    --junit FILE          write a JUnit XML report
    --json FILE           write a JSON report
    --tap FILE            write a TAP 13 report
    --quiet               print only the summary line

Exit codes: 0 all checks pass; 1 one or more checks fail; 2 usage error.
The DLL directory defaults to $WMMR_DLL_DIR, else the standard Debug path.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wmmr import runner, reports  # noqa: E402

DEFAULT_DLL_DIR = r"C:\Users\mcmco\Desktop\WMMR\build_clean\bin\Debug"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="run_tests.py",
        description="Run the WMMR ctypes test suite against 32-bit core DLLs.",
    )
    parser.add_argument("dll_dir", nargs="?", default=None,
                        help="directory holding the 32-bit WMMR DLLs")
    parser.add_argument("--list", action="store_true",
                        help="list registered tests and exit")
    parser.add_argument("--filter", action="append", default=[],
                        metavar="PATTERN",
                        help="run only matching tests (repeatable, OR)")
    parser.add_argument("--skip", action="append", default=[],
                        metavar="PATTERN",
                        help="skip matching tests (repeatable)")
    parser.add_argument("--retries", type=int, default=0, metavar="N",
                        help="retry failing test functions up to N times")
    parser.add_argument("--junit", metavar="FILE")
    parser.add_argument("--json", metavar="FILE")
    parser.add_argument("--tap", metavar="FILE")
    parser.add_argument("--quiet", action="store_true",
                        help="only print the summary line")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.retries < 0:
        parser.error("--retries must be >= 0")

    if args.list:
        print("Registered WMMR tests:")
        for group, dll, fn in runner.iter_tests():
            label = "%s (%s)" % (group, dll) if dll else group
            print("  %-22s %s" % (label, fn.__name__))
        return 0

    dll_dir = args.dll_dir or os.environ.get("WMMR_DLL_DIR") or DEFAULT_DLL_DIR
    if not os.path.isdir(dll_dir):
        parser.error("DLL directory does not exist: %s" % dll_dir)

    selected = runner.select_tests(args.filter, args.skip)
    if not selected:
        print("error: no tests matched --filter/--skip", file=sys.stderr)
        return 2

    checks, passed, failed = runner.run_all(
        dll_dir, filters=args.filter, skips=args.skip, retries=args.retries)

    if not args.quiet:
        for c in checks:
            print("%s %s%s" % (
                "PASS" if c.ok else "FAIL", c.name,
                " -- %s" % c.detail if c.detail else ""), flush=True)
    print("SUMMARY PASS=%d FAIL=%d" % (passed, failed))

    reports_cfg = [
        ("junit", args.junit),
        ("json", args.json),
        ("tap", args.tap),
    ]
    reports_cfg = [(kind, path) for kind, path in reports_cfg if path]
    report_errors = 0
    if reports_cfg:
        for kind, path, ok, err in reports.write_all_reports(reports_cfg, checks):
            if ok:
                print("REPORT %-6s -> %s" % (kind.upper(), path))
            else:
                print("REPORT %-6s ERROR writing %s: %s"
                      % (kind.upper(), path, err), file=sys.stderr)
                report_errors += 1

    if failed:
        return 1
    if report_errors:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
