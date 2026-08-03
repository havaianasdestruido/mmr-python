"""GPURenderer.dll -- DirectUI GPURenderer (12 exports, 0 clean C).

All 12 exports are C++ mangled DirectUI::GPURenderer methods (__thiscall:
Initialize, BeginDraw/EndDraw/Present, DrawVideoFrame, GetD2DContext,
GetDevice, Resize, Cleanup, ctor/dtor).  They are not callable from raw
ctypes without a vtable/this; this DLL is present-only, proven by loading
it and resolving a mangled export.
"""

from wmmr.bindings import load_dll, export_exists

GROUP = "gpurenderer"
DLL = "GPURenderer.dll"


def test_presence(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    expected = [
        "??0GPURenderer@DirectUI@@QAE@XZ",
        "??1GPURenderer@DirectUI@@QAE@XZ",
    ]
    present = [n for n in expected if export_exists(dll, n)]
    ctx.record(GROUP, "GPURenderer.Presence",
               present == expected,
               "exports present=%r" % present)


TESTS = [test_presence]
