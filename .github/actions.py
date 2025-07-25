import os
import copy
import re
import shutil
import sys

from bs4 import BeautifulSoup

# Add the .github directory to path to import download_release
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from download_release import download_package_files


INDEX_FILE = "index.html"
TEMPLATE_FILE = "pkg_template.html"
YAML_ACTION_FILES = [".github/workflows/delete.yml", ".github/workflows/update.yml"]
PACKAGES_DIR = "packages"

INDEX_CARD_HTML = '''
<a class="card" href="">
    placeholder_name
    <span>
    </span>
    <span class="version">
        placehholder_version
    </span>
    <br/>
    <span class="description">
        placeholder_description
    </span>
</a>'''


def normalize(name):
    """ From PEP503 : https://www.python.org/dev/peps/pep-0503/ """
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize_version(version):
    version = version.lower()
    return version[1:] if version.startswith("v") else version


def is_stable(version):
    return not ("dev" in version or "a" in version or "b" in version or "rc" in version)


def package_exists(soup, package_name):
    package_ref = package_name + "/"
    for anchor in soup.find_all('a'):
        if anchor['href'] == package_ref:
            return True
    return False


def transform_github_url(input_url):
    # Split the input URL to extract relevant information
    parts = input_url.rstrip('/').split('/')
    username, repo = parts[-2], parts[-1]

    # Create the raw GitHub content URL
    raw_url = f'https://raw.githubusercontent.com/{username}/{repo}/main/README.md'
    return raw_url


def get_package_links(norm_pkg_name, norm_version, version, package_files):
    """
    Generate HTML links for package files.
    
    Returns:
        String containing HTML anchor elements for wheel and/or tar.gz files
    """
    links = []
    base_url = f"../packages/{norm_pkg_name}/"
    
    if package_files.get('wheel'):
        wheel_filename = os.path.basename(package_files['wheel'])
        links.append(f'<a href="{base_url}{wheel_filename}">{norm_version}</a>')
    elif package_files.get('tar_gz'):
        tar_filename = os.path.basename(package_files['tar_gz'])
        links.append(f'<a href="{base_url}{tar_filename}">{norm_version}</a>')
    else:
        # Fallback to git URL (without egg parameter)
        return f'<a href="git+{package_files.get("homepage", "")}@{version}">{norm_version}</a>'
    
    # Return just the first link for single version display
    return links[0] if links else ""


def register(pkg_name, version, author, short_desc, homepage):
    long_desc = transform_github_url(homepage)
    # Read our index first
    with open(INDEX_FILE) as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
    norm_pkg_name = normalize(pkg_name)
    norm_version = normalize_version(version)

    if package_exists(soup, norm_pkg_name):
        raise ValueError(f"Package {norm_pkg_name} seems to already exists")

    # Download package files
    package_output_dir = os.path.join(PACKAGES_DIR, norm_pkg_name)
    print(f"Downloading package files for {pkg_name} v{version}")
    try:
        package_files = download_package_files(
            homepage, version, pkg_name, package_output_dir
        )
    except Exception as e:
        print(f"Warning: Could not download package files: {e}")
        # Continue with git URL fallback
        package_files = {'homepage': homepage}

    # Create a new anchor element for our new package
    placeholder_card = BeautifulSoup(INDEX_CARD_HTML, 'html.parser')
    placeholder_card = placeholder_card.find('a')
    new_package = copy.copy(placeholder_card)
    new_package['href'] = f"{norm_pkg_name}/"
    new_package.contents[0].replace_with(pkg_name)
    spans = new_package.find_all('span')
    spans[1].string = norm_version  # First span contain the version
    spans[2].string = short_desc    # Second span contain the short description

    # Add it to our index and save it
    soup.find('h6', class_='text-header').insert_after(new_package)
    with open(INDEX_FILE, 'wb') as index:
        index.write(soup.prettify("utf-8"))

    # Then get the template, replace the content and write to the right place
    with open(TEMPLATE_FILE) as temp_file:
        template = temp_file.read()

    # Generate package links HTML
    package_links = get_package_links(norm_pkg_name, norm_version, version, package_files)

    template = template.replace("_package_name", pkg_name)
    template = template.replace("_norm_version", norm_version)
    template = template.replace("_version", version)
    template = template.replace("_link", package_links)
    template = template.replace("_homepage", homepage)
    template = template.replace("_author", author)
    template = template.replace("_long_description", long_desc)
    template = template.replace("_latest_main", version)

    os.mkdir(norm_pkg_name)
    package_index = os.path.join(norm_pkg_name, INDEX_FILE)
    with open(package_index, "w") as f:
        f.write(template)


