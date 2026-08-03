"""WLXMP4Parser.dll -- MP4/ISOBMFF parser (8 exports, 4 clean C + COM).

The exported filter/factory functions are stubs:

* _AddMP4SourceFilter@12   -> E_NOTIMPL
* _BuildMP4FilterGraph@8   -> E_NOTIMPL  (BuildMP4PlayBack aliases it)
* _IsMP4FilePlayable@4     -> FALSE
* COM quartet: DllCanUnloadNow S_OK, DllGetClassObject
  CLASS_E_CLASSNOTAVAILABLE, Register/Unregister S_OK.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, E_NOTIMPL, HRESULT, GUID,
    bind_stdcall, load_dll)

GROUP = "wlxmp4parser"
DLL = "WLXMP4Parser.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "AddMP4SourceFilter": bind_stdcall(
            dll, "_AddMP4SourceFilter@12", HRESULT,
            wt.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)),
        "BuildMP4FilterGraph": bind_stdcall(
            dll, "_BuildMP4FilterGraph@8", HRESULT,
            wt.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)),
        "BuildMP4PlayBack": bind_stdcall(
            dll, "_BuildMP4PlayBack@8", HRESULT,
            wt.LPCWSTR, ctypes.c_void_p),
        "IsMP4FilePlayable": bind_stdcall(
            dll, "_IsMP4FilePlayable@4", wt.BOOL, wt.LPCWSTR),
        "DllCanUnloadNow": bind_stdcall(dll, "DllCanUnloadNow", HRESULT),
        "DllGetClassObject": bind_stdcall(
            dll, "DllGetClassObject", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
        "DllRegisterServer": bind_stdcall(dll, "DllRegisterServer", HRESULT),
        "DllUnregisterServer": bind_stdcall(dll, "DllUnregisterServer", HRESULT),
    }


def test_api(ctx):
    api = bind(ctx)

    pgraph = ctypes.c_void_p()
    hr = api["BuildMP4FilterGraph"](u"C:\\nonexistent\\movie.mp4",
                                    ctypes.byref(pgraph))
    ctx.record(GROUP, "WLXMP4Parser.BuildMP4FilterGraph",
               (hr & 0xFFFFFFFF) == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    hr = api["BuildMP4PlayBack"](u"C:\\nonexistent\\movie.mp4", None)
    ctx.record(GROUP, "WLXMP4Parser.BuildMP4PlayBack",
               (hr & 0xFFFFFFFF) == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    pfilter = ctypes.c_void_p()
    hr = api["AddMP4SourceFilter"](u"C:\\nonexistent\\movie.mp4", None,
                                   ctypes.byref(pfilter))
    ctx.record(GROUP, "WLXMP4Parser.AddMP4SourceFilter",
               (hr & 0xFFFFFFFF) == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    ok = api["IsMP4FilePlayable"](u"C:\\nonexistent\\movie.mp4")
    ctx.record(GROUP, "WLXMP4Parser.IsMP4FilePlayable",
               ok == 0, "IsMP4FilePlayable(nonexistent)=%d" % int(ok))

    # COM quartet
    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    ctx.record(GROUP, "WLXMP4Parser.DllCanUnloadNow",
               api["DllCanUnloadNow"]() == S_OK)
    ctx.record(GROUP, "WLXMP4Parser.DllGetClassObject",
               (api["DllGetClassObject"](ctypes.byref(clsid),
                                         ctypes.byref(iid),
                                         ctypes.byref(obj)) & 0xFFFFFFFF)
               == CLASS_E_CLASSNOTAVAILABLE)
    ctx.record(GROUP, "WLXMP4Parser.DllRegisterServer",
               api["DllRegisterServer"]() == S_OK)
    ctx.record(GROUP, "WLXMP4Parser.DllUnregisterServer",
               api["DllUnregisterServer"]() == S_OK)


TESTS = [test_api]
