"""WLXPipetran.dll -- the minimal single-export DLL.

Exports exactly one clean function: GetTFXCreateFunctions (stdcall, 2 args),
a stub returning E_NOTIMPL with a zeroed function table count.
"""

import ctypes

from wmmr.bindings import E_NOTIMPL, HRESULT, bind_stdcall, load_dll

GROUP = "wlxpipetran"
DLL = "WLXPipetran.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "GetTFXCreateFunctions": bind_stdcall(
            dll, "GetTFXCreateFunctions", HRESULT,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32)),
    }


def test_api(ctx):
    api = bind(ctx)
    functions = ctypes.c_void_p()
    count = ctypes.c_uint32()
    hr = api["GetTFXCreateFunctions"](ctypes.byref(functions),
                                      ctypes.byref(count))
    ctx.record(GROUP, "WLXPipetran.GetTFXCreateFunctions",
               (hr & 0xFFFFFFFF) == E_NOTIMPL and count.value == 0,
               "HRESULT=0x%08X count=%u" % (hr & 0xFFFFFFFF, count.value))


TESTS = [test_api]
