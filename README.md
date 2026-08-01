# WMMR Python ctypes test suite

This suite exercises the real 32-bit WMMR core DLLs from the Debug build
directory using `ctypes`.

## Requirement: 32-bit Python

All the WMMR DLLs under `build_clean\bin\Debug` are **32-bit (x86)**.
`ctypes` from a **64-bit Python cannot load a 32-bit DLL** — `LoadLibraryW`
fails with "cannot load 32-bit DLL ... in a 64-bit process" (`%1 is not a
valid Win32 application`).  You MUST run this suite with a **32-bit Python**.

The machine's installed system Python (Python 3.14, 64-bit) is not usable.
A suitable 32-bit build is the *embeddable* CPython distribution from
python.org, e.g.:

    https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip

Extract it OUTSIDE the repo (keep it out of git) and run:

    python32\python.exe run_tests.py C:\Users\mcmco\Desktop\WMMR\build_clean\bin\Debug

(If the DLL directory argument is omitted, it defaults to that Debug path.)

## What it covers

| DLL               | Function(s)                                                     | Expectation                     |
| ----------------- | --------------------------------------------------------------- | ------------------------------- |
| `wlidcli.dll`     | `WLCheckCredentials`                                            | `S_OK`                          |
|                   | `WLClogin`                                                      | `S_OK`, signs identity in       |
|                   | `WLCreateIdentityHandle`                                        | increments from `0x1000`        |
|                   | `WLGetEnvironment`                                              | `"production"` (freed)          |
|                   | `WLGetTicket`                                                   | string contains `"ticket="`     |
|                   | `WLFreeMemory`                                                  | `void`                          |
|                   | `WLIsSignedIn`                                                  | `TRUE` after login              |
| `uxctl.dll`       | `UxControlsInitProcess` / `UxControlsUninitProcess`             | `S_OK` / `void`                 |
|                   | `UxControlsCreateObject`                                        | `CLASS_E_CLASSNOTAVAILABLE`     |
| `WLXVideoTrim.dll`| `CreateAVICopierDirect`, `CreateVideoCopierFromMediaType`, ...  | `E_NOTIMPL`                     |
| `WLXPipetran.dll` | `GetTFXCreateFunctions`                                         | `E_NOTIMPL`, count `0`          |
| `MovieMakerCore.dll` | `MovieMakerMain` (`--help`)                                  | return `0`                      |

## Calling conventions

Every WMMR entry point here is `__stdcall` (WINAPI) except
`MovieMakerMain`, which is `__cdecl`.  In 32-bit Python the exported
functions are bound explicitly:

* `__stdcall` functions -> `ctypes.WINFUNCTYPE(restype, *argtypes)((name, dll))`
* `__cdecl`  functions -> `ctypes.CFUNCTYPE(restype, *argtypes)((name, dll))`
  (loaded with `ctypes.CDLL`)

with explicit `argtypes`/`restype` for every function (no default/int
conversions, no 64-bit `HRESULT` truncation issues).

## Exit code

The runner prints one `PASS`/`FAIL` line per check, a final
`SUMMARY PASS=N FAIL=0` line, and exits `0` iff all checks pass.
