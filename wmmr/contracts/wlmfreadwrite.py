"""WLMFReadWrite.dll -- Media Foundation reader/writer convenience API.

Real _MF* stdcall C API (decorated names).  All checks are guarded calls
that exercise the argument validation paths (NULL handles, nonexistent
files) so no real media I/O is required:

* MFReader_Open(nonexistent)  -> NULL
* MFReader_GetProperties(NULL)-> E_INVALIDARG
* MFReader_Close(NULL)        -> void (no crash)
* MFWriter_Create(NULL, ...)  -> NULL
* MFWriter_WriteFrame(NULL)   -> E_INVALIDARG
* MFWriter_Finalize(NULL)     -> E_INVALIDARG

DllCanUnloadNow returns S_OK (no outstanding COM objects; the source-level
S_FALSE stub value was removed to match the reference binary).
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, E_INVALIDARG, HRESULT, GUID,
    bind_stdcall, load_dll)

GROUP = "wlmfreadwrite"
DLL = "WLMFReadWrite.dll"


class WLMediaProperties(ctypes.Structure):
    _fields_ = [
        ("wszFileType", ctypes.c_wchar * 32),
        ("uVideoWidth", ctypes.c_uint32),
        ("uVideoHeight", ctypes.c_uint32),
        ("uFrameRateNumerator", ctypes.c_uint32),
        ("uFrameRateDenominator", ctypes.c_uint32),
        ("uVideoBitrate", ctypes.c_uint32),
        ("uAudioBitrate", ctypes.c_uint32),
        ("uAudioSampleRate", ctypes.c_uint32),
        ("uAudioChannels", ctypes.c_uint32),
        ("llDuration", ctypes.c_longlong),
        ("guidVideoSubtype", GUID),
        ("guidAudioSubtype", GUID),
        ("bHasVideo", wt.BOOL),
        ("bHasAudio", wt.BOOL),
    ]


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "DllCanUnloadNow": bind_stdcall(dll, "DllCanUnloadNow", HRESULT),
        "DllGetClassObject": bind_stdcall(
            dll, "DllGetClassObject", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
        "MFReader_Open": bind_stdcall(
            dll, "_MFReader_Open@4", wt.HANDLE, wt.LPCWSTR),
        "MFReader_Close": bind_stdcall(
            dll, "_MFReader_Close@4", None, wt.HANDLE),
        "MFReader_GetProperties": bind_stdcall(
            dll, "_MFReader_GetProperties@8", HRESULT,
            wt.HANDLE, ctypes.POINTER(WLMediaProperties)),
        "MFReader_ReadFrame": bind_stdcall(
            dll, "_MFReader_ReadFrame@24", HRESULT,
            wt.HANDLE, ctypes.c_longlong,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32)),
        "MFWriter_Create": bind_stdcall(
            dll, "_MFWriter_Create@8", wt.HANDLE,
            wt.LPCWSTR, ctypes.POINTER(WLMediaProperties)),
        "MFWriter_WriteFrame": bind_stdcall(
            dll, "_MFWriter_WriteFrame@20", HRESULT,
            wt.HANDLE, ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_uint32, ctypes.c_longlong),
        "MFWriter_Finalize": bind_stdcall(
            dll, "_MFWriter_Finalize@4", HRESULT, wt.HANDLE),
    }


def test_api(ctx):
    api = bind(ctx)

    missing = u"C:\\WMMR\\nonexistent\\movie.wmv"

    h = api["MFReader_Open"](missing)
    ctx.record(GROUP, "WLMFReadWrite.MFReader_Open",
               h is None, "MFReader_Open(nonexistent)=%r" % h)

    props = WLMediaProperties()
    hr = api["MFReader_GetProperties"](None, ctypes.byref(props))
    ctx.record(GROUP, "WLMFReadWrite.MFReader_GetProperties",
               (hr & 0xFFFFFFFF) == E_INVALIDARG,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    nread = ctypes.c_uint32()
    hr = api["MFReader_ReadFrame"](None, 0, None, 0, ctypes.byref(nread))
    ctx.record(GROUP, "WLMFReadWrite.MFReader_ReadFrame",
               (hr & 0xFFFFFFFF) == E_INVALIDARG,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    api["MFReader_Close"](None)
    ctx.record(GROUP, "WLMFReadWrite.MFReader_Close", True)

    hw = api["MFWriter_Create"](None, ctypes.byref(props))
    ctx.record(GROUP, "WLMFReadWrite.MFWriter_Create",
               hw is None, "MFWriter_Create(NULL,...)=%r" % hw)

    hr = api["MFWriter_WriteFrame"](None, None, 0, 0)
    ctx.record(GROUP, "WLMFReadWrite.MFWriter_WriteFrame",
               (hr & 0xFFFFFFFF) == E_INVALIDARG,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    hr = api["MFWriter_Finalize"](None)
    ctx.record(GROUP, "WLMFReadWrite.MFWriter_Finalize",
               (hr & 0xFFFFFFFF) == E_INVALIDARG,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    hr = api["DllCanUnloadNow"]()
    ctx.record(GROUP, "WLMFReadWrite.DllCanUnloadNow",
               (hr & 0xFFFFFFFF) == S_OK,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))
    hr = api["DllGetClassObject"](ctypes.byref(clsid), ctypes.byref(iid),
                                  ctypes.byref(obj))
    ctx.record(GROUP, "WLMFReadWrite.DllGetClassObject",
               (hr & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))


TESTS = [test_api]
