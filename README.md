# MIT Kavli Institute PyPI Index

A private Python package index for the MIT Kavli Institute for Astrophysics, hosted on GitHub Pages.

## Features

* **🏛️ GitHub-hosted** - Leverages GitHub Pages for reliable hosting
* **📦 File-based distribution** - Hosts wheel and tar.gz files directly
* **🔒 Private package support** - Requires GitHub authentication for private packages
* **🚀 Automated workflows** - GitHub Actions for package management
* **🚨 Security alerts** - Warns about potential supply chain attacks

## Installation

Install packages from this index using pip:

```bash
pip install <package_name> --extra-index-url https://mit-kavli-institute.github.io/MIT-Kavli-PyPi/
```

For private packages, you'll need to authenticate with GitHub.

## Package Management via GitHub Actions

All package operations are performed through GitHub Actions workflows that create pull requests for review.

### Register a New Package

**Workflow**: `.github/workflows/register.yml`

To register a new package:
1. Go to the Actions tab
2. Select "register" workflow
3. Click "Run workflow"
4. Fill in the required parameters:
   - **package_name**: Name of your package (will be normalized per PEP 503)
   - **version**: Version/tag of the package (e.g., "1.0.0" or "v1.0.0")
   - **author**: Author name(s)
   - **short_desc**: Brief description for the index page
   - **homepage**: GitHub repository URL

The workflow will:
- Download wheel/tar.gz files from the GitHub release
- Fall back to building from source if release assets aren't available
- Create a PR with the package registration

### Update an Existing Package

**Workflow**: `.github/workflows/update.yml`

To update a package to a new version:
1. Go to the Actions tab
2. Select "update" workflow  
3. Click "Run workflow"
4. Fill in the required parameters:
   - **package_name**: Name of the existing package
   - **version**: New version/tag

The workflow will:
- Download the new version's files
- Update the package page with the new version
- Create a PR with the changes

### Delete a Package

**Workflow**: `.github/workflows/delete.yml`

To remove a package from the index:
1. Go to the Actions tab
2. Select "delete" workflow
3. Click "Run workflow"
4. Fill in the required parameter:
   - **package_name**: Name of the package to delete

The workflow will:
- Remove the package directory and all associated files
- Update the main index
- Create a PR for the deletion

## Architecture Overview

This PyPI index follows [PEP 503](https://www.python.org/dev/peps/pep-0503/) standards:

- **Static HTML pages** serve as the package index
- **Package files** (wheel/tar.gz) are stored in the `packages/` directory
- **Package names** are normalized (lowercase, hyphens instead of underscores)
- **Dual distribution**: Primary method uses hosted files, falls back to git URLs
- **No backend required**: Everything runs as static files on GitHub Pages

Key components:
- `index.html`: Main package listing
- `pkg_template.html`: Template for individual package pages
- `.github/actions.py`: Core logic for package management
- `.github/download_release.py`: Handles downloading files from GitHub releases

## Security Considerations

### Supply Chain Attack Protection

This index includes automated protection against supply chain attacks. When you visit a package page, it checks if a package with the same name exists on public PyPI with a higher version. If found, a warning is displayed instead of the install command.

This is important because pip's `--extra-index-url` feature checks all indexes and installs the highest version found, which could be a malicious package on public PyPI.

**Best practices:**
- Use unique package names that don't conflict with public packages
- Regularly check for warnings on your package pages
- Consider using a package name prefix for your organization

## FAQ

### Is it secure?

The index itself is public, but it only contains links and metadata. Private packages require GitHub authentication when pip clones the repository. All package data is served over HTTPS.

### How do I install private packages in Docker?

Use a `.netrc` file with Docker secrets:

1. Create a `.netrc` file:
```
machine github.com
	login <github_username>
	password <github_token>
```

2. In your Dockerfile:
```dockerfile
# syntax=docker/dockerfile:experimental
FROM python:3
RUN --mount=type=secret,id=netrc,dst=/root/.netrc \
    pip install <package> --extra-index-url https://mit-kavli-institute.github.io/MIT-Kavli-PyPi/
```

3. Build with: `DOCKER_BUILDKIT=1 docker build --secret id=netrc,src=./.netrc .`

### What if my package name conflicts with a public package?

You can register it with a different name in this index. For example, if you have a private `numpy` package, register it as `kavli-numpy`. When installed, it will still import as `numpy` in Python.

### How are package versions handled?

- Use GitHub releases with semantic versioning
- Tags should follow the format: `1.2.3` or `v1.2.3`
- Stable versions (without alpha/beta/rc) are marked as "main" versions
- All versions are listed on the package page

### Can I use this without GitHub releases?

Yes, the system will fall back to building from source if no release assets are found. However, using releases with pre-built wheel/tar.gz files is recommended for better reliability and faster installation.

## Technical Details

- **Python compatibility**: Workflows test against Python 3.9-3.13
- **Package name normalization**: Follows PEP 503 (lowercase, underscores → hyphens)
- **HTML templates**: Uses BeautifulSoup for manipulation
- **File storage**: `packages/<normalized-name>/` directory structure
- **Client-side enhancements**: JavaScript for README rendering and PyPI checks

---

For issues or contributions, please use the GitHub repository's issue tracker.