def update(pkg_name, version):
    # Read our index first
    with open(INDEX_FILE) as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
    norm_pkg_name = normalize(pkg_name)
    norm_version = normalize_version(version)

    if not package_exists(soup, norm_pkg_name):
        raise ValueError(f"Package {norm_pkg_name} seems to not exists")

    # Change the version in the main page (only if stable)
    if is_stable(version):
        anchor = soup.find('a', attrs={"href": f"{norm_pkg_name}/"})
        spans = anchor.find_all('span')
        spans[1].string = norm_version
        with open(INDEX_FILE, 'wb') as index:
            index.write(soup.prettify("utf-8"))

    # Change the package page
    index_file = os.path.join(norm_pkg_name, INDEX_FILE) 
    with open(index_file) as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
        
    # Extract the URL from the onclick attribute
    button = soup.find('button', id='repoHomepage')
    if button:
        homepage = button.get("onclick")[len("openLinkInNewTab('"):-2]
    else:
        raise Exception("Homepage URL not found")

    # Download package files for this version
    package_output_dir = os.path.join(PACKAGES_DIR, norm_pkg_name)
    print(f"Downloading package files for {pkg_name} v{version}")
    try:
        package_files = download_package_files(
            homepage, version, pkg_name, package_output_dir
        )
    except Exception as e:
        print(f"Warning: Could not download package files: {e}")
        # Continue with git URL fallback
        package_files = {'homepage': homepage}

    # Create a new div element for our new version
    original_div = soup.find('section', class_='versions').findAll('div')[-1]
    new_div = copy.copy(original_div)
    anchor = new_div.find('a')
    new_div['onclick'] = f"load_readme('{version}', scroll_to_div=true);"
    new_div['id'] = version
    new_div['class'] = ""
    if not is_stable(version):
        new_div['class'] += "prerelease"
    else:
        # replace the latest main version
        main_version_span = soup.find('span', id='latest-main-version')
        main_version_span.string = version
    
    # Clear the anchor and add new links
    anchor.clear()
    anchor.string = norm_version
    
    # Generate package links for this version
    base_url = f"../packages/{norm_pkg_name}/"
    if package_files.get('wheel'):
        wheel_filename = os.path.basename(package_files['wheel'])
        anchor['href'] = f"{base_url}{wheel_filename}"
        anchor['title'] = wheel_filename
    elif package_files.get('tar_gz'):
        tar_filename = os.path.basename(package_files['tar_gz'])
        anchor['href'] = f"{base_url}{tar_filename}"
        anchor['title'] = tar_filename
    else:
        # Fallback to git URL without egg parameter
        anchor['href'] = f"git+{homepage}@{version}"

    # Add it to our index
    original_div.insert_after(new_div)

    # Change the latest version (if stable)
    if is_stable(version):
        soup.html.body.div.section.find_all('span')[1].contents[0].replace_with(version)

    # Save it
    with open(index_file, 'wb') as index:
        index.write(soup.prettify("utf-8"))


def delete(pkg_name):
    # Read our index first
    with open(INDEX_FILE) as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
    norm_pkg_name = normalize(pkg_name)

    if not package_exists(soup, norm_pkg_name):
        raise ValueError(f"Package '{norm_pkg_name}' seems to not exists")

    # Remove the package directory
    shutil.rmtree(norm_pkg_name)
    
    # Remove the package files directory if it exists
    package_files_dir = os.path.join(PACKAGES_DIR, norm_pkg_name)
    if os.path.exists(package_files_dir):
        shutil.rmtree(package_files_dir)

    # Find and remove the anchor corresponding to our package
    anchor = soup.find('a', attrs={"href": f"{norm_pkg_name}/"})
    anchor.extract()
    with open(INDEX_FILE, 'wb') as index:
        index.write(soup.prettify("utf-8"))


def main():
    # Call the right method, with the right arguments
    action = os.environ["PKG_ACTION"]

    if action == "REGISTER":
        register(
            pkg_name=os.environ["PKG_NAME"],
            version=os.environ["PKG_VERSION"],
            author=os.environ["PKG_AUTHOR"],
            short_desc=os.environ["PKG_SHORT_DESC"],
            homepage=os.environ["PKG_HOMEPAGE"],
        )
    elif action == "DELETE":
        delete(
            pkg_name=os.environ["PKG_NAME"]
        )
    elif action == "UPDATE":
        update(
            pkg_name=os.environ["PKG_NAME"],
            version=os.environ["PKG_VERSION"]
        )


if __name__ == "__main__":
    main()
