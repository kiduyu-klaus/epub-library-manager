import requests
from bs4 import BeautifulSoup

# Note: You'll need to install these packages if not already installed:
# pip install requests beautifulsoup4

base_url = 'https://www.goodreads.com'
series_url = 'https://www.goodreads.com/series/41029-in-death'
headers = {
    # Add necessary headers here
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
books = []

print(f"[+] Starting Goodreads scraper for series: {series_url}")
print("[+] Initializing scraping process...")

url = series_url
page_num = 1

while url:
    print(f"\n[+] Processing page {page_num}: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"[+] Successfully fetched page {page_num}")
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        break

    soup = BeautifulSoup(response.text, 'html.parser')

    # Scrape titles and authors
    page_books = []
    for title_tag in soup.find_all('a', class_='gr-h3'):
        title = title_tag.get_text(strip=True)
        author = None
        parent = title_tag.parent
        if parent:
            author_span = parent.find_next('span', itemprop='author')
            if author_span:
                author_link = author_span.find('a')
                if author_link:
                    author = author_link.get_text(strip=True)
                else:
                    author = author_span.get_text(strip=True)
        if title and author:
            page_books.append((title, author))
            books.append((title, author))

    print(f"[+] Found {len(page_books)} books on page {page_num}")

    # Check for next page
    next_button = soup.select_one('div.gr-paginationLinks button.gr-paginationLinks__nextButton')
    if next_button and 'disabled' not in next_button.attrs:
        # The "Next" button is enabled, find the next page URL
        page_num_buttons = soup.select('div.gr-paginationLinks button.gr-paginationLinks__pageNumLink')
        current_page = soup.select_one('div.gr-paginationLinks span.gr-paginationLinks__pageNumLink--selected')
        if current_page:
            current_page_num = current_page.text
            next_page_num = str(int(current_page_num) + 1)
            print(f"[+] Current page: {current_page_num}, Next page: {next_page_num}")

            # The next page URL is usually the same base URL with ?page=next_page_num
            url = series_url + f'?page={next_page_num}'
            page_num += 1
        else:
            print("[+] Could not find current page number, stopping pagination")
            url = None
    else:
        print("[+] No next page button found or next button is disabled")
        url = None

print("
[+] Scraping completed!"    print(f"[+] Total books collected: {len(books)}")

# Print all titles and authors
print("
[+] All books found:"    print("-" * 50)
for i, (title, author) in enumerate(books, 1):
    print(f"{i"2d"}. Title: {title}")
    print(f"    Author: {author}")
    print()
