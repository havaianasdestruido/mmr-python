"""ctypes usage tests for the 32-bit WMMR core DLLs.

REQUIRES A 32-BIT PYTHON.  The WMMR DLLs in build_clean\\bin\\Debug are
32-bit (x86); ctypes running in a 64-bit process cannot load them
("cannot load 32-bit DLL").  Use a 32-bit CPython (e.g. the embeddable
python-*-embed-win32.zip) and run:

    python32\\python.exe run_tests.py <path-to-bin-Debug>

The exported entry points exercised here are __stdcall (WINAPI) except
MovieMakerMain which is __cdecl.  __stdcall functions are therefore bound
with ctypes.WINFUNCTYPE so the 32-bit ctypes layer uses the stdcall
calling convention; MovieMakerMain is bound through a plain CDLL-loaded
module with the default (cdecl) convention.
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys

# ---------------------------------------------------------------------------
# HRESULT / constants
# ---------------------------------------------------------------------------
S_OK = 0x00000000
CLASS_E_CLASSNOTAVAILABLE = 0x80040111
E_NOTIMPL = 0x80004001

# wintypes in the 32-bit embeddable CPython does not ship HRESULT/GUID;
# define them explicitly (GUID layout matches the Win32 GUID).
HRESULT = ctypes.c_long


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]

DEFAULT_DLL_DIR = r"C:\Users\mcmco\Desktop\WMMR\build_clean\bin\Debug"

RESULTS = []  # list of (test_name, ok, detail)


def record(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("PASS %s" % name if ok else "FAIL %s -- %s" % (name, detail), flush=True)


# ---------------------------------------------------------------------------
# Binding helpers
# ---------------------------------------------------------------------------
def bind_stdcall(dll, name, restype, *argtypes):
    """Bind an exported __stdcall function with an explicit prototype."""
    return ctypes.WINFUNCTYPE(restype, *argtypes)((name, dll))


def bind_cdecl(dll, name, restype, *argtypes):
    """Bind an exported __cdecl function with an explicit prototype."""
    return ctypes.CFUNCTYPE(restype, *argtypes)((name, dll))


# ---------------------------------------------------------------------------
# wlidcli.dll
# ---------------------------------------------------------------------------
def test_wlidcli(dll_dir):
    dll = ctypes.WinDLL(os.path.join(dll_dir, "wlidcli.dll"))

    WLCheckCredentials = bind_stdcall(
        dll, "WLCheckCredentials", HRESULT, wt.LPCWSTR)
    WLClogin = bind_stdcall(
        dll, "WLClogin", HRESULT,
        wt.HWND, wt.LPCWSTR, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
    WLCreateIdentityHandle = bind_stdcall(
        dll, "WLCreateIdentityHandle", ctypes.c_uint32)
    WLGetEnvironment = bind_stdcall(
        dll, "WLGetEnvironment", HRESULT,
        ctypes.POINTER(ctypes.c_void_p))
    WLGetTicket = bind_stdcall(
        dll, "WLGetTicket", HRESULT,
        ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p))
    WLFreeMemory = bind_stdcall(dll, "WLFreeMemory", None, ctypes.c_void_p)
    WLIsSignedIn = bind_stdcall(
        dll, "WLIsSignedIn", wt.BOOL, ctypes.c_uint32)

    # WLCheckCredentials(LPCWSTR) -> S_OK
    hr = WLCheckCredentials(u"user@example.com")
    record("wlidcli.WLCheckCredentials", hr == S_OK, "HRESULT=0x%08X" % hr)

    # WLGetEnvironment(LPCWSTR*) -> S_OK, "production", freed via WLFreeMemory
    env_buf = ctypes.c_void_p()
    hr = WLGetEnvironment(ctypes.byref(env_buf))
    env = ctypes.cast(env_buf, ctypes.c_wchar_p).value
    WLFreeMemory(env_buf)
    record("wlidcli.WLGetEnvironment",
           hr == S_OK and env == "production",
           "HRESULT=0x%08X value=%r" % (hr, env))

    # WLCreateIdentityHandle -> DWORD, increments starting at 0x1000
    h1 = WLCreateIdentityHandle()
    h2 = WLCreateIdentityHandle()
    record("wlidcli.WLCreateIdentityHandle",
           h1 >= 0x1000 and h2 == h1 + 1,
           "h1=0x%X h2=0x%X" % (h1, h2))

    # WLClogin(HWND, LPCWSTR, DWORD, LPVOID*) -> S_OK and signs the identity in
    token = ctypes.c_void_p()
    hr = WLClogin(None, u"user@example.com", h1, ctypes.byref(token))
    record("wlidcli.WLClogin", hr == S_OK, "HRESULT=0x%08X" % hr)
    record("wlidcli.WLIsSignedIn",
           WLIsSignedIn(h1) != 0,
           "signed-in for handle 0x%X" % h1)

    # WLGetTicket(DWORD, LPWSTR*) -> S_OK, "ticket=" substring, WLFreeMemory
    ticket_buf = ctypes.c_void_p()
    hr = WLGetTicket(h1, ctypes.byref(ticket_buf))
    ticket = ctypes.cast(ticket_buf, ctypes.c_wchar_p).value
    WLFreeMemory(ticket_buf)
    record("wlidcli.WLGetTicket",
           hr == S_OK and "ticket=" in ticket,
           "HRESULT=0x%08X value=%r" % (hr, ticket))


# ---------------------------------------------------------------------------
# uxctl.dll
# ---------------------------------------------------------------------------
def test_uxctl(dll_dir):
    dll = ctypes.WinDLL(os.path.join(dll_dir, "uxctl.dll"))

    UxControlsInitProcess = bind_stdcall(
        dll, "UxControlsInitProcess", HRESULT)
    UxControlsCreateObject = bind_stdcall(
        dll, "UxControlsCreateObject", HRESULT,
        ctypes.POINTER(GUID), ctypes.POINTER(GUID),
        ctypes.POINTER(ctypes.c_void_p))
    UxControlsUninitProcess = bind_stdcall(
        dll, "UxControlsUninitProcess", None)

    hr = UxControlsInitProcess()
    record("uxctl.UxControlsInitProcess", hr == S_OK, "HRESULT=0x%08X" % hr)

    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    hr = UxControlsCreateObject(ctypes.byref(clsid), ctypes.byref(iid),
                                ctypes.byref(obj))
    record("uxctl.UxControlsCreateObject",
           hr & 0xFFFFFFFF == CLASS_E_CLASSNOTAVAILABLE,
           "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    UxControlsUninitProcess()
    record("uxctl.UxControlsUninitProcess", True)


# ---------------------------------------------------------------------------
# WLXVideoTrim.dll
# ---------------------------------------------------------------------------
def test_wlxvideotrim(dll_dir):
    dll = ctypes.WinDLL(os.path.join(dll_dir, "WLXVideoTrim.dll"))

    factory = [
        ("CreateAVICopierDirect", (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoCopierFromMediaType",
         (ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("CreateVideoFormatContextTranscoder",
         (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoPlayer", (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoWMVTranscoder", (ctypes.POINTER(ctypes.c_void_p),)),
    ]
    for name, argtypes in factory:
        fn = bind_stdcall(dll, name, HRESULT, *argtypes)
        obj = ctypes.c_void_p()
        if len(argtypes) == 1:
            args = (ctypes.byref(obj),)
        else:
            clsid = GUID()
            args = (ctypes.byref(clsid), ctypes.byref(obj))
        hr = fn(*args)
        record("WLXVideoTrim.%s" % name,
               hr & 0xFFFFFFFF == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))


# ---------------------------------------------------------------------------
# WLXPipetran.dll
# ---------------------------------------------------------------------------
def test_wlxpipetran(dll_dir):
    dll = ctypes.WinDLL(os.path.join(dll_dir, "WLXPipetran.dll"))

    GetTFXCreateFunctions = bind_stdcall(
        dll, "GetTFXCreateFunctions", HRESULT,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32))

    functions = ctypes.c_void_p()
    count = ctypes.c_uint32()
    hr = GetTFXCreateFunctions(ctypes.byref(functions), ctypes.byref(count))
    record("WLXPipetran.GetTFXCreateFunctions",
           hr & 0xFFFFFFFF == E_NOTIMPL and count.value == 0,
           "HRESULT=0x%08X count=%u" % (hr & 0xFFFFFFFF, count.value))


# ---------------------------------------------------------------------------
# MovieMakerCore.dll  (MovieMakerMain is __cdecl)
# ---------------------------------------------------------------------------
def test_moviemakercore(dll_dir):
    dll = ctypes.CDLL(os.path.join(dll_dir, "MovieMakerCore.dll"))

    MovieMakerMain = bind_cdecl(
        dll, "MovieMakerMain", ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_wchar)))

    args = [u"MovieMaker.exe", u"--help"]
    argv = (ctypes.c_wchar_p * len(args))(*args)
    argvp = ctypes.cast(argv, ctypes.POINTER(ctypes.POINTER(ctypes.c_wchar)))
    rc = MovieMakerMain(len(args), argvp)
    record("MovieMakerCore.MovieMakerMain", rc == 0, "return=%d" % rc)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_all(dll_dir):
    del RESULTS[:]
    tests = [test_wlidcli, test_uxctl, test_wlxvideotrim, test_wlxpipetran,
             test_moviemakercore]
    for test in tests:
        try:
            test(dll_dir)
        except Exception as exc:  # noqa: BLE001
            record(test.__name__, False, repr(exc))

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print("SUMMARY PASS=%d FAIL=%d" % (passed, failed))
    return 0 if failed == 0 else 1


def main(argv):
    dll_dir = argv[0] if argv else DEFAULT_DLL_DIR
    if not os.path.isdir(dll_dir):
        print("error: DLL directory does not exist: %s" % dll_dir)
        return 2
    return run_all(dll_dir)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
