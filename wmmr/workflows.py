"""Cross-DLL workflows -- deep scenarios that tie several DLLs together.

Each workflow is a ``test(ctx)`` function registered in ``WORKFLOWS`` under
the group name ``workflows``.  They reuse the per-DLL ``bind()`` helpers so
binding definitions live in exactly one place.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import S_OK, CLASS_E_CLASSNOTAVAILABLE, E_NOTIMPL, GUID
from wmmr.contracts import (
    dmxbici,
    moviemakercore,
    uxctl,
    uxcore,
    wlidcli,
    wlxpipeline,
    wlxpipetran,
    wlxmps,
    wlxmp4parser,
    wlxvideotrim,
)

GROUP = "workflows"


def wf_identity_and_telemetry(ctx):
    """Sign in with wlidcli, mint a ticket, then run a DmxBici experience."""
    wl = wlidcli.bind(ctx)
    dm = dmxbici.bind(ctx)

    h = wl["WLCreateIdentityHandle"]()
    token = ctypes.c_void_p()
    hr = wl["WLClogin"](None, u"user@example.com", h, ctypes.byref(token))
    if hr != S_OK:
        ctx.record(GROUP, "workflow.identity.then_telemetry", False,
                   "WLClogin failed 0x%08X" % hr)
        return
    ticket_buf = ctypes.c_void_p()
    hr = wl["WLGetTicket"](h, ctypes.byref(ticket_buf))
    ticket = ctypes.cast(ticket_buf, ctypes.c_wchar_p).value
    wl["WLFreeMemory"](ticket_buf)
    if hr != S_OK or not ticket:
        ctx.record(GROUP, "workflow.identity.then_telemetry", False,
                   "WLGetTicket failed 0x%08X" % hr)
        return

    sid = dm["StartExperienceWithId"](0x51)
    anid = dm["SetAnid"](u"user@example.com")
    inc = dm["Increment"](1, 1)
    dm["Set"](1, 42)
    dm["TimerStart"](3)
    dm["TimerRecord"](3)
    end = dm["EndExperience"]()
    ctx.record(
        GROUP, "workflow.identity.then_telemetry",
        sid == 0x51 and anid == S_OK and inc != 0 and end == S_OK,
        "ticket=%r sid=0x%X anid=0x%08X inc=%d end=0x%08X"
        % (ticket, sid, anid, inc, end))


def wf_directui_process_lifecycle(ctx):
    """uXCTL controls component + UXCore engine: init -> class objects -> teardown."""
    ux = uxctl.bind(ctx)
    core = uxcore.bind(ctx)

    hr_init = ux["InitProcess"]()
    hr_core = core["InitProcess"]()
    hr_thread = core["InitThread"]()

    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    hr_uxobj = ux["CreateObject"](ctypes.byref(clsid), ctypes.byref(iid),
                                  ctypes.byref(obj))
    obj2 = ctypes.c_void_p()
    hr_coreobj = core["UxGetClassObject"](ctypes.byref(clsid),
                                          ctypes.byref(iid),
                                          ctypes.byref(obj2))

    core["UnInitThread"]()
    core["UnInitProcess"]()
    ux["UninitProcess"]()
    ctx.record(
        GROUP, "workflow.directui.process_lifecycle",
        hr_init == S_OK and hr_core >= 0 and hr_thread == S_OK
        and (hr_uxobj & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE
        and (hr_coreobj & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE,
        "ux=0x%08X core=0x%08X thread=0x%08X uxobj=0x%08X coreobj=0x%08X"
        % (hr_init, hr_core, hr_thread,
           hr_uxobj & 0xFFFFFFFF, hr_coreobj & 0xFFFFFFFF))


def wf_moviemaker_cli_matrix(ctx):
    """MovieMakerMain argument matrix: all help forms short-circuit to 0."""
    api = moviemakercore.bind(ctx)

    def run(args):
        argv = (ctypes.c_wchar_p * len(args))(*args)
        argvp = ctypes.cast(argv, ctypes.POINTER(ctypes.POINTER(ctypes.c_wchar)))
        return api["MovieMakerMain"](len(args), argvp)

    results = []
    for switch in (u"--help", u"/?", u"-h"):
        results.append(run([u"MovieMaker.exe", switch]))
    ctx.record(GROUP, "workflow.moviemaker.cli_matrix",
               all(rc == 0 for rc in results),
               "help returns %r (want all 0)" % results)


def wf_video_factory_chain(ctx):
    """WLXVideoTrim factories real (S_OK / AVS_E_UNSUPPORTED for unknown
    media type); WLXPipetran + WLXPipeline factory tables real/counted."""
    vt = wlxvideotrim.bind(ctx)
    pt = wlxpipetran.bind(ctx)
    pl = wlxpipeline.bind(ctx)

    checks = []
    for name in ("CreateAVICopierDirect", "CreateVideoPlayer",
                 "CreateVideoWMVTranscoder", "CreateVideoFormatContextTranscoder"):
        obj = ctypes.c_void_p()
        checks.append((vt[name](ctypes.byref(obj)) & 0xFFFFFFFF) == S_OK)
    clsid = GUID()
    obj = ctypes.c_void_p()
    checks.append(
        (vt["CreateVideoCopierFromMediaType"](ctypes.byref(clsid),
                                              ctypes.byref(obj)) & 0xFFFFFFFF)
        == wlxvideotrim.AVS_E_UNSUPPORTED_FILE_TYPE)

    funcs = ctypes.c_void_p()
    count = ctypes.c_uint32()
    checks.append(
        (pt["GetTFXCreateFunctions"](ctypes.byref(funcs),
                                     ctypes.byref(count)) & 0xFFFFFFFF)
        == E_NOTIMPL)

    funcs = ctypes.c_void_p()
    count = ctypes.c_uint32()
    hr_pl = (pl["GetPipelineCreateFunctions"](ctypes.byref(funcs),
                                              ctypes.byref(count)) & 0xFFFFFFFF)
    checks.append(hr_pl == S_OK and count.value == 6)

    ctx.record(GROUP, "workflow.video.factory_chain",
               all(checks),
               "vt=4xS_OK copier=0x%08X pipetran=E_NOTIMPL pipeline=S_OK+%u"
               % (wlxvideotrim.AVS_E_UNSUPPORTED_FILE_TYPE, count.value))


def wf_publish_target_lifecycle(ctx):
    """PublishManager: create -> enumerate 5 targets -> round-trip -> destroy."""
    mps = wlxmps.bind(ctx)

    mgr = mps["Create"]()
    targets = (ctypes.c_int * 8)()
    count = ctypes.c_uint(len(targets))
    hr = mps["EnumerateTargets"](mgr, targets, ctypes.byref(count))

    names = []
    for i in range(min(count.value, len(targets))):
        buf = (ctypes.c_wchar * 64)()
        hr_name = mps["GetTargetName"](targets[i], buf, len(buf))
        names.append((targets[i], ctypes.cast(buf, ctypes.c_wchar_p).value,
                      hr_name))

    default = ctypes.c_int()
    hr_def = mps["GetDefaultTarget"](mgr, ctypes.byref(default))
    avail = wt.BOOL()
    hr_avail = mps["GetServiceStatus"](wlxmps.PublishTarget_YouTube,
                                       ctypes.byref(avail))
    mps["Destroy"](mgr)
    hr_cleanup = mps["Cleanup"]()

    ctx.record(
        GROUP, "workflow.publish.target_lifecycle",
        hr == S_OK and count.value == 5
        and all(h == S_OK and n in ("Facebook", "Flickr", "YouTube",
                                    "Vimeo", "SkyDrive")
                for _, n, h in names)
        and hr_def == S_OK and default.value == wlxmps.PublishTarget_Facebook
        and hr_avail == S_OK and avail.value != 0
        and hr_cleanup == S_OK,
        "count=%u names=%r default=%d avail=%d cleanup=0x%08X"
        % (count.value, [n for _, n, _ in names], default.value,
           int(avail.value), hr_cleanup))


def wf_mp4_filter_surface(ctx):
    """MP4 filter-graph surface: real impl fails on nonexistent input,
    add-source validates the NULL graph, playability FALSE."""
    mp4 = wlxmp4parser.bind(ctx)

    pgraph = ctypes.c_void_p()
    hr_graph = mp4["BuildMP4FilterGraph"](u"C:\\nope\\movie.mp4",
                                          ctypes.byref(pgraph))
    pfilter = ctypes.c_void_p()
    hr_add = mp4["AddMP4SourceFilter"](u"C:\\nope\\movie.mp4", None,
                                       ctypes.byref(pfilter))
    playable = mp4["IsMP4FilePlayable"](u"C:\\nope\\movie.mp4")

    ctx.record(
        GROUP, "workflow.mp4.filter_surface",
        (hr_graph & 0x80000000) != 0
        and (hr_add & 0xFFFFFFFF) == 0x80070057     # E_INVALIDARG (null graph)
        and playable == 0,
        "graph=0x%08X add=0x%08X playable=%d"
        % (hr_graph & 0xFFFFFFFF, hr_add & 0xFFFFFFFF, int(playable)))


WORKFLOWS = [
    wf_identity_and_telemetry,
    wf_directui_process_lifecycle,
    wf_moviemaker_cli_matrix,
    wf_video_factory_chain,
    wf_publish_target_lifecycle,
    wf_mp4_filter_surface,
]
