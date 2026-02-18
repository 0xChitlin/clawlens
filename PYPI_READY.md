# PyPI Publishing — Ready

The package is built and ready to publish.

## To publish:
1. Create account at pypi.org (or use existing)
2. Run: `pip install twine`
3. Run: `cd ~/.openclaw/workspace/clawlens && python -m twine upload dist/*`
4. Enter your PyPI username and password (or API token)

## Built files:
- `dist/clawlens-0.9.3-py3-none-any.whl`
- `dist/clawlens-0.9.3.tar.gz`

## Notes:
- Package is NOT currently on PyPI (confirmed 404)
- Version: 0.9.3
- Entry point: `clawlens = dashboard:main`
- Author: ClawWallet
- URL: https://github.com/0xChitlin/clawlens
