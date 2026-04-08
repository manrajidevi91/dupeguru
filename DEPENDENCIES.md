# Dependency Matrix

This repository now uses two dependency tracks:

- `requirements.txt` for the runtime/app path on the Python 3.7 compatibility line.
- `requirements-build.txt` for the legacy build/docs path used by `build.py` and `run.bat`.
- `requirements-extra.txt` for legacy test/package helpers.
- `requirements-modern.txt` for Python 3.12+ tooling in CI and developer environments.

## Runtime

| Package | Current file | Latest practical track | Notes |
| --- | --- | --- | --- |
| `distro` | `requirements.txt` | `1.9.0` | Safe on Python 3.7. |
| `mutagen` | `requirements.txt` | `1.47.0` | Safe on Python 3.7. |
| `polib` | `requirements.txt` | `1.2.0` | Used by localization/build scripts. |
| `PyQt5` | `requirements.txt` | `5.15.10` on Python 3.7 | `5.15.11` requires Python 3.8+. |
| `pywin32` | `requirements.txt` | `308` on Python 3.7 | `311` requires Python 3.8+. |
| `semantic-version` | `requirements.txt` | `2.10.0` | Safe on Python 3.7. |
| `Send2Trash` | `requirements.txt` | `1.8.3` on Python 3.7 | `2.1.0` requires Python 3.8+. |
| `xxhash` | `requirements.txt` | `3.6.0` | Safe on Python 3.7. |

## Build And Docs

| Package | File | Track |
| --- | --- | --- |
| `sphinx` | `requirements-build.txt` | Legacy build path for Python 3.7-compatible environments. |
| `sphinx` | `requirements-modern.txt` | Latest docs tooling on Python 3.12+. |

## Test And Packaging Helpers

| Package | File | Track |
| --- | --- | --- |
| `pytest` | `requirements-extra.txt` | Legacy test harness. |
| `pyinstaller` | `requirements-extra.txt` | Legacy packaging helper. |
| `pytest` | `requirements-modern.txt` | Latest test tooling on Python 3.12+. |
| `flake8` | `requirements-modern.txt` | Latest lint tooling on Python 3.12+. |
| `black` | `requirements-modern.txt` | Latest formatting tooling on Python 3.12+. |
| `pyinstaller` | `requirements-modern.txt` | Latest packaging tooling on Python 3.12+. |
| `pip`, `setuptools`, `wheel` | `requirements-modern.txt` | Bootstrap tools for the modern CI/dev path. |

## What Changed

- Runtime dependencies were bumped to the newest versions that still preserve the Python 3.7 line.
- Build/documentation dependencies were split out so `build.py` no longer requires Sphinx unless the build path needs it.
- Modern lint/test/packaging tooling now lives in a separate Python 3.12+ file so it can move independently of the runtime floor.
