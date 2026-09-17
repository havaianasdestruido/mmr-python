"""WLXPipeline.dll -- video processing pipeline (2 exports).

Exports DllRegisterServer (S_OK) and _GetPipelineCreateFunctions@8, a real
function that populates a PipelineCreateFunctions struct with 6 pointers
(uVersion, uStructSize, pfnCreate, pfnDestroy, pfnProcess, pfnGetInfo)
and returns S_OK.  The 2 exports use DIFFERENT decorations (the .def
lists DllRegisterServer undecorated; the pipeline factory is dllexport'ed
stdcall so its export name carries the @8 suffix).
"""

import ctypes

from wmmr.bindings import S_OK, HRESULT, bind_stdcall, load_dll

GROUP = "wlxpipeline"
DLL = "WLXPipeline.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "DllRegisterServer": bind_stdcall(dll, "DllRegisterServer", HRESULT),
        "GetPipelineCreateFunctions": bind_stdcall(
            dll, "_GetPipelineCreateFunctions@8", HRESULT,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32)),
    }


def test_api(ctx):
    api = bind(ctx)

    hr = api["DllRegisterServer"]()
    ctx.record(GROUP, "WLXPipeline.DllRegisterServer", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    functions = ctypes.c_void_p()
    count = ctypes.c_uint32()
    hr = api["GetPipelineCreateFunctions"](ctypes.byref(functions),
                                           ctypes.byref(count))
    ctx.record(GROUP, "WLXPipeline.GetPipelineCreateFunctions",
               hr == S_OK and count.value == 6,
               "HRESULT=0x%08X count=%u" % (hr & 0xFFFFFFFF, count.value))


TESTS = [test_api]
