# WMMR Python ctypes test framework

## Star History

<a href="https://www.star-history.com/?repos=havaianasdestruido%2Fmmr-python&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=havaianasdestruido/mmr-python&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=havaianasdestruido/mmr-python&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=havaianasdestruido/mmr-python&type=date&legend=top-left" />
 </picture>
</a>


Exercises the real 32-bit WMMR core DLLs (Windows Live Movie Maker 2012)
from the Debug build directory using `ctypes`.

## Requirement: 32-bit Python

All the WMMR DLLs under `build_clean\bin\Debug` are **32-bit (x86)**.
`ctypes` from a **64-bit Python cannot load a 32-bit DLL** — `LoadLibraryW`
fails with "cannot load 32-bit DLL ... in a 64-bit process".  Run this
suite with a **32-bit Python**.

A suitable 32-bit build is the *embeddable* CPython distribution from
python.org (e.g. `python-3.11.9-embed-win32.zip`).  Extract it OUTSIDE the
repo and run:

    python32\python.exe run_tests.py C:\Users\mcmco\Desktop\WMMR\build_clean\bin\Debug

The DLL directory may also be given via the `WMMR_DLL_DIR` environment
variable; if omitted entirely it defaults to that Debug path.

## Coverage

| Group              | DLL                        | What is exercised |
| ------------------ | -------------------------- | ----------------- |
| `wlidcli`          | `wlidcli.dll`              | Login, identity handles, ticket, environment |
| `uxctl`            | `uxctl.dll`                | Process lifecycle + class-object stub |
| `uxcore`           | `UXCore.dll`               | 6 stdcall + 19 cdecl clean-C entry points |
| `wlxvideotrim`     | `WLXVideoTrim.dll`         | 5 DirectShow factory stubs |
| `wlxpipetran`      | `WLXPipetran.dll`          | `GetTFXCreateFunctions` stub |
| `wlxpipeline`      | `WLXPipeline.dll`          | Pipeline-factory loader + register |
| `wlxmp4parser`     | `WLXMP4Parser.dll`         | MP4 graph stubs + playability probe + COM |
| `wlxmps`           | `WLXMediaPublishSubscribe.dll` | PublishManager target/enumeration API + COM |
| `wlmfreadwrite`    | `WLMFReadWrite.dll`        | MF reader/writer argument guards |
| `moviemakercore`   | `MovieMakerCore.dll`       | `MovieMakerMain` CLI matrix (help-only) |
| `wlxphotobase`     | `WLXPhotoBase.dll`         | `WLXPhotoBase_Init` + presence |
| `gpurenderer`      | `GPURenderer.dll`          | Presence only (all exports C++ thiscall) |
| `dmxbici`          | `DmxBici.dll`              | BiciWrapper telemetry API (mangled stdcall) |
| `wlxphotosqm`      | `WLXPhotoSqm.dll`          | SQM stub semantics (mangled stdcall) |
| `comstubs`         | MetadataSys, MovieMakerPreviewClient, WLMFDS, WLXFaceRecognition, WLXMovieLibrary, WLXPhotoCinematic, WLXSlideshow | COM quartet + `WLXPSGetItemPropertyHandler` |
| `workflows`        | (cross-DLL)                | 6 deep scenarios tying DLLs together |

## Calling conventions

Every WMMR entry point is `__stdcall` (WINAPI) except:

* `MovieMakerMain` — `__cdecl`
* the UXCore resource/registry helpers from `Resources.cpp` — `__cdecl`

`__stdcall` functions are bound with `ctypes.WINFUNCTYPE`, `__cdecl` with
`ctypes.CFUNCTYPE`, always with explicit `argtypes`/`restype`.  Exported
names carry their native decoration: undecorated when the `.def` lists
them (`CreateAVICopierDirect`, `WLCheckCredentials`), `_Name@N` when they
are `__declspec(dllexport)` (`_PublishManager_Create@0`, `_MFReader_Open@4`,
`_UXCoreInitProcess@0`).  DmxBici and WLXPhotoSqm export C++-mangled names
that alias plain `_BiciWrapper_*` / `_Sqm_*` stdcall symbols — only the
mangled names resolve via `GetProcAddress`, so those are bound directly.

HRESULTs are `c_long`; failed values are negative and masked with
`& 0xFFFFFFFF` for comparison.  C++-mangled-only DLLs (GPURenderer,
most of WLXPhotoBase, the 4256 MovieMakerCore classes, 522 UXCore classes)
are presence-probed (load + `GetProcAddress`) but never called — the raw
ABI is thiscall and not expressible through ctypes.

## CLI

    python32\python.exe run_tests.py [DLL-DIR] \
        [--list] [--filter PATTERN]... [--skip PATTERN]... [--retries N] \
        [--junit FILE] [--json FILE] [--tap FILE] [--quiet]

* `--list` prints every registered test and exits 0.
* `--filter`/`--skip` match `group:dll:testname` (case-insensitive substring).
* `--retries N` re-runs a failing test function up to N times.
* Reports: JUnit XML, JSON and TAP 13.
* Exit codes: `0` all pass, `1` any failure, `2` usage error.

The runner prints one `PASS`/`FAIL` line per check plus a
`SUMMARY PASS=N FAIL=0` line.

## CI

`.github/workflows/ci.yml` downloads the 32-bit embeddable CPython on
`windows-latest`, byte-compiles everything, lists the tests, and runs the
full suite when the `WMMR_DLL_DIR` repository secret points at a directory
containing the DLLs.
