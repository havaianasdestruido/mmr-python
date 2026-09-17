"""WLXMediaPublishSubscribe.dll -- publishing/subscription system (25 exports).

Exports the _PublishManager_* stdcall API (decorated names) plus a COM
quartet.  The manager is real: Create returns a HANDLE, EnumerateTargets
reports 5 built-in plugins (Facebook/Flickr/YouTube/Vimeo/SkyDrive),
GetTargetName/GetServiceStatus/GetDefaultTarget round-trip S_OK, and the
session/callback entry points are E_NOTIMPL stubs.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, E_NOTIMPL, E_INVALIDARG, HRESULT, GUID,
    bind_stdcall, load_dll)

GROUP = "wlxmps"
DLL = "WLXMediaPublishSubscribe.dll"

PublishTarget_Facebook = 0
PublishTarget_Flickr = 1
PublishTarget_YouTube = 2
PublishTarget_Vimeo = 3
PublishTarget_SkyDrive = 4

TARGET_NAMES = {
    PublishTarget_Facebook: u"Facebook",
    PublishTarget_Flickr: u"Flickr",
    PublishTarget_YouTube: u"YouTube",
    PublishTarget_Vimeo: u"Vimeo",
    PublishTarget_SkyDrive: u"SkyDrive",
}


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "Create": bind_stdcall(dll, "_PublishManager_Create@0", wt.HANDLE),
        "Destroy": bind_stdcall(dll, "_PublishManager_Destroy@4", None, wt.HANDLE),
        "EnumerateTargets": bind_stdcall(
            dll, "_PublishManager_EnumerateTargets@12", HRESULT,
            wt.HANDLE, ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_uint)),
        "GetTargetName": bind_stdcall(
            dll, "_PublishManager_GetTargetName@12", HRESULT,
            ctypes.c_int, ctypes.POINTER(ctypes.c_wchar), ctypes.c_uint),
        "GetServiceStatus": bind_stdcall(
            dll, "_PublishManager_GetServiceStatus@8", HRESULT,
            ctypes.c_int, ctypes.POINTER(wt.BOOL)),
        "GetDefaultTarget": bind_stdcall(
            dll, "_PublishManager_GetDefaultTarget@8", HRESULT,
            wt.HANDLE, ctypes.POINTER(ctypes.c_int)),
        "SetDefaultTarget": bind_stdcall(
            dll, "_PublishManager_SetDefaultTarget@8", HRESULT,
            wt.HANDLE, ctypes.c_int),
        "IsAuthenticated": bind_stdcall(
            dll, "_PublishManager_IsAuthenticated@12", HRESULT,
            wt.HANDLE, ctypes.c_int, ctypes.POINTER(wt.BOOL)),
        "GetStatus": bind_stdcall(
            dll, "_PublishManager_GetStatus@12", HRESULT,
            wt.HANDLE, ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint)),
        "Cleanup": bind_stdcall(dll, "_PublishManager_Cleanup@0", HRESULT),
        "DllCanUnloadNow": bind_stdcall(dll, "DllCanUnloadNow", HRESULT),
        "DllGetClassObject": bind_stdcall(
            dll, "DllGetClassObject", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
    }


def test_api(ctx):
    api = bind(ctx)

    mgr = api["Create"]()
    ctx.record(GROUP, "WLXMPS.PublishManager_Create",
               mgr is not None, "handle=%r" % mgr)

    for target in sorted(TARGET_NAMES):
        buf = (ctypes.c_wchar * 64)()
        hr = api["GetTargetName"](target, buf, len(buf))
        name = ctypes.cast(buf, ctypes.c_wchar_p).value
        ctx.record(GROUP, "WLXMPS.GetTargetName(%d)" % target,
                   hr == S_OK and name == TARGET_NAMES[target],
                   "target=%d name=%r HRESULT=0x%08X" % (target, name, hr))

    avail = wt.BOOL()
    hr = api["GetServiceStatus"](PublishTarget_YouTube, ctypes.byref(avail))
    ctx.record(GROUP, "WLXMPS.GetServiceStatus",
               hr == S_OK and avail.value != 0,
               "HRESULT=0x%08X available=%d" % (hr, int(avail.value)))

    default = ctypes.c_int()
    hr = api["GetDefaultTarget"](mgr, ctypes.byref(default))
    ctx.record(GROUP, "WLXMPS.GetDefaultTarget",
               hr == S_OK and default.value == PublishTarget_Facebook,
               "HRESULT=0x%08X target=%d" % (hr, default.value))

    hr = api["SetDefaultTarget"](mgr, PublishTarget_YouTube)
    ctx.record(GROUP, "WLXMPS.SetDefaultTarget", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    targets = (ctypes.c_int * 8)()
    count = ctypes.c_uint(len(targets))
    hr = api["EnumerateTargets"](mgr, targets, ctypes.byref(count))
    ctx.record(GROUP, "WLXMPS.EnumerateTargets",
               hr == S_OK and count.value == 5,
               "HRESULT=0x%08X count=%u" % (hr, count.value))

    auth = wt.BOOL()
    hr = api["IsAuthenticated"](mgr, PublishTarget_Facebook,
                                ctypes.byref(auth))
    ctx.record(GROUP, "WLXMPS.IsAuthenticated",
               hr == S_OK and auth.value == 0,
               "HRESULT=0x%08X auth=%d" % (hr, int(auth.value)))

    status = ctypes.c_uint()
    percent = ctypes.c_uint()
    hr = api["GetStatus"](None, ctypes.byref(status), ctypes.byref(percent))
    ctx.record(GROUP, "WLXMPS.GetStatus",
               (hr & 0xFFFFFFFF) == E_INVALIDARG,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    api["Destroy"](mgr)
    ctx.record(GROUP, "WLXMPS.PublishManager_Destroy", True)

    hr = api["Cleanup"]()
    ctx.record(GROUP, "WLXMPS.PublishManager_Cleanup", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    # COM quartet
    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    ctx.record(GROUP, "WLXMPS.DllCanUnloadNow",
               api["DllCanUnloadNow"]() == S_OK)
    ctx.record(GROUP, "WLXMPS.DllGetClassObject",
               (api["DllGetClassObject"](ctypes.byref(clsid),
                                         ctypes.byref(iid),
                                         ctypes.byref(obj)) & 0xFFFFFFFF)
               == CLASS_E_CLASSNOTAVAILABLE)


TESTS = [test_api]
