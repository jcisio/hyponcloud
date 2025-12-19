# Setup Instructions for hyponcloud

## Building the Package

### 1. Install build tools

```bash
pip install build twine
```

### 2. Build the package

```bash
python -m build
```

This creates:

- `dist/hyponcloud-0.1.0.tar.gz` (source distribution)
- `dist/hyponcloud-0.1.0-py3-none-any.whl` (wheel)

## Testing Locally

### 1. Install in development mode

```bash
pip install -e .
```

### 2. Run tests

```bash
pip install -e ".[dev]"
```

```bash
pytest
```

### 3. Run example

```bash
python example.py your_username your_password
```

## Publishing to PyPI

### 1. Test on Test PyPI first (recommended)

```bash
# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Install from Test PyPI to verify
pip install --index-url https://test.pypi.org/simple/ hyponcloud
```

### 2. Upload to PyPI

```bash
python -m twine upload dist/*
```

You'll need PyPI credentials. Create an account at https://pypi.org/

### 3. Create API token (recommended)

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Use `__token__` as username and the token as password when uploading

## Version Management

To release a new version:

1. Update version in `pyproject.toml` and `hyponcloud/__init__.py`
2. Create a git tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. Build and upload the new version

## Using in Home Assistant

Once published to PyPI, update the Home Assistant integration's `manifest.json`:

```json
{
  "requirements": ["hyponcloud==0.1.0"]
}
```

Then update the integration code to import from the package:

```python
from hyponcloud import HyponCloud, OverviewData, AuthenticationError
```
