#!/usr/bin/env python3
"""
Migration script to update existing packages to use wheel/tar.gz distribution
instead of git URLs with egg parameters.
"""

import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add the .github directory to path to import download_release
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.github'))
from download_release import download_package_files


def extract_package_info_from_html(package_dir):
    """
    Extract package information from the package's index.html file.
    
    Returns:
        dict with package_name, homepage, and versions
    """
    index_path = os.path.join(package_dir, 'index.html')
    
    with open(index_path, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # Extract package name from header
    header = soup.find('section', class_='header')
    package_name = header.contents[2].strip() if header else os.path.basename(package_dir)
    
    # Extract homepage URL
    homepage_button = soup.find('button', id='repoHomepage')
    homepage = None
    if homepage_button and homepage_button.get('onclick'):
        onclick = homepage_button['onclick']
        match = re.search(r"openLinkInNewTab\('(.+?)'\)", onclick)
        if match:
            homepage = match.group(1)
    
    # Extract versions
    versions = []
    version_section = soup.find('section', class_='versions')
    if version_section:
        for div in version_section.find_all('div'):
            if div.get('id') and div['id'] not in ['versions']:
                version_id = div['id']
                anchor = div.find('a')
                if anchor and anchor.get('href'):
                    # Extract version from git URL or use div id
                    href = anchor['href']
                    if '@' in href:
                        version_match = re.search(r'@([^#]+)', href)
                        if version_match:
                            version_id = version_match.group(1)
                    versions.append({
                        'version': version_id,
                        'div': div,
                        'anchor': anchor
                    })
    
    return {
        'package_name': package_name,
        'homepage': homepage,
        'versions': versions,
        'soup': soup,
        'index_path': index_path
    }


def migrate_package(package_dir):
    """
    Migrate a single package to use wheel/tar.gz distribution.
    """
    print(f"\nMigrating package: {os.path.basename(package_dir)}")
    
    try:
        # Extract package information
        info = extract_package_info_from_html(package_dir)
        
        if not info['homepage']:
            print(f"  ⚠️  No homepage found, skipping")
            return False
        
        package_name = info['package_name']
        norm_pkg_name = re.sub(r"[-_.]+", "-", package_name).lower()
        package_output_dir = os.path.join('packages', norm_pkg_name)
        
        # Process each version
        updated = False
        for version_info in info['versions']:
            version = version_info['version']
            print(f"  Processing version: {version}")
            
            try:
                # Download package files
                package_files = download_package_files(
                    info['homepage'], version, package_name, package_output_dir
                )
                
                # Update the anchor element
                anchor = version_info['anchor']
                base_url = f"../packages/{norm_pkg_name}/"
                
                if package_files.get('wheel'):
                    wheel_filename = os.path.basename(package_files['wheel'])
                    anchor['href'] = f"{base_url}{wheel_filename}"
                    anchor['title'] = wheel_filename
                    print(f"    ✓ Updated to wheel: {wheel_filename}")
                    updated = True
                elif package_files.get('tar_gz'):
                    tar_filename = os.path.basename(package_files['tar_gz'])
                    anchor['href'] = f"{base_url}{tar_filename}"
                    anchor['title'] = tar_filename
                    print(f"    ✓ Updated to tar.gz: {tar_filename}")
                    updated = True
                else:
                    # Update to git URL without egg parameter
                    current_href = anchor['href']
                    if '#egg=' in current_href:
                        new_href = current_href.split('#egg=')[0]
                        anchor['href'] = new_href
                        print(f"    ✓ Removed egg parameter from git URL")
                        updated = True
                
            except Exception as e:
                print(f"    ⚠️  Failed to download files: {e}")
                # Still remove egg parameter
                current_href = anchor.get('href', '')
                if '#egg=' in current_href:
                    new_href = current_href.split('#egg=')[0]
                    anchor['href'] = new_href
                    print(f"    ✓ Removed egg parameter from git URL")
                    updated = True
        
        # Save updated HTML if changes were made
        if updated:
            with open(info['index_path'], 'w') as f:
                f.write(str(info['soup']))
            print(f"  ✅ Migration complete for {package_name}")
            return True
        else:
            print(f"  ℹ️  No changes needed for {package_name}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error migrating {os.path.basename(package_dir)}: {e}")
        return False


def main():
    """
    Migrate all packages in the repository.
    """
    print("🚀 Starting package migration to wheel/tar.gz distribution\n")
    
    # Find all package directories
    package_dirs = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and os.path.exists(os.path.join(item, 'index.html')):
            # Skip special directories
            if item not in ['.git', '.github', 'static', 'packages']:
                package_dirs.append(item)
    
    print(f"Found {len(package_dirs)} packages to migrate: {', '.join(package_dirs)}")
    
    # Migrate each package
    success_count = 0
    for package_dir in package_dirs:
        if migrate_package(package_dir):
            success_count += 1
    
    print(f"\n✅ Migration complete! Successfully migrated {success_count}/{len(package_dirs)} packages")
    
    if success_count < len(package_dirs):
        print("\n⚠️  Some packages could not be fully migrated. They will continue to work with git URLs.")
    
    print("\n📝 Next steps:")
    print("1. Review the changes with 'git diff'")
    print("2. Test the migration locally with 'python -m http.server'")
    print("3. Commit and push the changes")


if __name__ == "__main__":
    main()