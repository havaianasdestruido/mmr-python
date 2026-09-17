"""WLXVideoTrim.dll -- DirectShow filter factories (5 exports, real).

The five Create* factories construct real engines.  Four return S_OK and
hand back a valid IUnknown; CreateVideoCopierFromMediaType returns
AVS_E_UNSUPPORTED_FILE_TYPE (0x80520005) for an unrecognized major type
(GUID_NULL).  The existing suite pins this behavior.
"""

import ctypes

from wmmr.bindings import (
    S_OK, E_NOTIMPL, HRESULT, GUID, bind_stdcall, load_dll)

# AVS_E_UNSUPPORTED_FILE_TYPE — facility 0x52, code 0x05
AVS_E_UNSUPPORTED_FILE_TYPE = 0x80520005

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
        # The zeroed GUID passed for CreateVideoCopierFromMediaType does not
        # match any MEDIATYPE_*, so the factory returns AVS_E_UNSUPPORTED_FILE_TYPE.
        expected = (AVS_E_UNSUPPORTED_FILE_TYPE if name == "CreateVideoCopierFromMediaType"
                    else S_OK)
        ctx.record(GROUP, "WLXVideoTrim.%s" % name,
                   (hr & 0xFFFFFFFF) == (expected & 0xFFFFFFFF),
                   "HRESULT=0x%08X want=0x%08X" % (hr & 0xFFFFFFFF, expected & 0xFFFFFFFF))


TESTS = [test_api]
