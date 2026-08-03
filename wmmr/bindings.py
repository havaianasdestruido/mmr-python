"""ctypes binding helpers for the 32-bit WMMR core DLLs.

Every WMMR entry point here is __stdcall (WINAPI) except:

* ``MovieMakerMain``  (__cdecl)
* the UXCore resource/registry helpers from Resources.cpp (__cdecl)

``__stdcall`` functions are bound with ``ctypes.WINFUNCTYPE`` and
``__cdecl`` functions with ``ctypes.CFUNCTYPE``, always with an explicit
``argtypes``/``restype`` so no implicit int->pointer coercion or 64-bit
HRESULT truncation can occur.  HRESULTs are c_long and failed values come
back negative; mask with :func:`hr` for the unsigned 0x8xxxxxxx form.
"""

import ctypes
import ctypes.wintypes as wt
import os

# ---------------------------------------------------------------------------
# HRESULT constants
# ---------------------------------------------------------------------------
S_OK = 0x00000000
S_FALSE = 0x00000001
E_FAIL = 0x80004005
E_UNEXPECTED = 0x8000FFFF
E_NOTIMPL = 0x80004001
E_INVALIDARG = 0x80070057
E_OUTOFMEMORY = 0x8007000E
CLASS_E_CLASSNOTAVAILABLE = 0x80040111

# The 32-bit embeddable CPython does not ship wintypes.HRESULT; define it.
HRESULT = ctypes.c_long


def hr(hrcode):
    """Return a signed HRESULT as its unsigned 0x........ form."""
    return hrcode & 0xFFFFFFFF


class GUID(ctypes.Structure):
    """Win32 GUID (layout matches the native struct)."""
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


def bind_stdcall(dll, name, restype, *argtypes):
    """Bind an exported __stdcall function with an explicit prototype."""
    return ctypes.WINFUNCTYPE(restype, *argtypes)((name, dll))


def bind_cdecl(dll, name, restype, *argtypes):
    """Bind an exported __cdecl function with an explicit prototype."""
    return ctypes.CFUNCTYPE(restype, *argtypes)((name, dll))


def load_dll(dll_dir, fname, cdecl=False):
    """Load a WMMR DLL; ``cdecl`` selects CDLL for __cdecl modules."""
    path = os.path.join(dll_dir, fname)
    return (ctypes.CDLL if cdecl else ctypes.WinDLL)(path)


def export_exists(dll, name):
    """Return True if the named export resolves via GetProcAddress."""
    try:
        dll[name]
        return True
    except AttributeError:
        return False
