# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub-hosted PyPI index for the MIT Kavli Institute for Astrophysics. It provides a private Python package repository using GitHub Pages that conforms to PEP503 standards.

## Key Commands

### Development Setup
```bash
# Install development dependencies
python -m pip install --upgrade pip
pip install beautifulsoup4
```

### Testing
```bash
# Run unit tests
python .github/tests.py

# Start local PyPI server for testing (runs on port 8000)
python -m http.server
```

### Package Management
```bash
# Update all packages programmatically
python update_pkgs.py

# Install a package from this index
pip install <package-name> --extra-index-url https://mit-kavli-institute.github.io/github-hosted-pypi/
```

## Architecture Overview

### Core Components

1. **Package Management System** (`.github/actions.py`): 
   - Handles REGISTER, UPDATE, and DELETE operations
   - Uses BeautifulSoup for HTML manipulation
   - Maintains PEP 503 compliance for package naming

2. **Static Site Structure**:
   - `index.html`: Main package listing with grid layout
   - `pkg_template.html`: Template for individual package pages
   - Package directories (e.g., `transformers/`, `private-hello/`): Each contains an index.html

3. **Client-Side Enhancements**:
   - `static/pypi_checker.js`: Checks for supply chain attacks by comparing with public PyPI
   - `static/package_page.js`: Handles dynamic README loading and version switching

4. **GitHub Actions Workflows**:
   - Manual triggers for package operations (register/update/delete)
   - All changes go through pull requests
   - Located in `.github/workflows/`

### Key Design Patterns

- **No Backend**: Everything runs as static files on GitHub Pages
- **Template-Based**: Single template (`pkg_template.html`) for all package pages with placeholder replacement
- **Git-Based URLs**: Packages installed directly from GitHub using format: `git+{homepage}@{version}#egg={name}-{version}`
- **Progressive Enhancement**: Works without JavaScript, enhanced features with JS enabled

### Important Notes

- Package names are normalized to lowercase with underscores replaced by hyphens (PEP 503)
- Version stability detection: versions without pre-release identifiers (alpha, beta, rc) are marked as stable
- The main index URL is: `https://mit-kavli-institute.github.io/github-hosted-pypi/`
- Private packages require GitHub authentication token for installation