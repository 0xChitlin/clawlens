# Publish `clawlens` To PyPI

From repo root:

```bash
cd packages/clawlens
python3 -m pip install --upgrade build twine
python3 -m build
python3 -m twine upload dist/*
```

After publish:

```bash
pip install clawlens
clawlens
```

Notes:
- This alias package depends on `openclaw-dashboard>=0.2.8`.
- Keep versions in sync when major dashboard behavior changes.
