import os
import time
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote, unquote
import random
from best_download import download_file
BASE_URL = "https://www.ebookhunter.net"

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

def get_random_headers():
    """Return headers with a random user agent"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
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

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def extract_epub_title(soup):
    """Extract the EPUB title from the h2 inside post-single-content div"""
    content_div = soup.find("div", class_="post-single-content")
    if not content_div:
        return None
        
    # Find the h2 tag inside the content div
    h2_tag = content_div.find("h2")
    if h2_tag:
        title_text = h2_tag.get_text(strip=True)
        # Remove " – Free eBooks Download" from the title
        title_text = re.sub(r'\s*–\s*Free\s*eBooks?\s*Download\s*$', '', title_text, flags=re.IGNORECASE)
        return title_text
    
    return None

def get_book_details(book_url, session):
    """Scrape book details and download link(s) from an individual book page."""
    try:
        response = session.get(book_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Failed to retrieve book page {book_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Title - try to get from the h2 in post-single-content first
    epub_title = extract_epub_title(soup)
    if not epub_title:
        # Fall back to the regular title
        title_tag = soup.find("h1", class_="title")
        epub_title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

    # Author
    author_tag = soup.find("span", class_="theauthor")
    author = author_tag.get_text(strip=True) if author_tag else "Unknown Author"

    # Description
    desc_tag = soup.find("div", class_="entry")
    description = desc_tag.get_text(" ", strip=True) if desc_tag else "No description available."

    # Cover Image
    cover_img = None
    img_tag = soup.find("div", class_="post-single-content")
    if img_tag and img_tag.find("img"):
        cover_img = img_tag.find("img").get("src", "")

    # Download links (inside post-single-content)
    content = soup.find("div", class_="post-single-content")
    download_links = []
    if content:
        for a in content.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("//"):
                href = "https:" + href
            # More comprehensive link detection
            if (href.endswith(".epub") or 
                "download" in a.get_text(strip=True).lower() or
                "epub" in a.get_text(strip=True).lower() or
                "download" in href.lower()):
                download_links.append(href)

    return {
        "Title": epub_title,
        "Author": author,
        "Description": description,
        "CoverImage": cover_img,
        "DownloadLinks": download_links,
        "URL": book_url
    }


def download_epub(epub_url, save_dir=".", title="book", author="unknown"):
    """Download an EPUB file into the specified directory with a safe filename and .epub extension."""

    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Sanitize author and title for filesystem safety
    safe_author = "".join(c for c in author if c.isalnum() or c in (" ", "_", "-")).strip()
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip()

    # Build filename and force .epub extension
    filename = f"{safe_author} - {safe_title}".strip()
    if not filename.lower().endswith(".epub"):
        filename += ".epub"

    filepath = os.path.join(save_dir, filename)

    try:
        success = download_file(
            epub_url,
            expected_checksum=None,   # supply SHA256 if available
            local_file=filepath,
            max_retries=3
        )
        if success:
            print(f"✅ EPUB saved to {filepath}")
            return filepath
        else:
            print(f"❌ Failed to download {epub_url}")
            return None
    except Exception as e:
        print(f"[!] Error downloading {epub_url}: {e}")
        return None

def get_link_type(link):
    """Determine the type of download link"""
    if link.endswith('.epub'):
        return 'Direct EPUB'
    elif 'epub' in link.lower():
        return 'EPUB (indirect)'
    elif 'download' in link.lower():
        return 'Download page'
    elif 'cloud' in link.lower():
        return 'Cloud storage'
    elif 'drive.google.com' in link:
        return 'Google Drive'
    elif 'mega.nz' in link:
        return 'MEGA'
    elif 'dropbox.com' in link:
        return 'Dropbox'
    else:
        return 'Unknown'

def search_books(query, max_pages=None, delay=2, auto_download=True, download_dir="downloads"):
    """Search for books and return details (and optionally download EPUBs)."""
    results = []
    seen_links = set()
    
    # Use session for connection pooling
    with requests.Session() as session:
        session.headers.update(get_random_headers())

        # First, get the first page to determine max pages
        first_page_url = f"{BASE_URL}/?s={quote(query)}"
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

        # Process the first page
        books = soup.find_all("article", class_="post-box")
        for book in books:
            title_tag = book.find("h2", class_="title")
            link_tag = title_tag.find("a") if title_tag else None

            if link_tag:
                book_link = link_tag.get("href", "").strip()
                if book_link and book_link not in seen_links:
                    seen_links.add(book_link)
                    print(f"    [+] Fetching book details: {book_link}")

                    details = get_book_details(book_link, session)
                    if details:
                        results.append(details)

                        # Auto download EPUB (first link only)
                        if auto_download and details["DownloadLinks"]:
                            download_epub(
                                details["DownloadLinks"][0], 
                                download_dir,
                                details["Title"],
                                details["Author"]
                            )
                            
                    # Add variable delay to avoid detection
                    time.sleep(delay * random.uniform(0.8, 1.2))

        # Process remaining pages if needed
        for page in range(2, max_pages + 1):
            search_url = f"{BASE_URL}/page/{page}/?s={quote(query)}"
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

                if link_tag:
                    book_link = link_tag.get("href", "").strip()
                    if book_link and book_link not in seen_links:
                        seen_links.add(book_link)
                        print(f"    [+] Fetching book details: {book_link}")

                        details = get_book_details(book_link, session)
                        if details:
                            results.append(details)

                            # Auto download EPUB (first link only)
                            if auto_download and details["DownloadLinks"]:
                                download_epub(
                                    details["DownloadLinks"][0], 
                                    download_dir,
                                    details["Title"],
                                    details["Author"]
                                )
                        # Add variable delay to avoid detection
                        time.sleep(delay * random.uniform(0.8, 1.2))

            # Randomize delay between pages
            time.sleep(delay * random.uniform(1, 2))

    return results

# === Example Usage ===
if __name__ == "__main__":
    # Create download directory
    download_dir = "downloaded_books"
    os.makedirs(download_dir, exist_ok=True)
    
    # Search with automatic page detection
    books = search_books(
        "Amber Lynn Natusch", 
        max_pages=1,
        auto_download=True,
        download_dir=download_dir
    )
    
    print(f"\n{'='*50}")
    print(f"Found {len(books)} books:")
    
    for i, b in enumerate(books, 1):
        print(f"\n{i}. 📖 {b['Title']} - {b['Author']}")
        print(f"   📄 Description: {b['Description'][:100]}...")
        print(f"   🖼️  Cover: {b['CoverImage']}")
        print(f"   🔗 Download Links ({len(b['DownloadLinks'])} found):")
        
        # Display each download link with type information
        for j, link in enumerate(b['DownloadLinks'], 1):
            link_type = get_link_type(link)
            print(f"      {j}. [{link_type}] {link}")
            
        print(f"   🌐 URL: {b['URL']}")
