import requests
import os
import re
from tqdm import tqdm


import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote, urlparse,parse_qs

import random
from urllib.parse import quote_plus

BASE_URL = "https://www.ebookhunter.net"

# List of user agents to rotate
LIST_OF_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]

def has_key(link):
    """
    Checks if a link contains a valid key/ID.
    
    Args:
        link (str): The link to check
    
    Returns:
        bool: True if the link has a key, False otherwise
    """
    try:
        # Parse the URL
        parsed_url = urlparse(link)
        
        # Check if it's empty or invalid
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        
        # Extract query parameters
        query = parsed_url.query
        
        # Check for the specific format: ?=KEY
        if query.startswith('='):
            key = query[1:]  # Remove the '=' prefix
            return len(key.strip()) > 0
        
        # Check for standard query parameters
        query_params = parse_qs(query)
        
        # Look for common key parameter names
        key_params = ['id', 'key', 'file', 'download', 'd']
        
        for param in key_params:
            if param in query_params:
                values = query_params[param]
                if values and len(values[0].strip()) > 0:
                    return True
        
        # Look for any parameter value that looks like an ID (long alphanumeric string)
        for param_values in query_params.values():
            for value in param_values:
                if re.match(r'^[A-Za-z0-9_-]{15,}$', value.strip()):
                    return True
        
        return False
        
    except Exception:
        return False


