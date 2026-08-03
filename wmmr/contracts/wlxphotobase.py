"""WLXPhotoBase.dll -- photo helper framework (91 exports, 1 clean C).

The single clean export is _WLXPhotoBase_Init@0 (void __stdcall), the
one-time initialization hook called by MovieMaker.exe.  The other 90
exports are C++ mangled Base:: classes (File, FindFile, Thread, IntSet,
TempFile, ...) which are thiscall and only presence-probed.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import bind_stdcall, load_dll, export_exists

GROUP = "wlxphotobase"
DLL = "WLXPhotoBase.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "Init": bind_stdcall(dll, "_WLXPhotoBase_Init@0", None),
    }


def test_api(ctx):
    api = bind(ctx)
    api["Init"]()
    ctx.record(GROUP, "WLXPhotoBase.Init", True)


def test_presence(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    expected = [
        "_WLXPhotoBase_Init@0",
        "??0File@Base@@QAE@XZ",
    ]
    present = [n for n in expected if export_exists(dll, n)]
    ctx.record(GROUP, "WLXPhotoBase.Presence",
               present == expected,
               "exports present=%r" % present)


TESTS = [test_api, test_presence]
