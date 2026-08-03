"""wlidcli.dll -- Windows Live ID client stubs (7 named stdcall exports).

Lifecycle: WLCreateIdentityHandle gives a handle; WLClogin signs it in;
WLGetTicket returns a CoTaskMemAlloc'ed ticket string freed with
WLFreeMemory; WLGetEnvironment returns the simulated L"production" value.
"""

import ctypes
import ctypes.wintypes as wt

from wmmr.bindings import (S_OK, HRESULT, bind_stdcall, load_dll)

GROUP = "wlidcli"
DLL = "wlidcli.dll"


def bind(ctx):
    dll = load_dll(ctx.dll_dir, DLL)
    return {
        "WLCheckCredentials": bind_stdcall(
            dll, "WLCheckCredentials", HRESULT, wt.LPCWSTR),
        "WLClogin": bind_stdcall(
            dll, "WLClogin", HRESULT,
            wt.HWND, wt.LPCWSTR, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p)),
        "WLCreateIdentityHandle": bind_stdcall(
            dll, "WLCreateIdentityHandle", ctypes.c_uint32),
        "WLGetEnvironment": bind_stdcall(
            dll, "WLGetEnvironment", HRESULT,
            ctypes.POINTER(ctypes.c_void_p)),
        "WLGetTicket": bind_stdcall(
            dll, "WLGetTicket", HRESULT,
            ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)),
        "WLFreeMemory": bind_stdcall(dll, "WLFreeMemory", None, ctypes.c_void_p),
        "WLIsSignedIn": bind_stdcall(
            dll, "WLIsSignedIn", wt.BOOL, ctypes.c_uint32),
    }


def test_api(ctx):
    api = bind(ctx)

    # WLCheckCredentials(LPCWSTR) -> S_OK
    hr = api["WLCheckCredentials"](u"user@example.com")
    ctx.record(GROUP, "wlidcli.WLCheckCredentials", hr == S_OK,
               "HRESULT=0x%08X" % hr)

    # WLGetEnvironment(LPCWSTR*) -> S_OK, "production", freed via WLFreeMemory
    env_buf = ctypes.c_void_p()
    hr = api["WLGetEnvironment"](ctypes.byref(env_buf))
    env = ctypes.cast(env_buf, ctypes.c_wchar_p).value
    api["WLFreeMemory"](env_buf)
    ctx.record(GROUP, "wlidcli.WLGetEnvironment",
               hr == S_OK and env == "production",
               "HRESULT=0x%08X value=%r" % (hr, env))

    # WLCreateIdentityHandle -> DWORD, increments starting at 0x1000
    h1 = api["WLCreateIdentityHandle"]()
    h2 = api["WLCreateIdentityHandle"]()
    ctx.record(GROUP, "wlidcli.WLCreateIdentityHandle",
               h1 >= 0x1000 and h2 == h1 + 1,
               "h1=0x%X h2=0x%X" % (h1, h2))

    # WLClogin(HWND, LPCWSTR, DWORD, LPVOID*) -> S_OK and signs the identity in
    token = ctypes.c_void_p()
    hr = api["WLClogin"](None, u"user@example.com", h1, ctypes.byref(token))
    ctx.record(GROUP, "wlidcli.WLClogin", hr == S_OK, "HRESULT=0x%08X" % hr)
    ctx.record(GROUP, "wlidcli.WLIsSignedIn",
               api["WLIsSignedIn"](h1) != 0,
               "signed-in for handle 0x%X" % h1)

    # WLGetTicket(DWORD, LPWSTR*) -> S_OK, "ticket=" substring, WLFreeMemory
    ticket_buf = ctypes.c_void_p()
    hr = api["WLGetTicket"](h1, ctypes.byref(ticket_buf))
    ticket = ctypes.cast(ticket_buf, ctypes.c_wchar_p).value
    api["WLFreeMemory"](ticket_buf)
    ctx.record(GROUP, "wlidcli.WLGetTicket",
               hr == S_OK and ticket and "ticket=" in ticket,
               "HRESULT=0x%08X value=%r" % (hr, ticket))


TESTS = [test_api]
