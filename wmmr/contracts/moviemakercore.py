"""MovieMakerCore.dll -- the 1.7 MB engine (4257 exports, 1 clean C).

The single clean C entry point is MovieMakerMain, which is __cdecl:

    int __cdecl MovieMakerMain(int argc, wchar_t** argv)

It parses the command line first and returns SUNDANCE_EXIT_SUCCESS (0) for
help switches without ever touching the UI, so it is safe to call.  We only
exercise the argument-parsing paths; the 4256 C++ mangled exports
(StoryboardManager, HMRAVSource, SundanceUI, ...) are presence-probed.
"""

import ctypes

from wmmr.bindings import bind_cdecl, load_dll, export_exists

GROUP = "moviemakercore"
DLL = "MovieMakerCore.dll"

SUNDANCE_EXIT_SUCCESS = 0


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL, cdecl=True)
    return {
        "MovieMakerMain": bind_cdecl(
            dll, "MovieMakerMain", ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_wchar))),
    }


def _run_main(api, args):
    argv = (ctypes.c_wchar_p * len(args))(*args)
    argvp = ctypes.cast(argv, ctypes.POINTER(ctypes.POINTER(ctypes.c_wchar)))
    return api["MovieMakerMain"](len(args), argvp)


def test_api(ctx):
    api = bind(ctx)

    # --help / /? / -h all short-circuit to SUNDANCE_EXIT_SUCCESS before
    # any single-instance mutex or app initialization happens.
    for switch in (u"--help", u"/?", u"-h"):
        rc = _run_main(api, [u"MovieMaker.exe", switch])
        ctx.record(GROUP, "MovieMakerCore.MovieMakerMain(%s)" % switch,
                   rc == SUNDANCE_EXIT_SUCCESS,
                   "return=%d" % rc)


def test_presence(ctx):
    dll = load_dll(ctx.dll_dir, DLL, cdecl=True)
    # Spot-check the clean entry plus a C++ mangled StoryboardManager export.
    expected = [
        "MovieMakerMain",
        "??0MovieProject@StoryboardManager@@QAE@XZ",
    ]
    present = [n for n in expected if export_exists(dll, n)]
    ctx.record(GROUP, "MovieMakerCore.Presence",
               present == expected,
               "exports present=%r" % present)


TESTS = [test_api, test_presence]
