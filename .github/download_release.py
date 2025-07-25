#!/usr/bin/env python3
"""
Utility to download wheel and tar.gz files from GitHub releases.
Falls back to building from source if wheels are not available.
"""

import os
import json
import urllib.request
import urllib.error
import tarfile
import zipfile
import shutil
import subprocess
import tempfile
from pathlib import Path


def get_release_assets(repo_url, version):
    """
    Fetch release assets from GitHub API.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        version: Version tag (e.g., v1.0.0 or 1.0.0)
    
    Returns:
        List of asset dictionaries with download URLs
    """
    # Extract owner and repo from URL
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]
    
    # Try with and without 'v' prefix
    versions_to_try = [version]
    if not version.startswith('v'):
        versions_to_try.append(f'v{version}')
    if version.startswith('v'):
        versions_to_try.append(version[1:])
    
    for v in versions_to_try:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{v}"
        
        try:
            with urllib.request.urlopen(api_url) as response:
                data = json.loads(response.read())
                return data.get('assets', [])
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
    
    raise ValueError(f"No release found for {repo_url} version {version}")


def download_file(url, dest_path):
    """Download a file from URL to destination path."""
    print(f"Downloading {url}")
    
    headers = {'User-Agent': 'MIT-Kavli-PyPi'}
    request = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(request) as response:
        with open(dest_path, 'wb') as f:
            shutil.copyfileobj(response, f)
    
    return dest_path


def find_package_files(assets, package_name):
    """
    Find wheel and tar.gz files in release assets.
    
    Returns:
        tuple: (wheel_url, tar_gz_url) - either can be None
    """
    wheel_url = None
    tar_gz_url = None
    
    for asset in assets:
        name = asset['name']
        url = asset['browser_download_url']
        
        # Look for wheel files
        if name.endswith('.whl') and package_name.replace('-', '_') in name:
            wheel_url = url
        
        # Look for tar.gz files
        elif name.endswith('.tar.gz'):
            tar_gz_url = url
    
    return wheel_url, tar_gz_url


def build_from_source(repo_url, version, package_name, output_dir):
    """
    Clone repository and build wheel from source.
    
    Returns:
        tuple: (wheel_path, tar_gz_path)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Clone the repository at specific version
        repo_dir = os.path.join(temp_dir, 'repo')
        
        print(f"Cloning {repo_url} at {version}")
        subprocess.run([
            'git', 'clone', '--depth', '1', '--branch', version,
            repo_url, repo_dir
        ], check=True)
        
        # Install build dependencies
        subprocess.run([
            'pip', 'install', '--quiet', 'build'
        ], check=True)
        
        # Build the package
        print(f"Building package from source")
        subprocess.run([
            'python', '-m', 'build', '--outdir', temp_dir
        ], cwd=repo_dir, check=True)
        
        # Find generated files
        wheel_path = None
        tar_gz_path = None
        
        for file in os.listdir(temp_dir):
            if file.endswith('.whl'):
                wheel_path = os.path.join(temp_dir, file)
                shutil.copy2(wheel_path, output_dir)
                wheel_path = os.path.join(output_dir, file)
            elif file.endswith('.tar.gz'):
                tar_gz_path = os.path.join(temp_dir, file)
                shutil.copy2(tar_gz_path, output_dir)
                tar_gz_path = os.path.join(output_dir, file)
        
        return wheel_path, tar_gz_path


def download_package_files(repo_url, version, package_name, output_dir):
    """
    Download or build package files for a specific version.
    
    Args:
        repo_url: GitHub repository URL
        version: Version to download
        package_name: Name of the package
        output_dir: Directory to save files
    
    Returns:
        dict: Paths to downloaded/built files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Try to get files from GitHub releases
        assets = get_release_assets(repo_url, version)
        wheel_url, tar_gz_url = find_package_files(assets, package_name)
        
        result = {
            'wheel': None,
            'tar_gz': None,
            'version': version
        }
        
        # Download wheel if available
        if wheel_url:
            wheel_name = wheel_url.split('/')[-1]
            wheel_path = os.path.join(output_dir, wheel_name)
            if not os.path.exists(wheel_path):
                download_file(wheel_url, wheel_path)
            result['wheel'] = wheel_path
        
        # Download tar.gz if available
        if tar_gz_url:
            tar_name = tar_gz_url.split('/')[-1]
            tar_path = os.path.join(output_dir, tar_name)
            if not os.path.exists(tar_path):
                download_file(tar_gz_url, tar_path)
            result['tar_gz'] = tar_path
        
        # If no files found in release, try building from source
        if not wheel_url and not tar_gz_url:
            print(f"No package files in release, building from source")
            wheel_path, tar_gz_path = build_from_source(
                repo_url, version, package_name, output_dir
            )
            result['wheel'] = wheel_path
            result['tar_gz'] = tar_gz_path
        
        return result
        
    except Exception as e:
        print(f"Error downloading package files: {e}")
        # Fallback to building from source
        try:
            print(f"Falling back to building from source")
            wheel_path, tar_gz_path = build_from_source(
                repo_url, version, package_name, output_dir
            )
            return {
                'wheel': wheel_path,
                'tar_gz': tar_gz_path,
                'version': version
            }
        except Exception as build_error:
            print(f"Failed to build from source: {build_error}")
            raise


def main():
    """Example usage and testing."""
    # Test with a known package
    test_cases = [
        {
            'repo_url': 'https://github.com/astariul/public-hello',
            'version': '0.2',
            'package_name': 'public-hello',
            'output_dir': 'packages/public-hello'
        }
    ]
    
    for test in test_cases:
        print(f"\nTesting download for {test['package_name']} v{test['version']}")
        try:
            result = download_package_files(**test)
            print(f"Success! Downloaded files:")
            if result['wheel']:
                print(f"  Wheel: {result['wheel']}")
            if result['tar_gz']:
                print(f"  Tar.gz: {result['tar_gz']}")
        except Exception as e:
            print(f"Failed: {e}")


if __name__ == "__main__":
    main()