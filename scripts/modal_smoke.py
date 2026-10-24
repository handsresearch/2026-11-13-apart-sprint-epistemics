"""Smoke test: check Modal auth and remote execution work (CPU only, a few cents at most).

Run from a laptop: Claude cloud sessions cannot reach Modal (its gRPC client cannot use their HTTPS proxy).
"""

import modal

app = modal.App("apart-sprint-smoke")


@app.function(timeout=60)
def square(x: int) -> int:
    import platform

    print(f"running on {platform.node()} / python {platform.python_version()}")
    return x * x


@app.local_entrypoint()
def main():
    results = list(square.map(range(4)))
    assert results == [0, 1, 4, 9], results
    print("modal OK:", results)
