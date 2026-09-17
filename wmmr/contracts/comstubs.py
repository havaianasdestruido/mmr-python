"""COM-stub quartet DLLs.

These seven DLLs export only the four COM boilerplate entry points
(DllCanUnloadNow / DllGetClassObject / DllRegisterServer /
DllUnregisterServer), three of which alias DllCanUnloadNow at the same RVA
in most of them.  MetadataSys additionally exports the real
WLXPSGetItemPropertyHandler stub (E_NOTIMPL).

DLLs covered: MetadataSys, MovieMakerPreviewClient, WLMFDS, WLXFaceRecognition,
WLXMovieLibrary, WLXPhotoCinematic, WLXSlideshow.
"""

import ctypes

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, E_NOTIMPL, HRESULT, GUID,
    bind_stdcall, load_dll)

GROUP = "comstubs"

COM_QUARTET = [
    ("MetadataSys", "MetadataSys.dll"),
    ("MovieMakerPreviewClient", "MovieMakerPreviewClient.dll"),
    ("WLMFDS", "WLMFDS.dll"),
    ("WLXFaceRecognition", "WLXFaceRecognition.dll"),
    ("WLXMovieLibrary", "WLXMovieLibrary.dll"),
    ("WLXPhotoCinematic", "WLXPhotoCinematic.dll"),
    ("WLXSlideshow", "WLXSlideshow.dll"),
]

# MovieMakerPreviewClient exports a real DllRegisterServer (registry writes),
# not an alias stub -- it returns S_OK or a registry error, and self-cleans
# through DllUnregisterServer on failure.  WLXPhotoCinematic also performs
# real HKLM registry writes, so its DllRegisterServer returns E_ACCESSDENIED
# in a non-elevated process (matching the reference binary's behavior).
REAL_REGISTRATION = {"MovieMakerPreviewClient", "WLXPhotoCinematic"}


def _bind_com(dll):
    return {
        "DllCanUnloadNow": bind_stdcall(dll, "DllCanUnloadNow", HRESULT),
        "DllGetClassObject": bind_stdcall(
            dll, "DllGetClassObject", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
        "DllRegisterServer": bind_stdcall(dll, "DllRegisterServer", HRESULT),
        "DllUnregisterServer": bind_stdcall(dll, "DllUnregisterServer", HRESULT),
    }


def test_wlmfds_load(ctx):
    """WLMFDS DllMain aborts DLL_PROCESS_ATTACH (binary diverges from source,
    whose dllmain always returns TRUE): LoadLibrary must fail with WinError 1114
    (ERROR_DLL_INIT_FAILED), deterministically, even in a fresh process."""
    try:
        load_dll(ctx.dll_dir, "WLMFDS.dll")
        ctx.record(GROUP, "WLMFDS.load", False,
                   "expected attach abort (WinError 1114), but load succeeded")
    except OSError as exc:
        ctx.record(GROUP, "WLMFDS.load",
                   getattr(exc, "winerror", None) == 1114,
                   "load aborted winerror=%s" % getattr(exc, "winerror", None))


def test_api(ctx):
    for label, fname in COM_QUARTET:
        if label == "WLMFDS":
            continue  # covered by test_wlmfds_load (DllMain aborts attach)
        dll = load_dll(ctx.dll_dir, fname)
        api = _bind_com(dll)

        hr = api["DllCanUnloadNow"]()
        ctx.record(GROUP, "%s.DllCanUnloadNow" % label, hr == S_OK,
                   "HRESULT=0x%08X" % hr)

        clsid = GUID()
        iid = GUID()
        obj = ctypes.c_void_p()
        hr = api["DllGetClassObject"](ctypes.byref(clsid), ctypes.byref(iid),
                                      ctypes.byref(obj))
        ctx.record(GROUP, "%s.DllGetClassObject" % label,
                   (hr & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE,
                   "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

        hr = api["DllRegisterServer"]()
        if label in REAL_REGISTRATION:
            ok = (hr == S_OK) or ((hr & 0x80000000) != 0)
            msg = "real registry impl: HRESULT=0x%08X (S_OK or reg error)" % hr
        else:
            ok = hr == S_OK
            msg = "HRESULT=0x%08X" % hr
        ctx.record(GROUP, "%s.DllRegisterServer" % label, ok, msg)

        hr = api["DllUnregisterServer"]()
        ctx.record(GROUP, "%s.DllUnregisterServer" % label, hr == S_OK,
                   "HRESULT=0x%08X" % hr)

    # MetadataSys's one real export: WLXPSGetItemPropertyHandler stub
    dll = load_dll(ctx.dll_dir, "MetadataSys.dll")
    WLXPSGetItemPropertyHandler = bind_stdcall(
        dll, "WLXPSGetItemPropertyHandler", HRESULT,
        ctypes.c_void_p, ctypes.c_uint32,
        ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))
    iid = GUID()
    obj = ctypes.c_void_p()
    hr = WLXPSGetItemPropertyHandler(None, 0, ctypes.byref(iid),
                                     ctypes.byref(obj))
    ctx.record(GROUP, "MetadataSys.WLXPSGetItemPropertyHandler",
               (hr & 0xFFFFFFFF) == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))


TESTS = [test_wlmfds_load, test_api]
