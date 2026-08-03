"""uxctl.dll -- DirectUI controls component (3 stdcall exports).

UxControlsInitProcess / UxControlsUninitProcess bracket the process;
UxControlsCreateObject is a stub returning CLASS_E_CLASSNOTAVAILABLE.
"""

import ctypes

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, HRESULT, GUID, bind_stdcall, load_dll)

GROUP = "uxctl"
DLL = "uxctl.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "InitProcess": bind_stdcall(dll, "UxControlsInitProcess", HRESULT),
        "CreateObject": bind_stdcall(
            dll, "UxControlsCreateObject", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
        "UninitProcess": bind_stdcall(dll, "UxControlsUninitProcess", None),
    }


def test_api(ctx):
    api = bind(ctx)

    hr = api["InitProcess"]()
    ctx.record(GROUP, "uxctl.UxControlsInitProcess", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    hr = api["CreateObject"](ctypes.byref(clsid), ctypes.byref(iid),
                             ctypes.byref(obj))
    ctx.record(GROUP, "uxctl.UxControlsCreateObject",
               (hr & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    api["UninitProcess"]()
    ctx.record(GROUP, "uxctl.UxControlsUninitProcess", True)


TESTS = [test_api]
