"""WLXPhotoSqm.dll -- SQM telemetry wrapper (44 exports, stub signature).

Like DmxBici, all 44 exports are C++-mangled names aliasing plain stdcall
symbols (_Sqm_*); only the mangled names resolve via GetProcAddress.  The
44 names collapse to just 7 RVAs: 17 alias _Sqm_AbortStreamTimer, 13 alias
_Sqm_DeferReportAverage, etc. -- near no-op stubs.  Everything void except
GetOptInState (0), IsEnabled (FALSE), IsStreamTimerActive/DataSet (FALSE).
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import bind_stdcall, load_dll

GROUP = "wlxphotosqm"
DLL = "WLXPhotoSqm.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "Startup": bind_stdcall(dll, "?Startup@Sqm@@YGXXZ", None),
        "StartupWithAppId": bind_stdcall(
            dll, "?Startup@Sqm@@YGXW4SqmDmxAppId@1@@Z", None,
            ctypes.c_uint32),
        "Shutdown": bind_stdcall(dll, "?Shutdown@Sqm@@YGXXZ", None),
        "GetOptInState": bind_stdcall(
            dll, "?GetOptInState@Sqm@@YG?AW4OptInState@1@XZ",
            ctypes.c_uint32),
        "IsEnabled": bind_stdcall(dll, "?IsEnabled@Sqm@@YG_NXZ", ctypes.c_bool),
        "IsStreamTimerActive": bind_stdcall(
            dll, "?IsStreamTimerActive@Sqm@@YG_NKK@Z", ctypes.c_bool,
            ctypes.c_uint32, ctypes.c_uint32),
        "Set": bind_stdcall(
            dll, "?Set@Sqm@@YGXKK@Z", None, ctypes.c_uint32, ctypes.c_uint32),
        "Increment": bind_stdcall(
            dll, "?Increment@Sqm@@YGXKK@Z", None,
            ctypes.c_uint32, ctypes.c_uint32),
        "AddToStream": bind_stdcall(
            dll, "?AddToStream@Sqm@@YGXKK@Z", None,
            ctypes.c_uint32, ctypes.c_uint32),
        "DeferReportAverage": bind_stdcall(
            dll, "?DeferReportAverage@Sqm@@YGXK@Z", None, ctypes.c_uint32),
    }


def test_api(ctx):
    api = bind(ctx)

    optin = api["GetOptInState"]()
    ctx.record(GROUP, "WLXPhotoSqm.GetOptInState", optin == 0,
               "OptInState=%u" % optin)
    ctx.record(GROUP, "WLXPhotoSqm.IsEnabled",
               api["IsEnabled"]() == 0, "IsEnabled=%d" % int(api["IsEnabled"]()))
    ctx.record(GROUP, "WLXPhotoSqm.IsStreamTimerActive",
               api["IsStreamTimerActive"](1, 2) == 0,
               "IsStreamTimerActive(1,2)=%d" % int(api["IsStreamTimerActive"](1, 2)))

    # void smoke sequence: startup -> counters -> timers -> shutdown, no crash
    api["Startup"]()
    api["StartupWithAppId"](0)
    api["Set"](1, 2)
    api["Increment"](1, 1)
    api["AddToStream"](1, 3)
    api["DeferReportAverage"](1)
    api["Shutdown"]()
    ctx.record(GROUP, "WLXPhotoSqm.Smoke", True)


TESTS = [test_api]
