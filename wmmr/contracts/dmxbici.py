"""DmxBici.dll -- Bici telemetry wrapper (19 exports).

Every export is a C++-mangled name that aliases a plain stdcall symbol
(e.g. ``?StartExperience@BiciWrapper@@YGJXZ = _BiciWrapper_StartExperience@0``).
The alias names are NOT resolvable via GetProcAddress, so the mangled
export names are bound directly.  The ``YG`` in the mangling marks
__stdcall; ``J``/``_N``/``X`` return LONG/BOOL/void.

Behavior (from DmxBici.cpp): StartExperienceWithId echoes its id;
SetAnid returns S_OK; Set/Increment/SetIfMax/SetIfMin/SetString return
TRUE; timer trio returns TRUE; EndExperience returns S_OK;
TransferExperienceToWeb writes *out = NULL and returns TRUE.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import S_OK, bind_stdcall, load_dll

GROUP = "dmxbici"
DLL = "DmxBici.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "StartExperience": bind_stdcall(
            dll, "?StartExperience@BiciWrapper@@YGJXZ", ctypes.c_long),
        "StartExperienceWithId": bind_stdcall(
            dll, "?StartExperience@BiciWrapper@@YGJW4BiciStartupId@1@@Z",
            ctypes.c_long, ctypes.c_uint32),
        "SetAnid": bind_stdcall(
            dll, "?SetAnid@BiciWrapper@@YGJPB_W@Z",
            ctypes.c_long, wt.LPCWSTR),
        "Set": bind_stdcall(
            dll, "?Set@BiciWrapper@@YG_NKK@Z",
            wt.BOOL, ctypes.c_uint32, ctypes.c_uint32),
        "Increment": bind_stdcall(
            dll, "?Increment@BiciWrapper@@YG_NKK@Z",
            wt.BOOL, ctypes.c_uint32, ctypes.c_uint32),
        "SetIfMax": bind_stdcall(
            dll, "?SetIfMax@BiciWrapper@@YG_NKK@Z",
            wt.BOOL, ctypes.c_uint32, ctypes.c_uint32),
        "SetIfMin": bind_stdcall(
            dll, "?SetIfMin@BiciWrapper@@YG_NKK@Z",
            wt.BOOL, ctypes.c_uint32, ctypes.c_uint32),
        "SetString": bind_stdcall(
            dll, "?SetString@BiciWrapper@@YG_NKPB_W@Z",
            wt.BOOL, ctypes.c_uint32, wt.LPCWSTR),
        "TimerStart": bind_stdcall(
            dll, "?TimerStart@BiciWrapper@@YG_NK@Z", wt.BOOL, ctypes.c_uint32),
        "TimerRecord": bind_stdcall(
            dll, "?TimerRecord@BiciWrapper@@YG_NK@Z", wt.BOOL, ctypes.c_uint32),
        "TimerAccumulate": bind_stdcall(
            dll, "?TimerAccumulate@BiciWrapper@@YG_NK@Z",
            wt.BOOL, ctypes.c_uint32),
        "EndExperience": bind_stdcall(
            dll, "?EndExperience@BiciWrapper@@YGJXZ", ctypes.c_long),
        "TransferExperienceToWeb": bind_stdcall(
            dll, "?TransferExperienceToWeb@BiciWrapper@@YG_NPB_WPAPA_W@Z",
            wt.BOOL, wt.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)),
    }


def test_api(ctx):
    api = bind(ctx)

    # StartExperienceWithId echoes the id; StartExperience allocates one.
    sid = api["StartExperienceWithId"](0x1234)
    ctx.record(GROUP, "DmxBici.StartExperienceWithId",
               sid == 0x1234, "id=0x%X" % sid)

    start = api["StartExperience"]()
    ctx.record(GROUP, "DmxBici.StartExperience",
               start >= 1, "id=%d" % start)

    anid = api["SetAnid"](u"wmmr-ctypes-test")
    ctx.record(GROUP, "DmxBici.SetAnid", anid == S_OK,
               "HRESULT=0x%08X" % anid)

    ctx.record(GROUP, "DmxBici.Set",
               api["Set"](1, 42) != 0, "Set(1,42)=%d" % api["Set"](1, 42))
    ctx.record(GROUP, "DmxBici.Increment",
               api["Increment"](1, 1) != 0,
               "Increment(1,1)=%d" % api["Increment"](1, 1))
    ctx.record(GROUP, "DmxBici.SetIfMax",
               api["SetIfMax"](2, 99) != 0,
               "SetIfMax(2,99)=%d" % api["SetIfMax"](2, 99))
    ctx.record(GROUP, "DmxBici.SetIfMin",
               api["SetIfMin"](2, 1) != 0,
               "SetIfMin(2,1)=%d" % api["SetIfMin"](2, 1))
    ctx.record(GROUP, "DmxBici.SetString",
               api["SetString"](3, u"profile") != 0,
               "SetString(3,L'profile')=%d" % api["SetString"](3, u"profile"))

    for tname in ("TimerStart", "TimerRecord", "TimerAccumulate"):
        r = api[tname](7)
        ctx.record(GROUP, "DmxBici.%s" % tname,
                   r != 0, "%s(7)=%d" % (tname, r))

    end = api["EndExperience"]()
    ctx.record(GROUP, "DmxBici.EndExperience", end == S_OK,
               "HRESULT=0x%08X" % end)

    out = ctypes.c_void_p()
    r = api["TransferExperienceToWeb"](u"https://example.com/publish",
                                       ctypes.byref(out))
    ctx.record(GROUP, "DmxBici.TransferExperienceToWeb",
               r != 0 and out.value is None,
               "ret=%d out=%r" % (r, out.value))


TESTS = [test_api]
