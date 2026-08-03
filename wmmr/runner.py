"""Discovery, selection and execution of WMMR ctypes checks.

A check is a (group, name, ok, detail) record.  Test functions receive a
:class:`Session` and call ``session.record(...)``.  The runner handles
filtering (--filter/--skip), retries and exit-code computation.
"""

from wmmr.contracts import GROUPS
from wmmr.workflows import WORKFLOWS


class Check(object):
    __slots__ = ("group", "name", "ok", "detail")

    def __init__(self, group, name, ok, detail=""):
        self.group = group
        self.name = name
        self.ok = bool(ok)
        self.detail = detail


class Session(object):
    """Result collector handed to every test function."""

    def __init__(self, dll_dir):
        self.dll_dir = dll_dir
        self.checks = []

    def record(self, group, name, ok, detail=""):
        self.checks.append(Check(group, name, ok, detail))


def iter_tests():
    """Yield (group, dll, test_fn) for every registered test."""
    for module in GROUPS:
        for fn in module.TESTS:
            yield module.GROUP, getattr(module, "DLL", ""), fn
    for fn in WORKFLOWS:
        yield "workflows", "", fn


def _test_key(group, dll, fn):
    return u"%s:%s:%s" % (group, dll, fn.__name__)


def _matches_any(patterns, group, dll, fn):
    """True if ANY pattern matches; False when no patterns given."""
    if not patterns:
        return False
    key = _test_key(group, dll, fn)
    return any(p.lower() in key.lower() for p in patterns)


def select_tests(filters=(), skips=()):
    """Return [(group, dll, fn)] honoring --filter / --skip patterns."""
    filters = [f for f in filters if f]
    skips = [s for s in skips if s]
    selected = []
    for group, dll, fn in iter_tests():
        if _matches_any(filters, group, dll, fn) or not filters:
            if not _matches_any(skips, group, dll, fn):
                selected.append((group, dll, fn))
    return selected


def run_test(group, fn, session, retries=0):
    """Run a test function, honoring retries; extend session with its checks."""
    attempts = []
    for _ in range(retries + 1):
        sub = Session(session.dll_dir)
        try:
            fn(sub)
        except Exception as exc:  # noqa: BLE001
            sub.record(group, "%s.%s" % (group, fn.__name__), False,
                       "raised %r" % (exc,))
        attempts.append(sub)
        if sub.checks and all(c.ok for c in sub.checks):
            break
    if not attempts or not attempts[0].checks:
        session.record(group, "%s.%s" % (group, fn.__name__), False,
                       "produced no checks")
        return
    # Prefer the first attempt with zero failures, else the first attempt.
    best = attempts[0]
    for sub in attempts:
        if sub.checks and all(c.ok for c in sub.checks):
            best = sub
            break
    session.checks.extend(best.checks)


def run_all(dll_dir, filters=(), skips=(), retries=0):
    """Run selected tests; return (checks, passed, failed)."""
    session = Session(dll_dir)
    for group, _dll, fn in select_tests(filters, skips):
        run_test(group, fn, session, retries)
    passed = sum(1 for c in session.checks if c.ok)
    failed = len(session.checks) - passed
    return session.checks, passed, failed