def is_download_link_accessible(url, timeout=10):
    """
    Simple check if a download link is accessible.
    
    Args:
        url (str): The URL to check
        timeout (int): Request timeout in seconds
    
    Returns:
        bool: True if link is accessible (status 200-299), False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return 200 <= response.status_code < 300
    except:
        return False

def get_random_headers():
    """Return headers with a random user agent"""
    return {
        "User-Agent": random.choice(LIST_OF_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def get_max_pages(soup):
    """Extract the maximum number of pages from pagination"""
    nav_links = soup.find("div", class_="nav-links")
    if not nav_links:
        return 1  # Only one page if no pagination found
    
    page_numbers = []
    # Find all page number links
    for link in nav_links.find_all("a", class_="page-numbers"):
        try:
            # Extract page number from URL
            href = link.get("href", "")
            if "/page/" in href:
                page_num = int(re.search(r"/page/(\d+)/", href).group(1))
                page_numbers.append(page_num)
        except (AttributeError, ValueError):
            continue
    
    # Also check for the current page
    current_page = nav_links.find("span", class_="page-numbers current")
    if current_page:
        try:
            page_num = int(current_page.get_text(strip=True))
            page_numbers.append(page_num)
        except ValueError:
            pass
    
    return max(page_numbers) if page_numbers else 1


def extract_epub_title(soup):
    """Extract the EPUB title from the h2 inside post-single-content div"""
    content_div = soup.find("div", class_="post-single-content")
    if not content_div:
        return None, None  # return (title, author)

    # Find the h2 tag inside the content div
    h2_tag = content_div.find("h2")
    if h2_tag:
        title_text = h2_tag.get_text(strip=True)

        # Remove " – Free eBooks Download" from the title
        title_text = re.sub(r'\s*–\s*Free\s*eBooks?\s*Download\s*$', '', title_text, flags=re.IGNORECASE)

        # Remove parentheses and anything inside them
        title_text = re.sub(r'\s*\([^)]*\)', '', title_text)

        # Clean up whitespace
        title_text = title_text.strip()

        # Try to split into title and author
        author = None
        match = re.split(r'\s+[bB][yY]\s+', title_text, maxsplit=1)
        if len(match) == 2:
            # Second part is author
            author = match[1].strip()

        return title_text, author

    return None, None

def get_book_details(book_url, session, max_retries=2):
    """Scrape book details and download link(s) from an individual book page."""
    try:
        response = session.get(book_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Failed to retrieve book page {book_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Title + Author (from h2 if possible)
    epub_title, author = extract_epub_title(soup)

    if not epub_title:
        # Fall back to <h1 class="title">
        title_tag = soup.find("h1", class_="title")
        epub_title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

    print(f"    📖 Title: {epub_title}")
    print(f"    ✍️ Author: {author}")

    # Look for links
    content = soup.find("div", class_="post-single-content")
    if not content:
        print("    ❌ No download section found.")
        return None

    success = None  # track download result

    for a in content.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("//"):
            href = "https:" + href

        print(f"    🔗 Found link: {href}")

        if not is_download_link_accessible(href):
            print(f"    ❌ Link {href} is not valid.")
            continue

        if not has_key(href):
            print(f"    ❌ Link {href} missing key/ID.")
            continue

        # Try resolving → downloading with retries
        for attempt in range(1, max_retries + 1):
            try:
                final_link = convert_to_final_link(href)
                print(f"    🔗 Converted to final link: {final_link}")

                success = downld_epub(final_link, filename=epub_title, extension="epub")
                if success:
                    print("    ✅ Download successful!")
                    break   # ✅ break out of retry loop
                else:
                    print(f"    ⚠️ Download failed (attempt {attempt}). Retrying...")
                    time.sleep(5)
            except Exception as e:
                print(f"    ❌ Failed to convert/download: {e}")
                time.sleep(5)

        if success:
            break   # ✅ break outer loop after first successful download

    if success:
        return success

    print("    ❌ No valid links succeeded.")
    return None


def convert_to_final_link(found_link):
    """
    Converts a found link to a Google Drive direct download link.
    
    Args:
        found_link (str): The original link in format: 
                         https://theebookhunter.com/d?=KEY
    
    Returns:
        str: The final Google Drive download link in format:
             https://drive.usercontent.google.com/download?id=KEY&export=download&authuser=0
    """
    try:
        # Parse the URL
        parsed_url = urlparse(found_link)
        
        # Extract the key from the query parameter
        # The key is after the '=' in the query string
        query = parsed_url.query
        if query.startswith('='):
            key = query[1:]  # Remove the '=' prefix
        else:
            # Fallback: try to extract from query parameters
            query_params = parse_qs(query)
            # Look for any parameter value that looks like a Google Drive ID
            key = None
            for param_values in query_params.values():
                for value in param_values:
                    if len(value) > 20:  # Google Drive IDs are typically long
                        key = value
                        break
                if key:
                    break
            
            if not key:
                raise ValueError("Could not extract key from the found link")
        
        # Construct the final Google Drive download link
        final_link = f"https://drive.usercontent.google.com/download?id={key}&export=download&authuser=0"
        
        return final_link
        
    except Exception as e:
        raise ValueError(f"Error processing link: {str(e)}")

def downld_epub(epub_link, filename=None, extension="epub"):
    """
    Download an EPUB file with progress bar.
    - Uses Content-Disposition filename if available
    - Falls back to URL name
    - Falls back to supplied filename + extension
    """
    try:
        download_dir = r"download_dir"
        os.makedirs(download_dir, exist_ok=True)
        with requests.Session() as session:
            with session.get(epub_link,stream=True, timeout=30) as response:
                time.sleep(3)  # Add delay between requests
                response.raise_for_status()

                detected_name, detected_ext = None, extension
                # headers printing
                # print("\n=== Response Headers ===")
                # for k, v in response.headers.items():
                #     print(f"{k}: {v}")
                # print("========================\n")

                # 1. Try Content-Disposition
                cd = response.headers.get("content-disposition")
                if cd:
                    match = re.findall('filename="?([^"]+)"?', cd)
                    if match:
                        detected_name, detected_ext = os.path.splitext(match[0])
                        detected_ext = detected_ext.lstrip(".") or extension

                # 2. Try from URL
                if not detected_name:
                    url_part = os.path.basename(epub_link.split("?")[0])
                    if url_part:
                        detected_name, url_ext = os.path.splitext(url_part)
                        detected_ext = url_ext.lstrip(".") or extension

                # 3. Fall back to supplied
                if not detected_name:
                    detected_name = filename or "downloaded_book"
                    
                final_filename = f"{detected_name}.{detected_ext}"
                    
                if final_filename.lower() == "d.epub":
                    print("❌ Skipping download: detected filename is 'd.epub' (invalid).")
                    return None

                # Final save path
                #filepath = os.path.join(download_dir, filename)
                save_path = os.path.join(download_dir, f"{detected_name}.{detected_ext}")
                
                if os.path.exists(save_path):
                    print(f"⏭️  File already exists: {save_path}")
                    return save_path

                total_size = int(response.headers.get("content-length", 0))
                with open(save_path, "wb") as file, tqdm(
                    desc=detected_name,
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                            bar.update(len(chunk))

        print(f"✅ Download complete: {save_path}")
        return save_path

    except requests.RequestException as e:
        print(f"❌ Download failed: {e}")
        return None

modify to load from https://www.ebookhunter.net/category/dark/page/2/ to max_pages

def search_books(query, max_pages=None, delay=2, auto_download=True, download_dir="downloads"):
    """Search for books and return details (and optionally download EPUBs)."""
    results = []
    seen_links = set()
    
    # Use session for connection pooling
    with requests.Session() as session:
        session.headers.update(get_random_headers())

        # First, get the first page to determine max pages
        first_page_url = f"{BASE_URL}/?s={quote_plus(query)}"
        print(f"[*] Checking first page: {first_page_url}")
        
        try:
            response = session.get(first_page_url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to retrieve first page: {e}")
            return results

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Determine max pages if not specified
        if max_pages is None:
            max_pages = get_max_pages(soup)
            print(f"[*] Found {max_pages} pages of results")
        else:
            print(f"[*] Limiting to {max_pages} pages")

        # Process remaining pages if needed
        for page in range(1, max_pages + 1):
        #for page in range(1, 1 + 1):
            search_url = f"{BASE_URL}/page/{page}/?s={quote_plus(query)}"
            #search_url = f"{BASE_URL}/page/{page}"
            print(f"\n[*] Scraping search page {page}: {search_url}")

            try:
                response = session.get(search_url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"[!] Failed to retrieve search page {page}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            books = soup.find_all("article", class_="post-box")

            if not books:
                print("[!] No more results found.")
                break

            for book in books:
                title_tag = book.find("h2", class_="title")
                link_tag = title_tag.find("a") if title_tag else None
                epub_title_author = title_tag.get_text(strip=True)
                author = None
                match = re.split(r'\s+[bB][yY]\s+', epub_title_author, maxsplit=1)
                if len(match) == 2:
                    # Second part is author
                    author = match[1].replace(" (ePUB)", "").strip()
                if author:
                    author= author.replace(" (ePUB, PDF, Downloads)", "").strip()
                    print(f"    ✍️ Author: {author}")
                    if query.lower().strip() != author.lower().strip():
                        print(f"    ❌ Author '{author}' does not match search query '{query}'. Skipping.")
                        continue
                    else:
                        if link_tag:
                            book_link = link_tag.get("href", "").strip()
                            if book_link and book_link not in seen_links:
                                seen_links.add(book_link)
                                print(f"    [+] Fetching book details: {book_link}")

                                get_book_details(book_link, session)
                                
                                # Add variable delay to avoid detection
                                time.sleep(delay * random.uniform(0.8, 1.2))
                  
            # Randomize delay between pages
            time.sleep(delay * random.uniform(1, 2))

    return results

def scrape_books(base_link, max_pages=1, delay=2, auto_download=True, download_dir="downloads"):
    """
    Scrape books starting from a given link (category or search) up to max_pages.
    
    Example:
        scrape_books("https://www.ebookhunter.net/category/dark/page/1/", max_pages=5)
        scrape_books("https://www.ebookhunter.net/?s=romance", max_pages=3)
    """
    results = []
    seen_links = set()

    with requests.Session() as session:
        session.headers.update(get_random_headers())

        for page in range(1, max_pages + 1):
            # Adjust URL depending on whether link already has "/page/"
            if "/page/" in base_link:
                # Replace the page number
                page_url = re.sub(r"/page/\d+/", f"/page/{page}/", base_link)
            else:
                # Append ?s=... or /category/... with /page/x/
                if "?" in base_link:  # search query
                    page_url = f"{BASE_URL}/page/{page}/{base_link.split(BASE_URL)[-1]}"
                else:  # category
                    page_url = base_link.rstrip("/") + f"/page/{page}/"

            print(f"\n[*] Scraping page {page}: {page_url}")

            try:
                response = session.get(page_url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"[!] Failed to retrieve page {page}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            books = soup.find_all("article", class_="post-box")

            if not books:
                print("[!] No more results found.")
                break

            for book in books:
                title_tag = book.find("h2", class_="title")
                link_tag = title_tag.find("a") if title_tag else None
                epub_title_author = title_tag.get_text(strip=True) if title_tag else None

                if not link_tag or not epub_title_author:
                    continue

                author = None
                match = re.split(r'\s+[bB][yY]\s+', epub_title_author, maxsplit=1)
                if len(match) == 2:
                    author = match[1].replace(" (ePUB)", "").strip()
                    author = author.replace(" (ePUB, PDF, Downloads)", "").strip()

                book_link = link_tag.get("href", "").strip()
                if book_link and book_link not in seen_links:
                    seen_links.add(book_link)
                    print(f"    [+] Fetching book details: {book_link}")
                    get_book_details(book_link, session)

                    # Add variable delay to avoid detection
                    time.sleep(delay * random.uniform(0.8, 1.2))

            # Random delay between pages
            time.sleep(delay * random.uniform(1, 2))

    return results

# === Example Usage ===
if __name__ == "__main__":
    # Create download directory
    download_dir = "downloaded_books"
    os.makedirs(download_dir, exist_ok=True)
    
    # Search with automatic page detection

    search_books("Layla Silver",max_pages=2, auto_download=False, download_dir=download_dir)

