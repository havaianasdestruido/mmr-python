"""Contract modules: one module per DLL or logical DLL group.

Each module exposes ``GROUP`` (short name), ``DLL`` (the filename it
exercises) and ``TESTS`` (list of ``test(ctx)`` functions).  ``ctx`` is a
:class:`wmmr.runner.Session` whose ``record(group, name, ok, detail)``
appends a result.

``GROUPS`` is the ordered discovery list used by the runner.
"""

from wmmr.contracts import (
    comstubs,
    dmxbici,
    gpurenderer,
    moviemakercore,
    uxctl,
    uxcore,
    wlidcli,
    wlmfreadwrite,
    wlxmp4parser,
    wlxmps,
    wlxphotobase,
    wlxphotosqm,
    wlxpipeline,
    wlxpipetran,
    wlxvideotrim,
)

GROUPS = [
    wlidcli,
    uxctl,
    uxcore,
    wlxvideotrim,
    wlxpipetran,
    wlxpipeline,
    wlxmp4parser,
    wlxmps,
    wlmfreadwrite,
    moviemakercore,
    wlxphotobase,
    gpurenderer,
    dmxbici,
    wlxphotosqm,
    comstubs,
]
