"""uxcore.py -- DirectUI engine DLL (25 clean C exports + 522 mangled).

The 25 clean C exports are a MIX of calling conventions:

* 6 __stdcall from UXCore.cpp: ``_UXCoreInitProcess@0``, ``_UXCoreInitThread@0``,
  ``_UXCoreUnInitProcess@0``, ``_UXCoreUnInitThread@0``, ``_UxGetClassObject@12``,
  ``_DuiCreateObject@8``.
* 19 __cdecl from Resources.cpp (undecorated): ``DuiGetLayerManager``,
  ``ElementFromGadget``, ``GetGadgetRect``, ``GetGadgetSize``,
  ``GetKeyFocusedElement``, ``GetMessageEx``, ``GetTopHWNDParent``,
  ``LayerManagerInitThread``, ``LayerManagerUnInitThread``, ``PeekMessageEx``,
  ``RMFindModule``, ``RMFindModuleForResource``, ``RMLoadImage``, ``RMLoadMenu``,
  ``RMLoadString``, ``RMLoadStringBSTR``, ``RMUpdateResourceSet``, ``StrToID``,
  ``Internal_GetKeyFocusedElement_HWNDElement``.

The 522 C++ mangled ``DirectUI::`` classes (Element, Value, CDUIDialog, ...) are
thiscall and are only presence-probed, not called.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import (
    S_OK, CLASS_E_CLASSNOTAVAILABLE, E_NOTIMPL, HRESULT, GUID,
    bind_stdcall, bind_cdecl, load_dll, export_exists)

GROUP = "uxcore"
DLL = "UXCore.dll"


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "InitProcess": bind_stdcall(dll, "_UXCoreInitProcess@0", HRESULT),
        "InitThread": bind_stdcall(dll, "_UXCoreInitThread@0", HRESULT),
        "UnInitProcess": bind_stdcall(dll, "_UXCoreUnInitProcess@0", None),
        "UnInitThread": bind_stdcall(dll, "_UXCoreUnInitThread@0", None),
        "UxGetClassObject": bind_stdcall(
            dll, "_UxGetClassObject@12", HRESULT,
            ctypes.POINTER(GUID), ctypes.POINTER(GUID),
            ctypes.POINTER(ctypes.c_void_p)),
        "DuiCreateObject": bind_stdcall(
            dll, "_DuiCreateObject@8", HRESULT,
            wt.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)),
        "LayerManagerInitThread": bind_cdecl(
            dll, "LayerManagerInitThread", HRESULT),
        "StrToID": bind_cdecl(dll, "StrToID", ctypes.c_int, wt.LPCWSTR),
        "RMFindModule": bind_cdecl(
            dll, "RMFindModule", wt.HMODULE, wt.HMODULE, wt.LPCWSTR),
        "GetGadgetSize": bind_cdecl(
            dll, "GetGadgetSize", wt.BOOL,
            ctypes.c_void_p, ctypes.POINTER(SIZE)),
    }


def test_api(ctx):
    api = bind(ctx)

    # Process lifecycle: creates D2D/DWrite/WIC factories
    hr = api["InitProcess"]()
    ctx.record(GROUP, "UXCore.UXCoreInitProcess", hr >= 0,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))
    hr = api["InitThread"]()
    ctx.record(GROUP, "UXCore.UXCoreInitThread", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    # Class factory stub -> CLASS_E_CLASSNOTAVAILABLE, ppv == NULL
    clsid = GUID()
    iid = GUID()
    obj = ctypes.c_void_p()
    hr = api["UxGetClassObject"](ctypes.byref(clsid), ctypes.byref(iid),
                                 ctypes.byref(obj))
    ctx.record(GROUP, "UXCore.UxGetClassObject",
               (hr & 0xFFFFFFFF) == CLASS_E_CLASSNOTAVAILABLE and obj.value is None,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    # DuiCreateObject(LPCWSTR, void**) -> E_NOTIMPL
    element = ctypes.c_void_p()
    hr = api["DuiCreateObject"](u"Button", ctypes.byref(element))
    ctx.record(GROUP, "UXCore.DuiCreateObject",
               (hr & 0xFFFFFFFF) == E_NOTIMPL,
               "HRESULT=0x%08X" % (hr & 0xFFFFFFFF))

    # cdecl resource helpers
    hr = api["LayerManagerInitThread"]()
    ctx.record(GROUP, "UXCore.LayerManagerInitThread", hr == S_OK,
               "HRESULT=0x%08X" % hr)
    ctx.record(GROUP, "UXCore.StrToID", api["StrToID"](u"1234") == 1234,
               "StrToID(u'1234')=%d" % api["StrToID"](u"1234"))
    ctx.record(GROUP, "UXCore.RMFindModule",
               api["RMFindModule"](None, None) is None,
               "RMFindModule(NULL,NULL)=%r" % api["RMFindModule"](None, None))

    sz = SIZE()
    ok = api["GetGadgetSize"](None, ctypes.byref(sz)) == 0
    ctx.record(GROUP, "UXCore.GetGadgetSize",
               ok and sz.cx == 0 and sz.cy == 0,
               "GetGadgetSize(NULL)=%d (%dx%d)" % (int(ok), sz.cx, sz.cy))

    api["UnInitThread"]()
    api["UnInitProcess"]()
    ctx.record(GROUP, "UXCore.UXCoreUnInitProcess", True)


def test_presence(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    expected = [
        "_UXCoreInitProcess@0",
        "_UXCoreUnInitProcess@0",
        "_UxGetClassObject@12",
        "_DuiCreateObject@8",
        "DuiGetLayerManager",
        "ElementFromGadget",
        "RMLoadString",
        "RMUpdateResourceSet",
        "StrToID",
        "GetMessageEx",
        "PeekMessageEx",
        "LayerManagerInitThread",
    ]
    missing = [n for n in expected if not export_exists(dll, n)]
    ctx.record(GROUP, "UXCore.Presence",
               not missing,
               "missing=%r" % missing if missing else "12/12 clean-C exports present")


TESTS = [test_api, test_presence]
