"""Report writers: JUnit XML, JSON and TAP 13."""

import json
import os
import time
from xml.sax.saxutils import escape


def _fmt_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def write_junit(path, checks):
    total = len(checks)
    failed = sum(1 for c in checks if not c.ok)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<testsuites tests="%d" failures="%d" timestamp="%s">'
        % (total, failed, _fmt_ts()),
        '  <testsuite name="wmmr" tests="%d" failures="%d">'
        % (total, failed),
    ]
    for c in checks:
        lines.append('    <testcase classname="%s" name="%s">'
                     % (escape(c.group), escape(c.name)))
        if not c.ok:
            lines.append('      <failure message="%s"/>'
                         % escape(c.detail or "check failed"))
        lines.append('    </testcase>')
    lines.append('  </testsuite>')
    lines.append('</testsuites>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_json(path, checks):
    passed = sum(1 for c in checks if c.ok)
    failed = len(checks) - passed
    data = {
        "suite": "wmmr",
        "generated": _fmt_ts(),
        "passed": passed,
        "failed": failed,
        "checks": [
            {
                "group": c.group,
                "name": c.name,
                "ok": c.ok,
                "detail": c.detail,
            }
            for c in checks
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def write_tap(path, checks):
    lines = ["TAP version 13", "1..%d" % len(checks)]
    for i, c in enumerate(checks, 1):
        desc = c.name
        if not c.ok and c.detail:
            desc += " # " + c.detail
        lines.append("%s %d - %s" % ("ok" if c.ok else "not ok", i, desc))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_all_reports(reports, checks):
    """Write each configured report; returns list of (kind, path, ok, error)."""
    out = []
    for kind, path in reports:
        try:
            if kind == "junit":
                write_junit(path, checks)
            elif kind == "json":
                write_json(path, checks)
            elif kind == "tap":
                write_tap(path, checks)
            else:
                out.append((kind, path, False, "unknown report kind"))
                continue
            out.append((kind, path, True, ""))
        except (OSError, ValueError) as exc:
            out.append((kind, path, False, repr(exc)))
    return out
