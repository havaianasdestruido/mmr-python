"""WLXVideoTrim.dll -- DirectShow filter factories (5 exports, all stubs).

All five Create* factories share the stub E_NOTIMPL pattern (4 of 5 export
entries alias the same RVA); the existing suite already pins this behavior.
"""

import ctypes

from wmmr.bindings import (
    E_NOTIMPL, HRESULT, GUID, bind_stdcall, load_dll)

GROUP = "wlxvideotrim"
DLL = "WLXVideoTrim.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "CreateAVICopierDirect": bind_stdcall(
            dll, "CreateAVICopierDirect", HRESULT,
            ctypes.POINTER(ctypes.c_void_p)),
        "CreateVideoCopierFromMediaType": bind_stdcall(
            dll, "CreateVideoCopierFromMediaType", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)),
        "CreateVideoFormatContextTranscoder": bind_stdcall(
            dll, "CreateVideoFormatContextTranscoder", HRESULT,
            ctypes.POINTER(ctypes.c_void_p)),
        "CreateVideoPlayer": bind_stdcall(
            dll, "CreateVideoPlayer", HRESULT,
            ctypes.POINTER(ctypes.c_void_p)),
        "CreateVideoWMVTranscoder": bind_stdcall(
            dll, "CreateVideoWMVTranscoder", HRESULT,
            ctypes.POINTER(ctypes.c_void_p)),
    }


def test_api(ctx):
    api = bind(ctx)
    factories = [
        ("CreateAVICopierDirect", (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoCopierFromMediaType",
         (ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))),
        ("CreateVideoFormatContextTranscoder",
         (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoPlayer", (ctypes.POINTER(ctypes.c_void_p),)),
        ("CreateVideoWMVTranscoder", (ctypes.POINTER(ctypes.c_void_p),)),
    ]
    for name, argtypes in factories:
        fn = api[name]
        obj = ctypes.c_void_p()
        if len(argtypes) == 1:
            args = (ctypes.byref(obj),)
        else:
            clsid = GUID()
            args = (ctypes.byref(clsid), ctypes.byref(obj))
        hr = fn(*args)
        ctx.record(GROUP, "WLXVideoTrim.%s" % name,
                   (hr & 0xFFFFFFFF) == E_NOTIMPL,
                   "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))


TESTS = [test_api]
