# Setup Instructions for hyponcloud

## Building the Package

### 1. Install build tools

```bash
pip install build twine
```

**Note:** The build process requires `setuptools-scm>=8.0` which is automatically installed as a build dependency to generate version numbers from git tags.

### 2. Build the package

```bash
python -m build
```

This creates distribution files in the `dist/` directory:

- `dist/hyponcloud-X.Y.Z.tar.gz` (source distribution)
- `dist/hyponcloud-X.Y.Z-py3-none-any.whl` (wheel)

The version (X.Y.Z) is automatically determined from your git tags using `setuptools-scm`.

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

### 4. Set up pre-commit hooks (optional but recommended)

Pre-commit hooks run quality checks automatically before each commit:

```bash
pre-commit install
```

This will run ruff, mypy, and other checks before allowing commits.

### 3. Run example

```bash
python example.py your_username your_password
```

## Publishing to PyPI

Publishing to PyPI is automated through GitHub Actions. When you push a git tag, the workflow automatically builds and publishes the package.

### Version Management

This project uses `setuptools-scm` for automatic version management based on git tags.

To release a new version:

1. Create a git tag with the version number:

   ```bash
   git tag v0.1.2
   git push origin v0.1.2
   ```

2. GitHub Actions will automatically:
   - Build the package with the version from the tag
   - Publish to PyPI
   - Create a GitHub release

### How it works

- **setuptools-scm** automatically determines the version from git tags
- Version is written to `hyponcloud/_version.py` during build
- No need to manually update version numbers in the code
- Development versions are automatically assigned based on commits since the last tag
- The `.github/workflows/publish.yml` workflow handles building and publishing

## Using in Home Assistant

Once published to PyPI, update the Home Assistant integration's `manifest.json`:

```json
{
  "requirements": ["hyponcloud==X.Y.Z"]
}
```

Replace `X.Y.Z` with the desired version number. Then update the integration code to import from the package:

```python
from hyponcloud import HyponCloud, OverviewData, AuthenticationError
```
