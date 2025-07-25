# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub-hosted PyPI index for the MIT Kavli Institute for Astrophysics. It provides a private Python package repository using GitHub Pages that conforms to PEP503 standards. The index now supports both wheel/tar.gz file distribution and git-based installation (fallback).

## Key Commands

### Development Setup
```bash
# Install development dependencies
python -m pip install --upgrade pip
pip install beautifulsoup4 build
```

### Testing
```bash
# Run unit tests
python .github/tests.py

# Run a specific test
python .github/tests.py TestClass.test_method_name

# Start local PyPI server for testing (runs on port 8000)
python -m http.server
```

### Package Management
```bash
# Update all packages programmatically
python update_pkgs.py

# Migrate existing packages to wheel/tar.gz distribution
python migrate_packages.py

# Install a package from this index
pip install <package-name> --extra-index-url https://mit-kavli-institute.github.io/github-hosted-pypi/

# Install a private package (requires GitHub token)
pip install <package-name> --extra-index-url https://mit-kavli-institute.github.io/github-hosted-pypi/ --index-url https://<token>@github.com/
```

### GitHub Actions (Manual Triggers)
```bash
# All package operations are done through GitHub Actions:
# 1. Go to Actions tab
# 2. Select workflow: register.yml, update.yml, or delete.yml
# 3. Click "Run workflow" and fill in the required fields
# 4. Review and merge the created PR
```

## Architecture Overview

### Core Components

1. **Package Management System** (`.github/actions.py`): 
   - Handles REGISTER, UPDATE, and DELETE operations
   - Downloads wheel/tar.gz files from GitHub releases
   - Falls back to building from source if needed
   - Uses BeautifulSoup for HTML manipulation
   - Maintains PEP 503 compliance for package naming
   - Key functions: `register()`, `update()`, `delete()`, `get_package_links()`

2. **Static Site Structure**:
   - `index.html`: Main package listing with grid layout
   - `pkg_template.html`: Template for individual package pages (contains placeholders like `_package_name`, `_version`, `_link`)
   - Package directories (e.g., `transformers/`, `private-hello/`): Each contains an index.html
   - `packages/` directory: Stores actual wheel and tar.gz files organized by package name

3. **Client-Side Enhancements**:
   - `static/pypi_checker.js`: Checks for supply chain attacks by comparing with public PyPI
   - `static/package_page.js`: Handles dynamic README loading and version switching

4. **GitHub Actions Workflows** (`.github/workflows/`):
   - `register.yml`: Registers new packages and downloads their files (requires: package_name, version, author, short_desc, homepage)
   - `update.yml`: Updates existing packages with new versions and files (requires: package_name, version)
   - `delete.yml`: Removes packages from the index and their files (requires: package_name)
   - `tests.yml`: Runs automated tests on push/PR
   - All workflows support Python 3.9-3.13 and create PRs for review

5. **Package Distribution System**:
   - `.github/download_release.py`: Downloads wheel/tar.gz from GitHub releases
   - Falls back to building from source if release assets not available
   - Supports both public and private repositories
   - `migrate_packages.py`: Migrates existing packages from git URLs to file distribution

### Key Design Patterns

- **No Backend**: Everything runs as static files on GitHub Pages
- **Template-Based**: Single template (`pkg_template.html`) for all package pages with placeholder replacement
- **Dual Distribution**: Primary method uses wheel/tar.gz files; falls back to git URLs without egg parameters
- **Progressive Enhancement**: Works without JavaScript, enhanced features with JS enabled
- **PR-Based Updates**: All changes go through pull requests for review
- **File-Based Package Hosting**: Wheel and tar.gz files stored in `packages/` directory

### Important Implementation Details

- Package names are normalized to lowercase with underscores replaced by hyphens (PEP 503)
- Version stability detection: versions without pre-release identifiers (alpha, beta, rc) are marked as stable
- The main index URL is: `https://mit-kavli-institute.github.io/github-hosted-pypi/`
- Private packages require GitHub authentication token for installation
- HTML files serve as the database - all package metadata is stored in HTML
- The `update_pkgs.py` script can batch update multiple packages from their GitHub releases
- Package files (wheel/tar.gz) are downloaded from GitHub releases during registration/update
- No egg parameters are used in URLs - modern pip versions handle package name detection automatically