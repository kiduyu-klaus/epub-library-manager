# Configure Gemini AI with the API key from the environment variable
genai.configure(api_key=Gemini_key)

# Create the model configuration
generation_config = {
    "temperature": 0.7,  # Lower temperature for deterministic responses
    "top_p": 0.95,  # Use nucleus sampling
    "top_k": 40,  # Consider top-k tokens
    "max_output_tokens": 512,  # Limit response length
    "response_mime_type": "text/plain",  # Expect text response
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",  # Use the appropriate model name
    generation_config=generation_config,
)

def get_goodreads_title(book_title, author_name):
    """
    Passes a book title and author to Gemini AI to get the Goodreads official book link.

    Args:
        book_title (str): The title of the book.
        author_name (str): The name of the author.

    Returns:
        str: The Goodreads official book link or an error message.
    """
    # Start a new chat session
    chat_session = model.start_chat(history=[])

    # Construct the input prompt
    prompt = (
        f"Find the official Goodreads title for the book titled '{book_title}' "
        f"written by the author '{author_name}'. Return only the goodreads title."
    )

    # Send the message to the Gemini model
    response = chat_session.send_message(prompt)

    # Extract the text response
    response_text = response.text.strip()
    if response_text.strip().lower() == book_title.strip().lower():
        return None
    return response_text

    # Validate the output (basic validation for Goodreads link)
    #if response_text.startswith("https://www.goodreads.com"):
        #return response_text
    #else:
        #return "Could not retrieve a valid Goodreads link."

def wiki_search(search_term, sentences=5):
    """
    Performs a Wikipedia search and returns a summary for the given search term.
    
    Args:
        search_term (str): The term to search for on Wikipedia.
        sentences (int, optional): The number of sentences to include in the summary. Default is 2.
        
    Returns:
        str: The summary of the Wikipedia page for the search term, or an error message if not found.
    """
    try:
        # Perform the Wikipedia search and get the summary
        result = wikipedia.summary(search_term, sentences=sentences)
        return result
    
    except PageError:
        # Handle case where no page is found for the search term
        return "No Description available."
    
    except DisambiguationError as e:
        # Handle disambiguation errors by suggesting possible options
        return "No Description available."

    except Exception as e:
        # Catch-all for any other potential errors
        return "No Description available."

def get_epub_info(fname):
    """
    Extracts metadata from an EPUB file.

    Args:
        fname (str): The path to the EPUB file.

    Returns:
        dict: A dictionary containing the extracted metadata, including 'title' and 'creator',
              or None if an error occurs.
    """
    ns = {
        # Namespace for the container.xml file
        'n': 'urn:oasis:names:tc:opendocument:xmlns:container',
        'pkg': 'http://www.idpf.org/2007/opf',  # Namespace for the package metadata
        'dc': 'http://purl.org/dc/elements/1.1/'  # Namespace for Dublin Core metadata
    }

    try:
        # Open the EPUB file
        zip = zipfile.ZipFile(fname)

        # Read the content of the container.xml file
        txt = zip.read('META-INF/container.xml')
        tree = etree.fromstring(txt)  # Parse the XML content
        
        # Extract the path of the contents metafile
        cfname = tree.xpath('n:rootfiles/n:rootfile/@full-path', namespaces=ns)[0]

        # Read the contents metafile
        cf = zip.read(cfname)  # Read the contents metafile
        tree = etree.fromstring(cf)  # Parse the XML content

        # Extract the metadata block
        p = tree.xpath('/pkg:package/pkg:metadata', namespaces=ns)[0]

        # Repackage the data
        res = {}  # Initialize a dictionary to store the metadata
        for s in ['title', 'creator']:
            # Extract the text content of each metadata element
            res[s] = p.xpath(f'dc:{s}/text()', namespaces=ns)[0]

        return res  # Return the metadata dictionary
    
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError, IndexError) as e:
        # Handle specific exceptions (e.g., invalid EPUB format, missing metadata)
        print(f"Error reading EPUB file '{fname}': {e}")
        return None
    except Exception as e:
        # Handle other unexpected exceptions
        print(f"An unexpected error occurred: {e}")
        return None

def appendbook_info_to_csv(epub_files_info, csv_file):
    """
    Appends the given list of EPUB files information to a CSV file.

    Args:
        epub_files_info (list of dict or dict): List of dictionaries containing book information or a single dictionary.
        csv_file (str): The path to the CSV file to append the data.

    Returns:
        None
    """
    # Check if a single dictionary is provided and convert it to a list of dictionaries
    if isinstance(epub_files_info, dict):
        epub_files_info = [epub_files_info]
    
    # Create a DataFrame from the provided data
    df = pd.DataFrame(epub_files_info)

    # Append the data to the CSV file
    if os.path.isfile(csv_file):
        # If the file exists, append without writing the header
        df.to_csv(csv_file, mode='a', index=False, header=False)
    else:
        # If the file does not exist, write with header
        df.to_csv(csv_file, mode='w', index=False, header=True)

def book_info(bookname, max_retries=3):
    """
    Retrieves the Goodreads URL for a book based on its name and author by performing a search.
    Retries the request in case of an HTTPError.

    Args:
        bookname (str): The name of the book to search for.
        author_b (str): The author of the book. (This parameter is not used in the current implementation.)
        max_retries (int): The maximum number of times to retry the request in case of an HTTPError.

    Returns:
        str: The URL of the book's Goodreads page, or a message indicating an error.
    
    Raises:
        IndexError: If no matching book is found, causing list index out of range when accessing the first element of `matching`.
    """
    base_url = 'https://www.goodreads.com/search?'
    params = {'q': bookname}
    print('searching for ',bookname)
    search_url = base_url + urllib.parse.urlencode(params)

    attempt = 0
    while attempt < max_retries:
        try:
            # Perform the search
            search_page = urlopen(search_url)
            search_html = search_page.read().decode("utf-8")
            search_soup = BeautifulSoup(search_html, "html.parser")

            # Extract links
            links_with_text = [a['href'] for a in search_soup.find_all('a', href=True) if a.text]

            # Find the first book link
            matching = [s for s in links_with_text if "/book/show/" in s]
            
            if not matching:
                raise IndexError("No matching book found in search results.")
            
            book_name = matching[0].split('?')[0]
            complete_url = "https://www.goodreads.com" + book_name
            print('=====> book found ')
            return complete_url
        
        except HTTPError as e:
            print(f"HTTPError: {e.code} - {e.reason}. Retrying in 5 seconds...")
            time.sleep(5)  # Wait before retrying
            attempt += 1
        
        except IndexError as e:
            print(f"IndexError: {str(e)}")
            return "Error: Book not found."
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return "Error: An unexpected error occurred."

    # Return a message after exhausting retries
    return "Error: Unable to fetch book information after multiple attempts."

def get_unique_aids_and_save(csv_filename, output_filename):
    unique_aids = set()

    # Read the CSV file and collect unique aids
    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            unique_aids.add(row['aid'])  # Add each aid to the set

    # If the output file exists, read existing aids and add them to the set to avoid duplicates
    if os.path.exists(output_filename):
        with open(output_filename, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                unique_aids.add(row['aid'])  # Add existing aids to the set

    # Write (or append) the unique aids to the output file
    with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['aid'])  # Write the header
        for aid in sorted(unique_aids):  # Sorting for better organization
            writer.writerow([aid])

def extract_search_query(url):
    """
    Extracts the search query from a URL.
    
    Args:
        url (str): The URL containing the search query.
    
    Returns:
        str: The extracted search query, or None if no query is found.
    """
    # Parse the URL and extract the query parameters
    parsed_url = urlparse(url)
    
    # Parse the query string into a dictionary
    query_params = parse_qs(parsed_url.query)
    
    # Get the 'q' parameter, which is typically used for search queries
    search_query = query_params.get('q')
    
    # Return the search query if it exists, otherwise return None
    return search_query[0] if search_query else None

def remove_extra_spaces(s):
    """
    Removes extra spaces from the string and ensures only single spaces between words.

    Args:
        s (str): The input string with extra spaces.

    Returns:
        str: The cleaned-up string with extra spaces removed.
    """
    # Split the string into words, automatically removing extra spaces
    words = s.split()
    # Join the words with a single space
    cleaned_string = ' '.join(words)
    return cleaned_string

def clean_url(url):
    """
    Cleans the URL by removing everything after the '?'.

    Args:
        url (str): The input URL to be cleaned.

    Returns:
        str: The cleaned URL with everything after '?' removed.
    """
    # Parse the URL
    parsed_url = urlparse(url)
    # Construct the cleaned URL by using the scheme, netloc, path, and excluding the query and fragment
    cleaned_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    return cleaned_url

def scrape_goodreads_books(url, author_name):
    """
    Scrapes Goodreads books from the provided URL and compares each book's author(s) with the given author name.
    
    Args:
        url (str): The URL of the Goodreads search results page.
        author_name (str): The author name to compare with the book authors.
    
    Returns:
        list: A list of URLs of the books found on the page.
    """
    source = urlopen(url)  # Open the URL and retrieve the HTML source
    soup = BeautifulSoup(source, "html.parser")  # Parse the HTML with BeautifulSoup
    setup_logging('log_filename.log')
    # Find all book containers on the page
    book_containers = soup.find_all('tr', itemtype='http://schema.org/Book')
    
    print(f'Results found: {len(book_containers)}')
    #log(f'Results found: {len(book_containers)}')
    log('log_filename.log', f'Results found: {len(book_containers)}', level=logging.INFO)
    
    # If only one result is found, return its URL immediately
    if len(book_containers) == 1:
        container = book_containers[0]
        title_link = container.find('a', class_='bookTitle').get("href")
        complete_book_url = clean_url(GOODREADS_URL + title_link)
        return [complete_book_url]
    
    # List to store all book URLs
    complete_book_urls = []
    search_query = extract_search_query(url)
    
    print(search_query)
    log('log_filename.log',search_query, level=logging.WARNING)
    
    # Iterate over each book container
    for container in book_containers:
        # Extract book title link and title
        title_link = container.find('a', class_='bookTitle').get("href")
        title = container.find('a', class_='bookTitle').text.strip()
        
        # Extract book author(s)
        author_containers = container.find_all('a', class_='authorName')
        authors = [author.text.strip() for author in author_containers]
        
        #print(authors)
        log('log_filename.log',authors, level=logging.WARNING)
        
        # Check if the given author_name matches any of the extracted authors
        if any(author_name.lower().strip() in remove_extra_spaces(author.lower().strip()) for author in authors):
            # Extract the book rating
            rating = container.find('span', class_='minirating').text.strip()
                
            # Extract the image URL
            image_url_tag = container.find('img', itemprop='image')
            image_url = image_url_tag['src'] if image_url_tag else 'No image available'
                
            # Construct the full book URL
            complete_book_url = clean_url(GOODREADS_URL + title_link)
            
            # Add the complete book URL to the list
            complete_book_urls.append(complete_book_url)
            return complete_book_url
        
        complete_book_url = clean_url(GOODREADS_URL + title_link)
        # Add the complete book URL to the list
        complete_book_urls.append(complete_book_url)
    if complete_book_urls:
    # Return the list of all book URLs
        return complete_book_urls[0]
    else:
        return None

def find_epub_and_cover(start_dir):
    """
    Recursively searches for all EPUB files and JPG files in the specified directory and its subdirectories.
    Checks if there is a JPG file in the same folder as the EPUB files.

    Args:
        start_dir (str): The root directory to start the search from.

    """
    for root, dirs, files in os.walk(start_dir):
        # Loop through all files in the current directory
        for file in files:
            # Check if the file is an EPUB file
            if file.endswith('.epub'):
                new_file_name = file.replace(' ', '_')
                book_url_local = new_file_name
                new_creator_name=''
                # Create the full path of the EPUB file
                epub_path = os.path.join(root, file)
                #print("EPUB Name:", file)
                
                ebook_info= get_epub_info(epub_path)
                ebook_title=ebook_info['title']
                print('----> working on '+ebook_title)
                ebook_name_clean = re.sub(r'\(.*?\)', '', ebook_title)
                if ':' in ebook_name_clean:
                    ebook_name_clean = ebook_name_clean.split(':')[0]
                ebook_creator=ebook_info['creator']
                new_creator_name=ebook_creator
                if ',' in ebook_creator:
                    creator_names= ebook_creator.split(',')
                    first_name=creator_names[1].strip()
                    second_name=creator_names[0].strip()
                    new_creator_name=first_name+' '+second_name
                    print(new_creator_name)
                bookname=ebook_name_clean+' by '+new_creator_name
                
                # URL of the Goodreads page to scrape
                base_url = 'https://www.goodreads.com/search?'
                params = {'q': bookname}

                search_url = base_url + urllib.parse.urlencode(params)
                print(search_url)

                # Call the function to scrape the book data
                ebook_url = scrape_goodreads_books(search_url,new_creator_name.strip())
                
                #ebook_url=book_info(bookname, max_retries=3)
                epub_files_info={
                     'title': ebook_name_clean,
                     'author': new_creator_name,
                     'book_link': ebook_url,
                     'book_url_local': book_url_local
                    
                 }
                appendbook_info_to_csv(epub_files_info,'james_patterson.csv')
                #time.sleep(5)
                #print("EPUB Name: "+ ebook_name_clean+" EPUB Author: "+new_creator_name)
                print('============================> done')
                
def find_ebooks_files(root_dir):
    """
    Recursively searches for all EPUB files in the specified directory and its subdirectories.

    Args:
        root_dir (str): The root directory to start the search from.

    Returns:
        list: A list of full paths of EPUB files with spaces in file names replaced by underscores.
    """
    epub_files = []

    for root, dirs, files in os.walk(root_dir):
        for file in fnmatch.filter(files, '*.epub'):
            # Replace spaces with underscores in the file name
            new_file_name = file
            # Construct the full path with the new file name
            full_path = os.path.join(root, new_file_name)
            epub_files.append(full_path)

    return epub_files            
        
def is_book_in_csv(book_file_url, csv_file):
    """
    Checks if a book with the given file URL is present in the specified CSV file.
    
    Args:
        book_file_url (str): The file URL of the book to search for.
        csv_file (str): The path to the CSV file.
        
    Returns:
        bool: True if the book is found in the CSV file, otherwise False.
    """
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file)
        
        # Check if the 'book_file_url' column contains the specified URL
        if 'book_file_url' in df.columns:
            if book_file_url in df['book_file_url'].values:
                return True
        else:
            print("Error: The CSV file does not contain a 'book_file_url' column.")
            return False
        
    except FileNotFoundError:
        print(f"Error: The file {csv_file} does not exist.")
        return False
    except pd.errors.EmptyDataError:
        print(f"Error: The file {csv_file} is empty.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    
    return False
    
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_url(url):
    """
    Validate if URL is usable and not from excluded domains
    """
    if not url:
        return False
    
    # Check if URL starts with http/https
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Exclude unwanted domains
    excluded_domains = [
        'translate.google.com',
        'webcache.googleusercontent.com',
        'support.google.com',
        'accounts.google.com',
        'policies.google.com'
    ]
    
    for excluded in excluded_domains:
        if excluded in url:
            return False
    
    return True

def extract_domain_safely(url):
    """
    Safely extract domain from URL with error handling
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()  # Normalize to lowercase
    except Exception as e:
        logger.warning(f"Error parsing URL {url}: {e}")
        return None

def do_google_search(query, num_results=10, driver=None, timeout=15):
    """
    Perform Google search and return unique URLs from different domains
    
    Args:
        query (str): Search query
        num_results (int): Number of results to request (default: 10)
        driver: Selenium WebDriver instance
        timeout (int): Timeout in seconds for page load (default: 15)
    
    Returns:
        list: List of unique URLs from different domains
    """
    if not driver:
        raise ValueError("WebDriver instance is required")
    
    if not query or not query.strip():
        logger.error("Query cannot be empty")
        return []
    
    # URL encode the query for safety
    encoded_query = quote(query.strip())
    search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
    
    logger.info(f"Searching for: '{query}' with {num_results} results")
    logger.info(f"Search URL: {search_url}")
    
    try:
        # Navigate to Google search
        driver.get(search_url)
        
        # Wait for search results to load
        WebDriverWait(driver, timeout).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, 'div.yuRUbf a'))
        )
        
        # Add small delay to ensure page is fully loaded
        time.sleep(1)
        
    except TimeoutException:
        logger.error(f"Timeout waiting for search results for query: '{query}'")
        return []
    except WebDriverException as e:
        logger.error(f"WebDriver error during search: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading search page: {e}")
        return []
    
    try:
        # Find all search result links
        links = driver.find_elements(By.CSS_SELECTOR, 'div.yuRUbf a')
        logger.info(f"Found {len(links)} potential search result links")
        
        if not links:
            logger.warning("No search result links found")
            return []
        
        # Extract URLs with validation
        raw_urls = []
        for link in links:
            try:
                href = link.get_attribute("href")
                if is_valid_url(href):
                    raw_urls.append(href)
            except Exception as e:
                logger.warning(f"Error extracting href from link: {e}")
                continue
        
        logger.info(f"Found {len(raw_urls)} valid URLs after filtering")
        
        # Remove duplicates by domain (keep first occurrence)
        unique_domains = set()
        unique_urls = []
        
        for url in raw_urls:
            domain = extract_domain_safely(url)
            if domain and domain not in unique_domains:
                unique_domains.add(domain)
                unique_urls.append(url)
                logger.debug(f"Added URL from domain {domain}: {url}")
        
        logger.info(f"Final result: {len(unique_urls)} unique URLs from different domains")
        
        # Log domains for debugging
        if unique_domains:
            logger.info(f"Domains found: {', '.join(sorted(unique_domains))}")
        
        return unique_urls
        
    except NoSuchElementException:
        logger.error("Search result elements not found on page")
        return []
    except Exception as e:
        logger.error(f"Error extracting URLs from search results: {e}")
        return []

def g_search(text):
    user_agent = random.choice(list_of_user_agents)
    time.sleep(random.uniform(1, 3))
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        urls = do_google_search(text, 5, driver)
        print(f'Found {len(urls)} URLs:')
        for url in urls:
            print(url)
            if url.startswith('https://www.goodreads.com/book/show/') or url.startswith('https://www.goodreads.com/en/book/show'):
                return url
    finally:
        driver.quit()
    
def get_sub_category_id(sub_category_name, csv_file='subcategories.csv'):
    """
    Searches for a subcategory in the CSV file and returns its ID and associated category ID.
    Exits the search once the subcategory is found.

    Args:
        sub_category_name (str): The subcategory name to search for.
        csv_file (str): The path to the CSV file.

    Returns:
        dict: A dictionary with 'sid' and 'cat_id' if found, otherwise None.
    """
    # Normalize the subcategory name
    sub_category_name = sub_category_name.strip().lower()

    try:
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Normalize the subcategory name from the CSV file
                csv_sub_category_name = row['sub_cat_name'].strip().lower()

                if csv_sub_category_name == sub_category_name:
                    return {
                        'sid': int(row['sid']),  # Return the subcategory ID as an integer
                        'cat_id': int(row['cat_id'])  # Return the category ID as an integer
                    }
                #print(f"{sub_category_name} not found in {csv_file}.")
            # Return None if the subcategory is not found
            return None
    except FileNotFoundError:
        print(f"Error: The file {csv_file} does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def process_subcategories(sub_cat_id_string, csv_file='subcategories.csv'):
    """
    Processes the sub_cat_id string from the book data, searches for each subcategory
    in the CSV file, and returns the ID and category ID of the first found subcategory.

    Args:
        sub_cat_id_string (str): Comma-separated string of subcategory names.
        csv_file (str): The path to the CSV file containing subcategories.

    Returns:
        dict: A dictionary with 'sid', 'cat_id', and 'sub_cat_name' of the first found subcategory,
              otherwise creates a new subcategory and returns its information.
    """
    if sub_cat_id_string:
        subcategories = [sub_cat.strip() for sub_cat in sub_cat_id_string.split(',')]
        
        # Skip specific genres if there are more than 2 subcategories including them
        skip_genres = {'fiction', 'mystery', 'romance'}
        filtered_subcategories = []
        
        for genre in skip_genres:
            if genre in (sub.lower() for sub in subcategories):
                count_including_genre = sum(1 for sub in subcategories if sub.lower() != genre)
                if count_including_genre > 1:
                    filtered_subcategories = [sub for sub in subcategories if sub.lower() != genre]
                else:
                    filtered_subcategories = subcategories
            else:
                filtered_subcategories = subcategories
                
        subcategories = filtered_subcategories

        for subcategory in subcategories:
            # Search for the subcategory ID
            subcategory_info = get_sub_category_id(subcategory, csv_file)
            if subcategory_info is not None:
                # Return the first found subcategory with its ID and category ID
                return {
                    'sid': subcategory_info['sid'],
                    'cat_id': subcategory_info['cat_id'],
                    'sub_cat_name': subcategory
                }

        # If no subcategory is found, create a new one
        new_subcategory_name = subcategories[0]  # Choose the first subcategory
        df = pd.read_csv(csv_file)
        
        if not df.empty:
            last_sid = df['sid'].max()
            new_sid = last_sid + 1
        else:
            new_sid = 1
        
        new_subcategory = {
            'sid': new_sid,
            'cat_id': 1,  # Assign a default category ID if needed
            'sub_cat_name': new_subcategory_name,
            'sub_cat_image': new_subcategory_name + '.jpg',
            'status': 1
        }
        
        # Append the new subcategory to the CSV file
        new_df = pd.DataFrame([new_subcategory])
        new_df.to_csv(csv_file, mode='a', index=False, header=False)
        
        return {
            'sid': new_sid,
            'cat_id': 1,
            'sub_cat_name': new_subcategory_name
        }
    
    else:
        return {
            'sid': 1,
            'cat_id': 1,
            'sub_cat_name': 'Default'
        }
    
def get_genre_list(soup):
    """
    Extracts genre information from a BeautifulSoup object representing an HTML page.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML page.

    Returns:
        list: A list of dictionaries representing genres with their corresponding 'sid' and 'found_cat_id'.
    """

    genres = []
    genres_container = soup.find("div", {"data-testid": "genresList"})

    if genres_container:
        genre_links = genres_container.find("ul").find("span").find_all("a")

        for link in genre_links:
            genre = link.find("span").text
            genres.append(genre)
        categories_string = ', '.join(genres)
        return categories_string

    return None

def get_id(bookid):
    """
    Extracts the ID from a book ID.

    Args:
        bookid (str): The book ID.

    Returns:
        str: The extracted ID.

    """
    pattern = re.compile("([^.-]+)")
    bookdd = bookid.split('-')[0]
    bookdd = bookdd.split('.')[0]
    return bookdd

def get_author_description(soup, id_number):
    cell = soup.find("span", {"id": "freeTextContainerauthor" + id_number})
    if cell:
        return cell.text.strip()
    
    return None

def get_author_id(soup):
    """
    Retrieves the author ID from a BeautifulSoup object.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object representing the HTML page.

    Returns:
        str: The author ID.

    """
    # Find the anchor tag with the class "ContributorLink"
    #author_url = soup.find("a", {"class": "ContributorLink"})['href']
    author_url22 = soup.find('a', class_='ContributorLink')
    if author_url22:
        author_url = author_url22['href']
        # Split the author URL by "/" and take the last element as the author ID
        author_id = author_url.split("/")[-1]
        # Split the author ID by "." and take the first element as the final author ID value
        author_id = author_id.split(".")[0]
        # Return the author ID
        return author_id

def get_book_description(soup):
    """
    Retrieves the book description from a BeautifulSoup object.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object representing the HTML page.

    Returns:
        str: The book description.

    """
    # Initialize an empty string for the book description
    bdescription = ''
    try:
        # Check if the book description element exists
        if soup.find("div", {"class": "DetailsLayoutRightParagraph__widthConstrained"}).get_text():
            # Retrieve the book description text
            bdescription = soup.find(
                "div", {"class": "DetailsLayoutRightParagraph__widthConstrained"}).get_text()
            # Return the book description
            return bdescription
    except AttributeError:
        # Return 'No Description available' if there is an AttributeError (element not found)
        return 'No Description available'

    # Return 'No Description available' if the book description is empty
    return 'No Description available'

def get_id_number(author_id):
    """
    Extracts the ID number from an author ID.

    Args:
        author_id (str): The author ID.

    Returns:
        str: The extracted ID number.

    """
    pattern = re.compile("([^.-]+)")
    aid = pattern.search(author_id).group()
    author_split = aid.split(".")
    author_url1 = author_split[0]
    return author_url1

def get_author_image(soup, author_name):
    """
    Extracts the image URL of an author from a BeautifulSoup object.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object representing the HTML page.
        author_name (str): The name of the author used to locate the image.

    Returns:
        str: The URL of the author image if found, or a placeholder image URL otherwise.

    """
    cell = soup.find("img", {"alt": author_name, "itemprop": "image"})
    if cell:
        return cell.attrs.get("src")
    return 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png'

def get_author_info(soup):
    """Get all information from an author (genres, influences, website etc.).
    Args:
        soup (bs4.element.Tag): author page connection.
    Returns:
        dict
    """
    container = soup.find('div', attrs={'class': 'rightContainer'})
    author_info = {}
    data_div = container.find('br', attrs={'class': 'clear'})
    while data_div:
        if data_div.name:
            data_class = data_div.get('class')[0]
            # Information section is finished
            if data_class == 'aboutAuthorInfo':
                break
            # Key elements
            elif data_class == 'dataTitle':
                key = data_div.text.strip()
                author_info[key] = []
            # Born section
            if data_div.text == 'Born':
                data_div = data_div.next_sibling
                author_info[key].append(data_div.strip())
            # Influences section
            elif data_div.text == 'Influences':
                data_div = data_div.next_sibling.next_sibling
                data_items = data_div.findAll('span')[-1].findAll('a')
                for data_a in data_items:
                    author_info[key].append(data_a.text.strip())
            # Member since section
            elif data_div.text == 'Member Since':
                data_div = data_div.next_sibling.next_sibling
                author_info[key].append(data_div.text.strip())
            # Genre, website and other sections
            else:
                data_items = data_div.findAll('a')
                for data_a in data_items:
                    author_info[key].append(data_a.text.strip())
        data_div = data_div.next_sibling
    return author_info

def author_youtube_search(Author_name):
    """
    Search for the author's YouTube channel using the specified author's name.
    
    Args:
        Author_name (str): The author's name.
        
    Returns:
        str: The YouTube channel link if found, or an empty string if not found.
    """
    try:
        # Append the author's name and additional keywords to the search query
        search_txt = Author_name + ' channel youtube'
        
        # Perform the search with a limit of 10 results
        search_results = search(search_txt, num_results=10)
        
        # Look for a YouTube link in the search results
        for result in search_results:
            if 'https://www.youtube.com' in result:
                return result
        
    except HTTPError as e:
        print(f"HTTPError occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # Return an empty string if no YouTube link is found or an error occurred
    return ''

def author_instagram_search(Author_name):
    """
    Search for the author's official Instagram account using the specified author's name.
    
    Args:
        Author_name (str): The author's name.
        
    Returns:
        str: The Instagram account link if found, or an empty string if not found.
    """
    try:
        # Append the author's name and additional keywords to the search query
        search_txt = Author_name + ' instagram official'
        
        # Perform the search with a limit of 10 results
        search_results = search(search_txt, num_results=10)
        
        # Look for an Instagram link in the search results
        for result in search_results:
            if 'https://www.instagram.com' in result:
                return result
    
    except HTTPError as e:
        print(f"HTTPError occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    # Return an empty string if no Instagram link is found or an error occurred
    return ''

def author_facebook_search(Author_name):
    """
    Search for the author's official Facebook page using the specified author's name.
    
    Args:
        Author_name (str): The author's name.
        
    Returns:
        str: The Facebook page link if found, or an empty string if not found.
    """
    try:
        # Append the author's name and additional keywords to the search query
        search_txt = Author_name + ' facebook official'
        
        # Perform the search with a limit of 10 results
        search_results = search(search_txt, num_results=10)
        
        # Look for a Facebook link in the search results
        for result in search_results:
            if 'https://www.facebook.com' in result:
                return result

    except HTTPError as e:
        print(f"HTTPError occurred while searching Facebook: {e}")
    except Exception as e:
        print(f"An error occurred while searching Facebook: {e}")
    
    # Return an empty string if no Facebook link is found or an error occurred
    return ''

def author_website_search(author_name):
    """
    Search for the author's official website using the specified author's name.
    
    Args:
        author_name (str): The author's name.
        
    Returns:
        str: The website link if found, or an empty string if not found.
    """
    try:
        # Append the author's name and additional keywords to the search query
        search_txt = author_name + ' official website'
        
        # Perform the search with a limit of 10 results
        search_results = search(search_txt, num_results=10)
        
        # Return the first valid result
        for result in search_results:
            return result

    except HTTPError as e:
        print(f"HTTPError occurred while searching for the website: {e}")
    except Exception as e:
        print(f"An error occurred while searching for the website: {e}")
    
    # Return an empty string if no website link is found or an error occurred
    return ''

def scrape_author(author_id):
    """
    Scrapes the author information from the Goodreads website.

    Args:
        author_id (str): The author ID.

    Returns:
        dict: A dictionary containing the scraped author information.
    """

    url = "https://www.goodreads.com/author/show/" + author_id

    time.sleep(3)  # Pause execution for 3 seconds

    source = urlopen(url)  # Open the URL and retrieve the HTML source
    soup = BeautifulSoup(source, "html.parser")  # Create a BeautifulSoup object for parsing the HTML

    author_name = soup.find("span", {"itemprop": "name"}).text.strip()  # Extract the author name from the HTML
    id_number = get_id_number(author_id)  # Call a helper function to get the ID number

    author_info = get_author_info(soup)  # Call a helper function to get additional author information
    if author_info:
        if 'Born' in author_info:
            author_city_name = author_info["Born"][0]  # Extract the author's city name if available
        else:
            author_city_name = 'No City Name Found'

        if 'Website' in author_info:
            author_website = author_info["Website"]  # Extract the author's website if available
        else:
            author_website = 'none'
    else:
        author_city_name = 'No City Name Found'
        author_website = 'none'

    #info["author_name"] = author_name  # Add the author name to the 'info' dictionary
    
    author_des= get_author_description(soup, id_number)
     

    return {
        "author_id": id_number,
        "author_name": author_name,
        "author_city_name": author_city_name,
        "author_description": author_des,  # Call a helper function to get the author description
        "author_image": get_author_image(soup, author_name),  # Call a helper function to get the author image
        "author_youtube": author_youtube_search(author_name),  # Call a helper function to search for the author on YouTube
        "author_instagram": author_instagram_search(author_name),  # Call a helper function to search for the author on Instagram
        "author_facebook": author_facebook_search(author_name),  # Call a helper function to search for the author on Facebook
        "author_website": author_website_search(author_name),  # Call a helper function to search for the author's website
        "status": '1',
    }

def get_book_cover(soup):
    """
    Retrieves the book cover image URL from a BeautifulSoup object.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object representing the HTML page.

    Returns:
        str: The URL of the book cover image.

    """
    if soup.find('img', {'class': 'ResponsiveImage'}):
        cover = soup.find('img', {'class': 'ResponsiveImage'})
        return cover.attrs.get('src')
    #if soup.find(id="coverImage"):
        #cover = soup.find(id="coverImage")
       # print(cover)
       # return cover.get('src')  # img.get
    return 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png'

def scrape_book(book_url, book_url_local,random_header):
    """
    Scrapes book information from a Goodreads book URL.

    Args:
        book_url (str): The Goodreads book URL.
        book_url_local (str): The local URL of the book file.

    Returns:
        dict: A dictionary containing the scraped book information.

    """
    
    url = book_url
    source = requests.get(url,headers = random_header)
    #print(source.status_code)
    time.sleep(2)
    soup = bs4.BeautifulSoup(source.content, 'html.parser')
    book_title_element = soup.find('h1', class_='Text Text__title1', attrs={'data-testid': 'bookTitle'})
    book_title =  ' '.join(book_title_element.text.split())
    book_id_beta = book_url.replace('https://www.goodreads.com/book/show/', '')
    book_id_beta1 = book_id_beta.replace(
                'https://www.goodreads.com/en/book/show/', '')
    g_list=get_genre_list(soup)
    #print(g_list)
    category_ids = process_subcategories(g_list)
    sid = category_ids.get('sid')
    cat_id = category_ids.get('cat_id')
    #sid = 41
    #cat_id = 3
    
    return {
                'id': get_id(book_id_beta1),
                'cat_id': cat_id,
                'sub_cat_id': sid,
                'aid': get_author_id(soup),
                'featured': '1',
                'book_title': book_title,
                'book_description': get_book_description(soup),
                'book_cover_img': get_book_cover(soup),
                'book_bg_img': get_book_cover(soup),
                'book_file_type': 'epub',
                'book_file_url': book_url_local,
                'total_rate': soup.find('span', {'data-testid': 'ratingsCount'}).text.strip().replace('\xa0ratings',''),
                'rate_avg': soup.find('div', {'class': 'RatingStatistics__rating'}).text.strip(),
                'book_views': soup.find('span', {'data-testid': 'reviewsCount'}).text.strip().replace('\xa0reviews',''),
                'status': '1'

            }

def append_to_book_csv(book_data, csv_file):
    """
    Appends the book data to the specified CSV file.

    Args:
        book_data (dict): A dictionary containing book details.
        csv_file (str): The path to the CSV file where the data should be appended.
    """
    fieldnames = ['id', 'cat_id', 'sub_cat_id', 'aid', 'featured', 'book_title', 
                  'book_description', 'book_cover_img', 'book_bg_img', 'book_file_type',
                  'book_file_url', 'total_rate', 'rate_avg', 'book_views', 'status']

    # Check if the file exists to write the header only if it's a new file
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write header only if file is empty or does not exist
            if file.tell() == 0:
                writer.writeheader()

            # Write the book data
            writer.writerow(book_data)
            print(f"Appended data for book '{book_data['book_title']}' to {csv_file}.")
    
    except IOError as e:
        print(f"An I/O error occurred: {e}")
        
def append_author_to_csv(file_name, author_data):
    """
    Appends the scraped author data to a CSV file.

    Args:
        file_name (str): The name of the CSV file.
        author_data (dict): A dictionary containing the scraped author information.
    """
    fieldnames = [
        'author_id', 'author_name', 'author_city_name', 'author_description',
        'author_image', 'author_youtube', 'author_instagram', 'author_facebook',
        'author_website', 'status'
    ]

    # Check if the file exists and write header if not
    try:
        with open(file_name, mode='r', newline='', encoding='utf-8') as file:
            pass
    except FileNotFoundError:
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

    # Append author data to the CSV file
    with open(file_name, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writerow(author_data)

def add_spaces_before_capitals(filename):
    """
    Adds spaces before each capital letter in the filename, excluding the file extension.

    Args:
        filename (str): The filename of the ebook, e.g., 'BeyondEverAfter.epub'.

    Returns:
        str: The filename with spaces added before each capital letter, excluding the file extension.
    """
    # Remove the file extension
    base_name = filename.rsplit('.', 1)[0]

    # Add spaces before each capital letter
    spaced_name = re.sub(r'(?<!^)(?<!\s)([A-Z])', r' \1', base_name)

    return spaced_name 

def remove_text_between_parentheses(text):
    # Remove text between parentheses and also any text after the first opening parenthesis
    cleaned_text = re.sub(r'\(.*?\)', '', text)
    # Remove any text after the first opening parenthesis
    cleaned_text = re.sub(r'\(.*', '', cleaned_text)
    return cleaned_text.strip()

def insert_book_data(data):
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='php_web_services'
        )
        cursor = conn.cursor()

        # SQL query to insert data into tbl_books
        sql_query = """
        INSERT INTO tbl_books 
        (id, cat_id, sub_cat_id, aid, featured, book_title, book_description, book_cover_img, 
         book_bg_img, book_file_type, book_file_url, total_rate, rate_avg, book_views, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Data to be inserted (from the returned dictionary)
        values = (
            data['id'], 
            data['cat_id'], 
            data['sub_cat_id'], 
            data['aid'], 
            int(data['featured']), 
            data['book_title'], 
            data['book_description'], 
            data['book_cover_img'], 
            data['book_bg_img'], 
            data['book_file_type'], 
            data['book_file_url'], 
            int(data['total_rate'].replace(',', '')), 
            float(data['rate_avg']), 
            int(data['book_views'].replace(',', '')), 
            int(data['status'])
        )

        # Execute the query and commit the transaction
        cursor.execute(sql_query, values)
        conn.commit()

        print(f"Book '{data['book_title']}' inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def check_and_append_aid(aid, csv_file='aid1.csv'):
    """
    Checks if an author ID exists in the CSV file, and if not, appends it on a new line.
    If the file is empty, adds a header before appending the ID.

    Args:
        aid (str): The author ID to search for.
        csv_file (str): The path to the CSV file (default is 'aid1.csv').

    Returns:
        bool: True if the ID was appended, False if it already existed.
    """
    aid_exists = False
    
    # Check if the file exists and is empty
    file_exists = os.path.exists(csv_file)
    file_empty = os.path.getsize(csv_file) == 0 if file_exists else True

    # Read the CSV and check if the ID exists
    if not file_empty:
        try:
            with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['aid'] == str(aid):
                        aid_exists = True
                        break
        except FileNotFoundError:
            print(f"File {csv_file} not found, creating a new one.")

    # If the ID doesn't exist, append it to the file
    if not aid_exists:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if file_empty:  # Add header if the file is empty or newly created
                writer.writerow(['aid'])
            writer.writerow([aid])  # Append the ID on a new line
        print(f"Appended ID {aid} to {csv_file}.")
        return True
    else:
        print(f"ID {aid} already exists in {csv_file}.")
        return False

def move_and_rename_epub(source_path, destination_directory, new_name):
    """
    Move an EPUB file from the source path to the destination directory and rename it.

    Args:
        source_path (str): The path to the source EPUB file.
        destination_directory (str): The path to the destination directory.
        new_name (str): The new name for the EPUB file (including .epub extension).

    Returns:
        str: The path to the newly moved and renamed EPUB file.
    """
    if not os.path.isfile(source_path):
        print(f"Source file '{source_path}' does not exist.")
        return None

    if not os.path.isdir(destination_directory):
        print(f"Destination directory '{destination_directory}' does not exist.")
        return None

    new_file_path = os.path.join(destination_directory, new_name)

    try:
        shutil.move(source_path, new_file_path)
        print(f"File moved and renamed to '{new_file_path}'.")
        return new_file_path
    except Exception as e:
        print(f"Error moving or renaming file: {e}")
        return None

def process_book_search(book_name, book_url_local, author_name, current_csv, list_of_user_agents, file):
    """
    Process a book search to find and scrape book information from Goodreads.

    Parameters:
    - book_name (str): The name of the book to search for.
    - book_url_local (str): The local URL or filename of the book.
    - author_name (str): The author of the book.
    - current_csv (str): The name of the CSV file to append book information.
    - list_of_user_agents (list): A list of user agent strings for HTTP requests.

    Returns:
    None
    """
    text = book_name + ' goodreads book show'
    result_book_url = g_search(text)
    dest = r'E:\The ToDo Network\Ebook project files\2024 lets do this again\genres\uploads'

    if result_book_url:
        handle_result_book_url(result_book_url, book_name, book_url_local, author_name, current_csv, list_of_user_agents, file, dest)
    else:
        handle_no_result_book_url(book_name, book_url_local, author_name, current_csv, list_of_user_agents, file, dest)

def handle_result_book_url(result_book_url, book_name, book_url_local, author_name, current_csv, list_of_user_agents, file, dest):
    """
    Handle the case where a valid book URL is already found and process it.

    Parameters:
    - result_book_url (str): The URL of the book to scrape.
    - book_name (str): The name of the book.
    - book_url_local (str): The local URL or filename of the book.
    - author_name (str): The name of the book's author.
    - current_csv (str): The CSV file to store book data.
    - list_of_user_agents (list): A list of user agent strings for HTTP requests.
    - file (str): The path to the eBook file being processed.
    - dest (str): The destination directory for moving and renaming the eBook file.

    Returns:
    None
    """
    # Inform the user that the book link has been found
    print('Link for ' + str(book_url_local) + ' found at ' + str(result_book_url))

    # Select a random user agent for the HTTP request to mimic browser behavior
    user_agent = random.choice(list_of_user_agents)
    random_header = {'User-Agent': user_agent}

    try:
        # Scrape book details from the provided URL
        book_info = scrape_book(result_book_url, book_url_local, random_header)

        # Check if the book's ID is already in the database or the current CSV
        if not search_book_id(book_info['id']) and not check_book_id(book_info['id'], current_csv):
            # Append the author ID to a dedicated CSV if it is not already present
            authorid = book_info["aid"]
            check_and_append_aid(authorid, csv_file='aid1.csv')
            
            # Log that the book scraping was successful
            print('Book scraped ----> ' + book_info['id'])

            # Append book details to the main CSV file
            append_to_book_csv(book_info, current_csv)

            # Move the eBook file to the specified destination and rename it
            move_and_rename_epub(file, dest, book_url_local)
            print('=========================> Scraping ' + book_name + ' done')
        else:
            # If the book is already added, skip processing and delete the file
            print(f"{book_info['book_title']} already added.....skipping..")
            os.remove(file)
            print('book deleted')

    except ConnectionError as e:
        # Handle connection errors, particularly issues with HTTPS connections
        if 'HTTPSConnectionPool' in str(e):
            print(f"ConnectionError: HTTPSConnectionPool occurred for {book_name}. Skipping this book.")
            # Save the book details to a failed books log for later review
            save_failed_book(book_name, book_url_local, author_name, file, result_book_url)

    except Exception as e:
        # Handle other exceptions during the scraping process
        print(f"An error occurred while scraping the book {book_name}: {e}")
        # Save the book details to a failed books log for later review
        save_failed_book(book_name, book_url_local, author_name, file, result_book_url)

def split_title_and_author(book_info):
    """
    Splits a book string into the title and author.

    Args:
        book_info (str): A string containing the book title and author in the format 'Title by Author'.

    Returns:
        tuple: A tuple containing the title and author as strings.
    """
    # Split the string by the delimiter " by "
    parts = book_info.rsplit(" by ", 1)  # Use rsplit to ensure the split occurs at the last " by "

    if len(parts) == 2:
        title, author = parts
        return title.strip(), author.strip()
    else:
        raise ValueError("Input string format is incorrect. Expected format: 'Title by Author'.")
      
def handle_no_result_book_url(book_name, book_url_local, author_name, current_csv, list_of_user_agents, file, dest):
    """
    Handle the case where no result book URL is found and attempt to search on Goodreads.

    Parameters:
    - book_name (str): The name of the book to process.
    - book_url_local (str): The local URL or filename of the book.
    - author_name (str): The author of the book.
    - current_csv (str): The name of the CSV file to append book information.
    - list_of_user_agents (list): A list of user agent strings for HTTP requests.
    - file (str): The path to the eBook file being processed.
    - dest (str): The destination directory for moving and renaming the eBook file.

    Returns:
    None
    """
    # Inform the user that the function is attempting a Goodreads search
    print('Trying Goodreads search again')
    
    # Construct the Goodreads search URL with the book name as a query parameter
    base_url = 'https://www.goodreads.com/search?'
    params = {'q': book_name}
    search_url = base_url + urllib.parse.urlencode(params)
    print(search_url)

    # Scrape Goodreads for the book's URL based on the search results and author name
    ebook_url = scrape_goodreads_books(search_url, author_name)
    if ebook_url:
        # If multiple URLs are returned, take the first one
        if isinstance(ebook_url, list):
            ebook_url = ebook_url[0]
        print('Link for ' + str(book_url_local) + ' found at ' + str(ebook_url))

        # Randomly select a user-agent header for the HTTP request
        user_agent = random.choice(list_of_user_agents)
        random_header = {'User-Agent': user_agent}

        try:
            # Scrape detailed book information from the retrieved Goodreads URL
            book_info = scrape_book(ebook_url, book_url_local, random_header)

            # Check if the book's ID is already present in the database or CSV
            if not search_book_id(book_info['id']) and not check_book_id(book_info['id'], current_csv):
                # Handle the author ID: append it to a CSV if it is not already present
                authorid = book_info["aid"]
                check_and_append_aid(authorid, csv_file='aid1.csv')
                
                # Log successful scraping of the book
                print('Book scraped ----> ' + book_info['id'])
                
                # Append the scraped book info to the main CSV
                append_to_book_csv(book_info, current_csv)
                
                # Move and rename the eBook file to the specified destination
                move_and_rename_epub(file, dest, book_url_local)
                print('=========================> Scraping ' + book_name + ' done')
            else:
                # If the book is already in the database, skip and delete the file
                print(f"{book_info['book_title']} already added.....skipping.")
                os.remove(file)
                print('book deleted')
        except ConnectionError as e:
            # Handle connection errors, specifically for HTTPS issues
            if 'HTTPSConnectionPool' in str(e):
                # Uncomment the following line to save failed book data
                # save_failed_book(book_name, book_url_local, author_name, file, result_book_url)
                print(f"{book_url_local} skipped.")
        except Exception as e:
            # Handle generic errors during the scraping process
            print(f"An error occurred while scraping the book {book_name}: {e}")
            # Uncomment the following line to save failed book data
            # save_failed_book(book_name, book_url_local, author_name, file, result_book_url)
    else:
        # If no URL is found on Goodreads, skip processing for this book
        print(f"=====>>>>> {book_name} not found .... trying advanced search.")
        title1, author1 = split_title_and_author(book_name)
        new_book_name=get_goodreads_title(title1, author1)
        if new_book_name:
            new_book_and_author=new_book_name+' by '+author1
            process_book_search(new_book_and_author, book_url_local, author_name, current_csv, list_of_user_agents, file)
                
        else:
           print(f"{book_url_local} skipped.")     
        
def copy_and_rename_epub(source_path, destination_directory, new_name):
    """
    Copy an EPUB file from the source path to the destination directory and rename it.

    Args:
        source_path (str): The path to the source EPUB file.
        destination_directory (str): The path to the destination directory.
        new_name (str): The new name for the EPUB file (including .epub extension).

    Returns:
        str: The path to the newly copied and renamed EPUB file.
    """
    if not os.path.isfile(source_path):
        print(f"Source file '{source_path}' does not exist.")
        return None

    if not os.path.isdir(destination_directory):
        print(f"Destination directory '{destination_directory}' does not exist.")
        return None

    new_file_path = os.path.join(destination_directory, new_name)

    try:
        shutil.copy(source_path, new_file_path)
        print(f"File copied and renamed to '{new_file_path}'.")
        return new_file_path
    except Exception as e:
        print(f"Error copying or renaming file: {e}")
        return None

def search_book_id(book_id,csv_file = 'tbl_books.csv'):
    """
    Search for a specific book ID in the 'tbl_books.csv' file.

    Args:
        csv_file (str): Path to the CSV file containing book data.
        book_id (int or str): The book ID to search for in the CSV file.

    Returns:
        bool: True if the book ID is found, False otherwise.

    Raises:
        FileNotFoundError: If the CSV file cannot be found or opened.

    
    """
    
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Loop through each row in the CSV
            for row in reader:
                # Check if the current row's 'id' matches the given book_id
                if row['id'] == str(book_id):
                    return True  # Return True if the book_id is found
        return False  # Return False if not found
    except FileNotFoundError:
        print(f"Error: The file {csv_file} was not found.")
        return False            

def check_book_id(book_id,csv_file):
    """
    Search for a specific book ID in the 'tbl_books.csv' file.

    Args:
        csv_file (str): Path to the CSV file containing book data.
        book_id (int or str): The book ID to search for in the CSV file.

    Returns:
        bool: True if the book ID is found, False otherwise.

    Raises:
        FileNotFoundError: If the CSV file cannot be found or opened.

    
    """
    
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Loop through each row in the CSV
            for row in reader:
                # Check if the current row's 'id' matches the given book_id
                if row['id'] == str(book_id):
                    return True  # Return True if the book_id is found
        return False  # Return False if not found
    except FileNotFoundError:
        print(f"Error: The file {csv_file} was not found.")
        return False            

def is_author_id_in_csv(aid, csv_file= 'tbl_author.csv'):
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == str(aid):  # Check if the first column matches the author ID
                    return True
        return False
    except FileNotFoundError:
        print(f"File {csv_file} not found.")
        return False

def split_epub_filename(epub_filename):
    """
    Splits an EPUB filename into title and author.
    
    Args:
        epub_filename (str): The EPUB filename.
        
    Returns:
        dict: A dictionary containing the 'title' and 'author' as separate strings.
    """
    # Remove the file extension (.epub)
    filename = os.path.splitext(epub_filename)[0]
    
    # Find the last hyphen to split title and author
    last_hyphen_index = filename.rfind(' - ')
    
    if last_hyphen_index != -1:
        title = filename[:last_hyphen_index].strip()
        author = filename[last_hyphen_index + 3:].strip()  # Skip past the hyphen and spaces
    else:
        # If no hyphen is found, treat the whole filename as the title
        title = filename.strip()
        author = 'Unknown'

    # Remove the author's name from the title if it appears in it
    title_without_author = title.replace(author, '').strip()
    
    pattern = r'\b\d+\s*(?=\w)'

    # Remove any leading character or number before the title
    title_cleaned = re.sub(r'^[^A-Za-z0-9]*(.*)', r'\1', title_without_author).strip()
    title_cleaned1 = re.sub(pattern, '',  title_cleaned).strip()
    title_cleaned2 = re.sub(r'^[\d.]+\s*', '', title_cleaned1).strip()

    return {
        'title': clean_ebook_filename(title_cleaned2),
        'author': author
    }

def clean_ebook_filename(filename):
    """
    Removes specified substrings from an ebook filename.
    
    Args:
        filename (str): The original ebook filename.
        
    Returns:
        str: The cleaned ebook filename.
    """
    # Remove everything between ( and ) including the parentheses
    cleaned_filename = re.sub(r'\s*\(.*?\)\s*', '', filename)
    
    
    cleaned_filename = re.sub(r'^[\d.]+\s*', '', filename)

    # Remove everything after just ( including it
    cleaned_filename = re.sub(r'\s*\(.*', '', cleaned_filename)

    # Remove everything after the first - or _ (including them)
    cleaned_filename = re.sub(r'\s*[-_].*', '', cleaned_filename)

    # Strip any extra spaces
    return cleaned_filename.strip()

def search_folder_by_name(folder_name, root_dir=r'E:\Novels Library\DCIM\Calibre Library'):
    """
    Searches for a folder by name within the specified root directory and returns its path.
    This function only searches in the root directory and not in its subdirectories.

    Args:
        folder_name (str): The name of the folder to search for.
        root_dir (str): The root directory to start the search from.

    Returns:
        str: The full path to the folder if found, otherwise None.
    """
    # List all items in the root directory
    try:
        root_items = os.listdir(root_dir)
    except PermissionError as e:
        print(f"Permission error accessing directory: {root_dir}. {e}")
        return None
    except FileNotFoundError as e:
        #print(f"Directory not found: {root_dir}. {e}")
        return None

    # Check if the folder_name is in the list of directories
    if folder_name in root_items:
        folder_path = os.path.join(root_dir, folder_name)
        if os.path.isdir(folder_path):
            return folder_path
    
    return None  # Return None if the folder is not found

def count_epub_files_in_folder_recursive(folder_path):
    """
    Counts the number of EPUB files in the specified folder and its subdirectories.

    Args:
        folder_path (str): The path to the folder where the EPUB files are located.

    Returns:
        int: The count of EPUB files in the folder and its subdirectories.
    """
    epub_count = 0

    try:
        # Traverse the folder and subdirectories using os.walk
        for root, dirs, files in os.walk(folder_path):
            # Filter for files that end with .epub
            epub_files = [file for file in files if file.lower().endswith('.epub')]
            epub_count += len(epub_files)
    except PermissionError as e:
        print(f"Permission error accessing directory: {folder_path}. {e}")
    except FileNotFoundError as e:
        print(f"Directory not found: {folder_path}. {e}")

    return epub_count

def check_author_name(author_name, csv_file='tbl_author.csv'):
    """
    Search for a specific author name in the 'tbl_author.csv' file.

    Args:
        csv_file (str): Path to the CSV file containing author data.
        author_name (str): The author name to search for in the CSV file.

    Returns:
        bool: True if the author name is found, False otherwise.

    Raises:
        FileNotFoundError: If the CSV file cannot be found or opened.
    """
    
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Loop through each row in the CSV
            for row in reader:
                # Check if the current row's 'author_name' matches the given author_name
                if row['author_name'].strip().lower() == author_name.strip().lower():
                    return True  # Return True if the author_name is found
        return False  # Return False if not found
    except FileNotFoundError:
        print(f"Error: The file {csv_file} was not found.")
        return False 
    
def count_ebooks_by_author(root_folder):
    """
    Scans the root folder and its subfolders organized by author
    to count the number of .epub files for each author.

    Args:
        root_folder (str): The path to the root folder.

    Returns:
        dict: A dictionary where keys are author names and values are counts of .epub files.
    """
    author_ebook_count = {}

    # Iterate over folders in the root directory
    for author_folder in os.listdir(root_folder):
        author_path = os.path.join(root_folder, author_folder)

        # Check if it's a directory
        if os.path.isdir(author_path):
            epub_count = 0

            # Scan all subfolders and files in the author's directory
            for root, _, files in os.walk(author_path):
                # Count .epub files
                epub_count += sum(1 for file in files if file.endswith('.epub'))

            # Store the count with the author's name
            author_ebook_count[author_folder] = epub_count

    return author_ebook_count

def is_author_id_in_local_csv(aid, csv_file):
    """
    Checks if a given author ID exists in the specified CSV file.

    Args:
        aid (int or str): The author ID to search for.
        csv_file (str): The path to the CSV file where the author ID is stored.

    Returns:
        bool: True if the author ID is found in the CSV file, False otherwise.
    """
    try:
        # Open the CSV file in read mode, specifying UTF-8 encoding for compatibility
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)  # Create a CSV reader object to read rows from the file
            for row in reader:
                # Check if the first column matches the provided author ID
                if row[0] == str(aid):  # Convert 'aid' to string for comparison
                    return True  # Return True if a matching author ID is found
        return False  # Return False if the author ID is not found after reading all rows
    except FileNotFoundError:
        # Handle the case where the CSV file does not exist
        print(f"File {csv_file} not found.")
        return False

def check_filename(file_name, csv_file='tbl_books.csv'):
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['book_file_url'] == file_name:
                    return True
        return False
    except FileNotFoundError:
        print(f"The file {csv_file} was not found.")
        return False
    except KeyError:
        print(f"The column 'book_file_url' does not exist in {csv_file}.")
        return False

def count_ebooks_by_author(root_folder):
    """
    Scans the root folder and its subfolders organized by author
    to count the number of .epub files for each author.

    Args:
        root_folder (str): The path to the root folder.

    Returns:
        list: A list of tuples where each tuple contains the author name,
              count of .epub files, and the author's folder path.
    """
    author_ebook_data = []

    # Iterate over folders in the root directory
    for author_folder in os.listdir(root_folder):
        author_path = os.path.join(root_folder, author_folder)

        # Check if it's a directory
        if os.path.isdir(author_path):
            epub_count = 0

            # Scan all subfolders and files in the author's directory
            for root, _, files in os.walk(author_path):
                # Count .epub files
                epub_count += sum(1 for file in files if file.endswith('.epub'))

            # Store the data as a tuple (author name, count, folder path)
            author_ebook_data.append((author_folder, epub_count, author_path))

    return author_ebook_data

def save_to_csv(data, csv_filename):
    """
    Saves the list of author ebook data to a CSV file,
    sorted by the number of books in descending order.

    Args:
        data (list): A list of tuples containing author names, ebook counts, and folder paths.
        csv_filename (str): The name of the CSV file to save the data.
    """
    # Sort the data by ebook count in descending order
    sorted_data = sorted(data, key=lambda x: x[1], reverse=True)

    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Author', 'Ebook Count', 'Folder Path'])  # Header
        for author, count, path in sorted_data:
            writer.writerow([author, count, path])

def get_authors_with_book_count(csv_filename, min_count, max_count):
    """
    Reads the CSV file and returns the folder paths of authors
    whose ebook counts are between the specified range.

    Args:
        csv_filename (str): The path to the CSV file.
        min_count (int): The minimum number of books (inclusive).
        max_count (int): The maximum number of books (inclusive).

    Returns:
        list: A list of folder paths for authors within the specified book count range.
    """
    folder_paths = []

    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Iterate through each row in the CSV file
        for row in reader:
            # Parse the book count as an integer
            book_count = int(row['Ebook Count'])
            
            # Check if the book count is within the specified range
            if min_count <= book_count <= max_count:
                folder_paths.append(row['Folder Path'])

    return folder_paths

def append_csv_data(source_csv):
    """
    Appends all data from source_csv to the predefined target CSV without adding headers.
    
    :param source_csv: Name of the source CSV file in the specified directory.
    """
    base_path = r"E:\The ToDo Network\Ebook project files\2024 lets do this again\genres\books"
    source_csv_path = f"{base_path}\\{source_csv}"  # Full path to the source CSV
    target_csv = f"{base_path}\\combined_csv.csv"   # Full path to the target CSV

    try:
        with open(source_csv_path, mode='r', newline='', encoding='utf-8') as src_file:
            reader = csv.reader(src_file)
            # Skip headers in the source file
            headers = next(reader, None)

            with open(target_csv, mode='a', newline='', encoding='utf-8') as tgt_file:
                writer = csv.writer(tgt_file)
                writer.writerows(reader)  # Append rows from source file

        print(f"Data from {source_csv_path} successfully appended to {target_csv}.")
    except Exception as e:
        print(f"An error occurred: {e}")

def count_books_by_aid(aid_to_check):
    """
    Counts the number of books for a given author ID in the 'tbl_books.csv' dataset.

    Args:
        aid_to_check (str): The author ID to count books for.

    Returns:
        int: The count of books for the given author ID.
    """
    count = 0
    try:
        with open('tbl_books.csv', "r", encoding="utf-8") as books_file:
            books_csv = csv.DictReader(books_file)
            for row in books_csv:
                if row['aid'] == aid_to_check:
                    count += 1
    except IOError as e:
        print(f"An error occurred reading tbl_books.csv: {e}")

    return count

def save_failed_book(book_name, book_url_local, author_name, file, result_book_url):
    failed_books_file = 'failedbooks.csv'
    if not os.path.exists(failed_books_file):
        with open(failed_books_file, mode='w', newline='', encoding='utf-8') as failed_file:
            writer = csv.writer(failed_file)
            writer.writerow(['book_name', 'book_url_local', 'author_name', 'file', 'result_book_url'])  # Write header

    # Save failed book details to failedbooks.csv
    with open(failed_books_file, mode='a', newline='', encoding='utf-8') as failed_file:
        writer = csv.writer(failed_file)
        writer.writerow([book_name, book_url_local, author_name, file, result_book_url])


starts = r'C:\cracks\My_App\epub-library-manager\All_Books'
current_folder = os.path.basename(starts)

# Create the 'books' directory if it doesn't exist
books_folder = os.path.join(os.getcwd(), 'books')
os.makedirs(books_folder, exist_ok=True)

# Set the path for the current CSV file in the 'books' directory
current_csv = os.path.join(books_folder, 'allbooks.csv')

# Create the CSV file if it doesn't exist
if not os.path.exists(current_csv):
    with open(current_csv, mode='w', newline='') as csv_file:
        pass

# Initialize counters
processed_books = 0
skipped_books = 0
already_added_books = 0

# First pass: count total EPUB files
total_epub_files = 0
for root, dirs, files in os.walk(starts):
    for file in files:
        if file.endswith('.epub') or file.endswith('.ePub'):
            total_epub_files += 1

print(f"📚 Found {total_epub_files} EPUB files to process...")
print("=" * 50)

# Initialize current book counter
current_book = 0

# Main EPUB loop
for root, dirs, files in os.walk(starts):
    for file in files:
        if file.endswith('.epub') or file.endswith('.ePub'):
            current_book += 1
            book_url_local = file
            epub_path = os.path.join(root, file)
            book_title, author_name = parse_filename(file)

            if not book_title or not author_name:
                print(f"❌ Ebook {current_book} of {total_epub_files}: Skipping '{file}' due to missing title or author.")
                skipped_books += 1
                continue

            book_url_local = file.replace(' ', '_')
            url_book = "upload\\" + book_url_local
            if not is_book_in_csv(url_book, current_csv):
                bookname = f"{book_title} by {author_name}"
                print(f'📖 Ebook {current_book} of {total_epub_files}: Working on {bookname}')
                
                search_url = GOODREADS_URL + '/search?' + urllib.parse.urlencode({'q': bookname})
                print(f"  🔍 Searching: {search_url} for '{book_title}' by '{author_name}'")

                goodreads_url = scrape_goodreads_books(search_url, author_name, book_title)
                # 🎯 Add genre lookup here
                #genre = get_book_genre_with_gemini(book_title, author_name)
                #print(f"  📚 Genre: {genre}")
                if goodreads_url:
                    headers = {'User-Agent': random.choice(LIST_OF_USER_AGENTS)}
                    book_info,a_name = scrape_book(goodreads_url, book_url_local, headers)
                    # Check if the book's ID is already in the database or the current CSV
                    if not search_book_id(book_info['id']) and not check_book_id(book_info['id'], current_csv):
                        # Append the author ID to a dedicated CSV if it is not already present
                        authorid = book_info["author_ids"]
                        # Check if authorid is a comma-separated list
                        if ',' in authorid:
                            author_ids = authorid.split(',')
                            for author in author_ids:
                                check_and_append_aid(author.strip(), csv_file='aid1.csv')
                            # If author name is unknown, save the first author ID in new_author_id
                            if author_name.lower() == 'unknown':
                                new_author_id = author_ids[0].strip()
                        else:
                            # If it's a single author ID, process it normally
                            check_and_append_aid(authorid.strip(), csv_file='aid1.csv')
                            # If author name is unknown, save the author ID in new_author_id
                            if author_name.lower() == 'unknown':
                                new_author_id = authorid.strip()
                        
                        # Log that the book scraping was successful
                        print('Book scraped ----> ' + book_info['id'])

                        dest = os.path.join('upload', a_name)
                        if not os.path.exists(dest):
                                os.makedirs(dest)
                        
                        # Move the eBook file to the specified destination and rename it
                        new_file_path=move_and_rename_epub(epub_path, dest, book_url_local)
                        book_info['url'] = new_file_path
                        #print('Book file moved to ' + new_file_path)
                        append_to_book_csv(book_info, current_csv)
                        processed_books += 1
                        print(f'✅ Ebook {current_book} of {total_epub_files}: Processing {bookname} completed! (Total processed: {processed_books})')
                    else:
                        # If the book is already added, skip processing and delete the file
                        print(f"🔄 Ebook {current_book} of {total_epub_files}: {book_info['title']} already in database, deleting file...")
                        os.remove(epub_path)
                        already_added_books += 1
                else:                    
                    bookname = f"{book_title} by {author_name}"
                    print(f'+++++++++-> trying {bookname} again')
                    
                    search_query = clean_search_query(book_title, author_name)
                    search_url = GOODREADS_URL + '/search?' + urllib.parse.urlencode({'q': search_query})
                    print(f"  🔍 Advanced Searching: {search_url} for '{book_title}' by '{author_name}'")
                    goodreads_url = scrape_goodreads_books_raw(search_url, author_name, book_title=None)
                    if goodreads_url:
                        headers = {'User-Agent': random.choice(LIST_OF_USER_AGENTS)}
                        book_info,a_name = scrape_book(goodreads_url, book_url_local, headers)
                        # Check if the book's ID is already in the database or the current CSV
                        if not search_book_id(book_info['id']) and not check_book_id(book_info['id'], current_csv):
                            # Append the author ID to a dedicated CSV if it is not already present
                            authorid = book_info["author_ids"]
                            # Check if authorid is a comma-separated list
                            if ',' in authorid:
                                author_ids = authorid.split(',')
                                for author in author_ids:
                                    check_and_append_aid(author.strip(), csv_file='aid1.csv')
                                # If author name is unknown, save the first author ID in new_author_id
                                if author_name.lower() == 'unknown':
                                    new_author_id = author_ids[0].strip()
                            else:
                                # If it's a single author ID, process it normally
                                check_and_append_aid(authorid.strip(), csv_file='aid1.csv')
                                # If author name is unknown, save the author ID in new_author_id
                                if author_name.lower() == 'unknown':
                                    new_author_id = authorid.strip()
                            
                            # Log that the book scraping was successful
                            print('Book scraped ----> ' + book_info['id'])

                            dest = os.path.join('upload', a_name)
                            if not os.path.exists(dest):
                                    os.makedirs(dest)
                            
                            # Move the eBook file to the specified destination and rename it
                            new_file_path=move_and_rename_epub(epub_path, dest, book_url_local)
                            book_info['url'] = new_file_path
                            #print('Book file moved to ' + new_file_path)
                            append_to_book_csv(book_info, current_csv)
                            processed_books += 1
                            print(f'✅ Ebook {current_book} of {total_epub_files}: Processing {bookname} completed! (Total processed: {processed_books})')
                        else:
                            # If the book is already added, skip processing and delete the file
                            print(f"🔄 Ebook {current_book} of {total_epub_files}: {book_info['title']} already in database, deleting file...")
                            os.remove(epub_path)
                            already_added_books += 1
                    else:                        
                        url=simple_google_search(bookname)
                        if url:
                            print(f"Found Goodreads URL via Google search: {url}")
                            goodreads_url = url   
                            headers = {'User-Agent': random.choice(LIST_OF_USER_AGENTS)}
                            book_info,a_name = scrape_book(goodreads_url, book_url_local, headers)
                            # Check if the book's ID is already in the database or the current CSV
                            if not search_book_id(book_info['id']) and not check_book_id(book_info['id'], current_csv):
                                # Append the author ID to a dedicated CSV if it is not already present
                                authorid = book_info["author_ids"]
                                # Check if authorid is a comma-separated list
                                if ',' in authorid:
                                    author_ids = authorid.split(',')
                                    for author in author_ids:
                                        check_and_append_aid(author.strip(), csv_file='aid1.csv')
                                    # If author name is unknown, save the first author ID in new_author_id
                                    if author_name.lower() == 'unknown':
                                        new_author_id = author_ids[0].strip()
                                else:
                                    # If it's a single author ID, process it normally
                                    check_and_append_aid(authorid.strip(), csv_file='aid1.csv')
                                    # If author name is unknown, save the author ID in new_author_id
                                    if author_name.lower() == 'unknown':
                                        new_author_id = authorid.strip()
                                
                                # Log that the book scraping was successful
                                print('Book scraped ----> ' + book_info['id'])

                                dest = os.path.join('upload', a_name)
                                if not os.path.exists(dest):
                                        os.makedirs(dest)
                                
                                # Move the eBook file to the specified destination and rename it
                                new_file_path=move_and_rename_epub(epub_path, dest, book_url_local)
                                book_info['url'] = new_file_path
                                #print('Book file moved to ' + new_file_path)
                                append_to_book_csv(book_info, current_csv)
                                processed_books += 1
                                print(f'✅ Ebook {current_book} of {total_epub_files}: Processing {bookname} completed! (Total processed: {processed_books})')
                            else:
                                # If the book is already added, skip processing and delete the file
                                print(f"🔄 Ebook {current_book} of {total_epub_files}: {book_info['title']} already in database, deleting file...")
                                os.remove(epub_path)
                                already_added_books += 1 
                        else:    
                            print(f"❌ Ebook {current_book} of {total_epub_files}: No Goodreads URL found for '{bookname}'")
                            skipped_books += 1 
            else:
                print(f"📋 Ebook {current_book} of {total_epub_files}: '{file}' already exists in CSV, skipping...")
                already_added_books += 1

# Print final summary
print("\n" + "=" * 60)
print("📊 PROCESSING SUMMARY")
print("=" * 60)
print(f"📚 Total EPUB files found: {total_epub_files}")
print(f"✅ Successfully processed: {processed_books}")
print(f"🔄 Already in database (deleted): {already_added_books}")
print(f"⚠️  Skipped due to missing info: {skipped_books}")
print(f"📈 Success rate: {(processed_books/total_epub_files*100):.1f}%" if total_epub_files > 0 else "📈 Success rate: 0%")
print("=" * 60)

import csv
import ast
import os

def load_combined_map(file_path="combined_map.txt"):
    """Load combined_map dictionary from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        combined_map = ast.literal_eval(content)
    return combined_map


def load_categories(csv_file="categories_filtered.csv"):
    """Load categories.csv into a dictionary {category_name.lower(): id}"""
    categories = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories[row["category_name"].strip().lower()] = int(row["id"])
    return categories


def save_subcategories_from_combined_map(
    combined_map_file="combined_map.txt",
    categories_file="categories_filtered.csv",
    output_file="sub_cat_final.csv"
):
    combined_map = load_combined_map(combined_map_file)
    categories = load_categories(categories_file)

    file_exists = os.path.isfile(output_file)

    # Get last id if file already exists
    start_id = 1
    if file_exists:
        with open(output_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ids = [int(row["id"]) for row in reader if row["id"].isdigit()]
            if ids:
                start_id = max(ids) + 1

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(
                ["id", "cat_id", "sub_category_name", "sub_category_image", "status"]
            )

        for idx, ((main, sub), sub_category_name) in enumerate(combined_map.items(), start=start_id):
            main = main.strip().lower()
            if main not in categories:
                print(f"⚠️ Category '{main}' not found in {categories_file}, skipping...")
                continue

            cat_id = categories[main]

            sub_category_image = sub_category_name.lower().replace(" ", "_") + ".png"

            writer.writerow([idx, cat_id, sub_category_name, sub_category_image, "0"])
            print(f"✅ Added: {sub_category_name} under cat_id={cat_id}")

    print(f"\n🎉 Finished writing subcategories to {output_file}")


# Example usage
if __name__ == "__main__":
    save_subcategories_from_combined_map()


import os
import xml.etree.ElementTree as ET
from collections import Counter



def extract_subjects(base_path=r"D:\Novels Library\download_five_each_author"):
    """
    Recursively search for metadata.opf files and extract <dc:subject> values.
    Prints genres after each file is read, and counts cat_id/sub_id usage.
    """
    subjects_map = {}
    all_subjects = set()
    pair_counter = Counter()  # 🔑 Counter for (cat_id, sub_id)

    for root, dirs, files in os.walk(base_path):
        if "metadata.opf" in files:
            file_path = os.path.join(root, "metadata.opf")
            try:
                tree = ET.parse(file_path)
                root_xml = tree.getroot()

                ns = {"dc": "http://purl.org/dc/elements/1.1/"}
                subjects = [s.text.strip() for s in root_xml.findall(".//dc:subject", ns) if s.text]

                if subjects:
                    subjects_map[file_path] = subjects
                    all_subjects.update(subjects)

                    # 🔑 Pass single genre string if only one subject
                    if len(subjects) == 1:
                        print(f"   ⚠️ Only one genre found, skipping category assignment.")
                        print(f"     Genre: {subjects}")
                        continue
                    else:
                        print(f"   ✅ Found {len(subjects)} genres.")
                        print(f"     Genres: {subjects}")
                        cat_id, sub_id = find_sub_category(subjects)
                        print(f" ==================================================    Mapped to: Category ID {cat_id}, Subcategory ID {sub_id}")

                    # Update counter
                    pair_counter[(cat_id, sub_id)] += 1


            except Exception as e:
                print(f"❌ Failed to parse {file_path}: {e}")

    # Final summary
    # Final summary
    print("\n📌 Final Category → Subcategory counts:")
    for (cat_id, sub_id), count in pair_counter.most_common():
        cursor.execute("""
            SELECT c.category_name, s.sub_category_name
            FROM sub_categories s
            JOIN categories c ON s.cat_id = c.id
            WHERE s.id = %s
        """, (sub_id,))
        row = cursor.fetchone()
        if row:
            print(f"   {row['category_name']} → {row['sub_category_name']} : {count} times")
        else:
            print(f"   (cat_id={cat_id}, sub_id={sub_id}) : {count} times")

    cursor.close()
    conn.close()

    return subjects_map, sorted(all_subjects), pair_counter

base_r = r"D:\Novels Library\download_five_each_author\Kara Lennox"
_, final_genres, _ = extract_subjects()

import ast

def load_combined_map(file_path="combined_map.txt"):
    """
    Load combined_map dictionary from file.
    Returns an empty dict if file does not exist or is invalid.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return ast.literal_eval(content)  # safely convert str -> dict
    except FileNotFoundError:
        print(f"⚠️ {file_path} not found, returning empty dict.")
        return {}
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return {}

# Example usage
combined_map = load_combined_map("combined_map.txt")
print("Loaded combined_map:")
for k, v in combined_map.items():
    print(f"{k} -> {v}")
    

save_subcategories(combined_map, cat_id=5)

combined_map33 = {
    ("young adult", "contemporary"): "Young Adult Contemporary",
    ("young adult", "fantasy"): "Young Adult Fantasy",
    ("young adult", "historical fiction"): "Young Adult Historical Fiction",
    ("young adult", "horror"): "Young Adult Horror",
    ("young adult", "mystery"): "Young Adult Mystery",
    ("young adult", "paranormal"): "Young Adult Paranormal",
    ("young adult", "romance"): "Young Adult Romance",
    ("young adult", "science fiction"): "Young Adult Science Fiction"
}

save_combined_map(combined_map33, file_path=combined_map_file)
save_subcategories(combined_map33, 9,
                               output_file=sub_cat_file)
category_name = "horror"
cat_id = 7
combined_map_file = "combined_map.txt"
sub_cat_file = "sub_cat.csv"


print(f"\n🔍 Processing category: {category_name} (id={cat_id})")

# Build combined map for this category
combined_map = build_genre_combined_map(category_name)

if not combined_map:
    print(f"⚠️ No subcategories found for {category_name}")
    

import os
import ast
import pprint

def search_genre_by_last_subcategory(search_term, csv_file="all_list_genres.csv", ignore=1):
    """
    Search all_list_genres.csv for entries where the last subcategory matches search_term.
    
    - If search_term is a single word: match only the last part.
    - If search_term has multiple words: replace spaces with dashes and match the last N parts.
    
    Args:
        search_term (str): The genre keyword to match.
        csv_file (str): Path to the CSV file.
        ignore (int, optional): Maximum allowed number of '-' in entry.
                                If exceeded, the entry is skipped.

    Returns:
        list: Matching genre entries.
    """
    search_term = search_term.strip().lower()
    search_parts = search_term.split()
    matches = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            genre = row["Genre"].strip()
            if not genre:
                continue

            # Skip if ignore threshold exceeded
            if ignore is not None and genre.count("-") > ignore:
                continue

            parts = genre.lower().split("-")

            # Single-word search → last part only
            if len(search_parts) == 1:
                if parts[-1] == search_term:
                    matches.append(genre)

            # Multi-word search → check last N parts
            else:
                if parts[-len(search_parts):] == search_parts:
                    matches.append(genre)

    return matches



def build_genre_combined_map(search_term, csv_file="all_list_genres.csv", ignore=None):
    """
    Build a mapping of combined categories based on entries ending with search_term.
    Handles both single and multi-word search terms.

    Example:
        - search_term="romance"
          "billionaire-romance" -> ("romance", "billionaire"): "Billionaire Romance"

        - search_term="science fiction"
          "dystopian-science-fiction" -> ("science fiction", "dystopian"): "Dystopian Science Fiction"
    """
    search_term = search_term.strip().lower()
    search_parts = search_term.split()

    # Force ignore = number of words in search_term
    ignore = len(search_parts)

    results = search_genre_by_last_subcategory(search_term, csv_file, ignore)
    combined_map = {}

    for r in results:
        parts = r.lower().split("-")

        if len(search_parts) == 1:
            # Single-word case
            if len(parts) > 1 and parts[-1] == search_parts[0]:
                prefix = " ".join(parts[:-1])
                key = (search_term, prefix)
                label = f"{prefix.title()} {search_term.title()}"
                combined_map[key] = label

        else:
            # Multi-word case, e.g. "science fiction"
            last_n = "-".join(parts[-len(search_parts):])
            if last_n == "-".join(search_parts):
                prefix = " ".join(parts[:-len(search_parts)])
                key = (search_term, prefix)
                label = f"{prefix.title()} {search_term.title()}"
                combined_map[key] = label

    return combined_map





def save_combined_map(combined_map, file_path="combined_map.txt"):
    """
    Save combined_map into a single dictionary in file_path.
    If file exists, merge with existing dictionary instead of appending.
    Each key/value pair is written on a new line for readability.
    """
    existing_map = {}

    # Load existing dictionary if file exists
    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                try:
                    existing_map = ast.literal_eval(content)
                except Exception:
                    print("⚠️ Warning: existing file not valid dictionary, overwriting.")

    # Merge new entries
    existing_map.update(combined_map)

    # Write back as one big dictionary, formatted line by line
    with open(file_path, "w", encoding="utf-8") as f:
        pprint.pprint(existing_map, stream=f, sort_dicts=False, width=120)

    print(f"✅ Saved {len(combined_map)} new entries, total {len(existing_map)} in {file_path}")


def save_subcategories(combined_map, cat_id, output_file="sub_cat.csv"):
    """
    Save combined_map entries into sub_cat.csv with schema:
    "id","cat_id","sub_category_name","sub_category_image","status"

    - Appends if file exists
    - Auto-increments id based on last row
    """
    file_exists = os.path.isfile(output_file)

    # Determine starting id
    start_id = 1
    if file_exists:
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ids = [int(row["id"])
                   for row in reader if row.get("id") and row["id"].isdigit()]
            if ids:
                start_id = max(ids) + 1

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header only if file is new
        if not file_exists:
            writer.writerow(["id", "cat_id", "sub_category_name",
                            "sub_category_image", "status"])

        for idx, (key, sub_category_name) in enumerate(combined_map.items(), start=start_id):
            # Create image filename
            sub_category_image = sub_category_name.lower().replace(" ", "_") + ".png"
            writer.writerow(
                [idx, cat_id, sub_category_name, sub_category_image, "0"])

    print(f"✅ Appended {len(combined_map)} subcategories to {output_file}")
    
    


def process_genre_categories(categories_file="categories.csv",
                       genres_file="all_list_genres.csv",
                       combined_map_file="combined_map.txt",
                       sub_cat_file="sub_cat.csv",
                       ignore=None):
    """
    Loop through categories.csv and:
    - search_genre_by_last_subcategory using category_name
    - build_combined_map
    - save_combined_map
    - save_subcategories

    Args:
        categories_file (str): Path to categories.csv
        genres_file (str): Path to all_list_genres.csv
        combined_map_file (str): Output for combined_map.txt
        sub_cat_file (str): Output for sub_cat.csv
        ignore (int, optional): Max allowed '-' in genre entries
    """
    if not os.path.isfile(categories_file):
        print(f"❌ {categories_file} not found")
        return

    with open(categories_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat_id = row["id"].strip()
            category_name = row["category_name"].strip().lower()

            print(f"\n🔍 Processing category: {category_name} (id={cat_id})")

            # Build combined map for this category
            combined_map = build_genre_combined_map(category_name)

            if not combined_map:
                print(f"⚠️ No subcategories found for {category_name}")
                continue

            # Save combined_map.txt
            save_combined_map(combined_map, file_path=combined_map_file)

            # Save sub_cat.csv
            save_subcategories(combined_map, cat_id,
                               output_file=sub_cat_file)

process_genre_categories(
    categories_file="categories.csv",
    genres_file="all_list_genres.csv",
    combined_map_file="combined_map.txt",
    sub_cat_file="sub_cat.csv",
    ignore=1  # skip entries with more than 1 dash
)

import requests
from bs4 import BeautifulSoup
import csv
import os

BASE_URL = "https://www.goodreads.com"
START_URL = "https://www.goodreads.com/genres/list?utf8=%E2%9C%93&filter=top-level"
CSV_FILE = "all_list_genres_top_level.csv"


def get_list_max_pages(soup):
    """
    Extract the maximum number of pages from pagination element.
    Looks for pagination in leftContainer div and finds the highest page number.
    Returns max page number as int, or 1 if no pagination found.
    """
    try:
        # Find the leftContainer div
        left_container = soup.find("div", class_="leftContainer")
        if not left_container:
            print("[!] Could not find leftContainer div")
            return 1

        # Find the pagination div (has no attributes)
        pagination_div = None
        for div in left_container.find_all("div", recursive=False):
            if not div.attrs:  # no attributes
                pagination_div = div
                break

        if not pagination_div:
            print("[!] Could not find pagination div without attributes")
            return 1

        max_page = 1

        # Check current page (em tag with class "current")
        current_page_elem = pagination_div.find("em", class_="current")
        if current_page_elem:
            try:
                current_page = int(current_page_elem.get_text(strip=True))
                max_page = max(max_page, current_page)
            except ValueError:
                pass

        # Check all page links (a tags with href containing "page=")
        page_links = pagination_div.find_all("a", href=True)
        for link in page_links:
            href = link.get("href", "")
            if "page=" in href:
                try:
                    # Extract page number from URL
                    page_param = href.split("page=")[1]
                    page_num_str = page_param.split("&")[0].split("#")[0]
                    page_num = int(page_num_str)
                    max_page = max(max_page, page_num)
                except (ValueError, IndexError):
                    continue

        print(f"[+] Found max page: {max_page}")
        return max_page

    except Exception as e:
        print(f"[!] Error extracting max pages: {e}")
        return 1


def scrape_goodreads_list(start_url, output_file, max_pages=None):
    """
    Scrapes a paginated Goodreads genre/list page and saves results to CSV.

    Args:
        start_url (str): The starting URL (page 1).
        max_pages (int, optional): Limit number of pages to scrape (for testing).
        output_file (str): CSV file to save results.

    Returns:
        list of dict: Extracted results from all pages.
    """
    results = []
    url = start_url
    page = 1

    while url:
        print(f"📖 Scraping page {page}: {url}")
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"❌ Failed to fetch {url} (status {response.status_code})")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # --- Extract all genre links ---
        for link in soup.select("a[href*='/genres/']"):
            name = link.get_text(strip=True)
            href = BASE_URL + link["href"]
            results.append({"Genre": name, "URL": href})

        # --- Handle pagination ---
        left_container = soup.find("div", class_="leftContainer")
        if not left_container:
            print("⚠️ No leftContainer found.")
            break

        # Pagination <div> inside leftContainer has NO attributes
        pagination_div = None
        for div in left_container.find_all("div", recursive=False):
            if not div.attrs:  # no attributes at all
                pagination_div = div
                break

        if pagination_div:
            next_tag = pagination_div.find("a", class_="next_page")
            if next_tag and "href" in next_tag.attrs:
                next_page = BASE_URL + next_tag["href"]
                url = next_page
                page += 1
            else:
                print("✅ No next page found.")
                break
        else:
            print("⚠️ Pagination div not found.")
            break

        if max_pages and page > max_pages:
            print(f"⏹️ Reached max_pages={max_pages}, stopping.")
            break

    # --- Save to CSV ---
    file_exists = os.path.isfile(output_file)
    with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Genre", "URL"])
        if not file_exists:  # Write header only if file is new
            writer.writeheader()
        writer.writerows(results)

    print(f"✅ Saved {len(results)} genres to {output_file}")
    return results


scrape_goodreads_list(START_URL, output_file=CSV_FILE)

import requests

OX_API_USER = 'king_klau'
OX_API_PASS = 'kiduyuKLAUS1995='
OX_API_URL = 'https://realtime.oxylabs.io/v1/queries'


def oxylabs_search(query, limit=5):
    """Perform search via Oxylabs Realtime API and return list of URLs."""
    try:
        payload = {
            'source': 'google_search',
            'query': query,
            'domain': 'com',
            'locale': 'en-us',
            'parse': True,
            'start_page': 1,
            'pages': 1,
            'limit': limit
        }

        response = requests.post(OX_API_URL, auth=(
            OX_API_USER, OX_API_PASS), json=payload)
        if response.status_code != 200:
            print(f"Oxylabs API Error: {response.json()}")
            return []

        data = response.json()
        urls = []
        if 'results' in data and len(data['results']) > 0:
            content = data['results'][0].get('content', {})
            results = content.get('results', {})
            organic_results = results.get('organic', [])
            for result in organic_results:
                url = result.get('url')
                if url:
                    urls.append(url)
        return urls

    except Exception as e:
        print(f"Oxylabs search error: {e}")
        return []


def author_youtube_search(author_name):
    query = f"{author_name} channel youtube"
    results = oxylabs_search(query)
    fallback = None
    for url in results:
        if "youtube.com" in url:
            clean = url.split("?")[0].split("#")[0].rstrip("/")
            parts = clean.split("/")
            if len(parts) == 4:
                return clean + "/"
            if not fallback:
                fallback = clean + "/"
    return fallback or ""


def author_instagram_search(author_name):
    query = f"{author_name} instagram official"
    results = oxylabs_search(query)
    fallback = None
    for url in results:
        if "instagram.com" in url:
            clean = url.split("?")[0].split("#")[0].rstrip("/")
            parts = clean.split("/")
            if len(parts) == 4:
                return clean + "/"
            if not fallback:
                fallback = clean + "/"
    return fallback or ""


def author_facebook_search(author_name):
    query = f"{author_name} facebook official"
    results = oxylabs_search(query)
    fallback = None
    for url in results:
        if "facebook.com" in url:
            clean = url.split("?")[0].split("#")[0].rstrip("/")
            parts = clean.split("/")
            if len(parts) == 4:
                return clean + "/"
            if not fallback:
                fallback = clean + "/"
    return fallback or ""


def author_website_search(author_name):
    query = f"{author_name} official website"
    results = oxylabs_search(query)
    if results:
        return results[0]
    return ""


# ==== Example usage ====
if __name__ == "__main__":
    author = "Lee Child"
    print("YouTube:", author_youtube_search(author))
    print("Instagram:", author_instagram_search(author))
    print("Facebook:", author_facebook_search(author))
    print("Website:", author_website_search(author))


import mysql.connector

# ==== MySQL Connection (XAMPP) ====
conn = mysql.connector.connect(
    host="localhost",     # XAMPP MySQL host
    user="root",          # XAMPP MySQL username
    password="",          # XAMPP MySQL password (empty by default)
    database="final_klaus_ebooks_library"
)
cursor = conn.cursor(dictionary=True)

# Step 1: Get all authors
cursor.execute("SELECT id, name FROM authors")
authors = cursor.fetchall()

# Step 2: Count books for each author
authors_with_few_books = []

for author in authors:
    author_id = str(author["id"])

    # Find books where this author_id appears in books.author_ids
    query = """
        SELECT COUNT(*) AS book_count 
        FROM books 
        WHERE FIND_IN_SET(%s, author_ids)
    """
    cursor.execute(query, (author_id,))
    result = cursor.fetchone()
    book_count = result["book_count"]

    if book_count < 10:
        authors_with_few_books.append(
            (author["id"], author["name"], book_count))

# Step 3: Print results
print("Authors with fewer than 10 books:\n")
for author_id, name, count in authors_with_few_books:
    print(f"ID: {author_id} | Name: {name} | Books: {count}")

cursor.close()
conn.close()

import csv
import re

def merge_authors1(tbl_author_file="update_authors_final.csv",
                  tbl_author_old_file="tbl_author_old.csv",
                  output_file="updated_authors_final.csv"):
    """
    Merge tbl_author.csv and tbl_author_old.csv into updated_authors_final.csv.
    Rules:
      - Match on id (tbl_author.id → tbl_author_old.author_id)
      - Update info if NULL, empty, or 'No Description available'
      - For URLs, prefer one starting with 'https://www', else non-empty
      - Collapse multiple spaces in names
      - Keep all rows from both files
    """
    
    def clean_name(name: str) -> str:
        return re.sub(r"\s+", " ", name.strip()) if name else name

    def pick_url(url1, url2):
        url1 = url1 or ""
        url2 = url2 or ""
        if url1.startswith("https://www"):
            return url1
        if url2.startswith("https://www"):
            return url2
        return url1 or url2

    # Load tbl_author.csv
    authors1 = {}
    with open(tbl_author_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_id = row["id"]
            row["name"] = clean_name(row["name"])
            authors1[row_id] = row

    # Load tbl_author_old.csv
    authors2 = {}
    with open(tbl_author_old_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_id = row["author_id"]
            row["author_name"] = clean_name(row["author_name"])
            authors2[row_id] = row

    # Merge all unique IDs
    all_ids = set(authors1.keys()) | set(authors2.keys())
    merged = {}

    for aid in all_ids:
        row1 = authors1.get(aid)
        row2 = authors2.get(aid)

        if row1 and row2:
            merged_row = {
                "id": row1["id"],
                "name": row1["name"] or row2["author_name"],
                "info": row1["info"] if row1["info"] not in (None, "", "No Description available") else row2.get("author_description", ""),
                "image": row1["image"] or row2.get("author_image", ""),
                "facebook_url": pick_url(row1.get("facebook_url"), row2.get("author_facebook")),
                "instagram_url": pick_url(row1.get("instagram_url"), row2.get("author_instagram")),
                "youtube_url": pick_url(row1.get("youtube_url"), row2.get("author_youtube")),
                "website_url": pick_url(row1.get("website_url"), row2.get("author_website")),
                "status": row1.get("status") or row2.get("status") or "1"
            }
            merged[aid] = merged_row

        elif row1:
            merged_row = {
                "id": row1["id"],
                "name": row1["name"],
                "info": row1.get("info", ""),
                "image": row1.get("image", ""),
                "facebook_url": row1.get("facebook_url", ""),
                "instagram_url": row1.get("instagram_url", ""),
                "youtube_url": row1.get("youtube_url", ""),
                "website_url": row1.get("website_url", ""),
                "status": row1.get("status", "1")
            }
            merged[aid] = merged_row

        else:  # row2 only
            merged_row = {
                "id": row2["author_id"],
                "name": row2["author_name"],
                "info": row2.get("author_description", ""),
                "image": row2.get("author_image", ""),
                "facebook_url": row2.get("author_facebook", ""),
                "instagram_url": row2.get("author_instagram", ""),
                "youtube_url": row2.get("author_youtube", ""),
                "website_url": row2.get("author_website", ""),
                "status": row2.get("status", "1")
            }
            merged[aid] = merged_row

    # Write merged CSV
    fieldnames = ["id", "name", "info", "image", "facebook_url", "instagram_url", "youtube_url", "website_url", "status"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for aid in sorted(merged.keys(), key=lambda x: int(x)):
            writer.writerow(merged[aid])

    print(f"✅ Merged authors written to {output_file}")

merge_authors1()

import csv

subcat_file = "sub_cat12.csv"
cat_file = "categories.csv"
output_file = "categories_filtered.csv"

# Step 1: Collect all used cat_ids from sub_cat12.csv
used_cat_ids = set()
with open(subcat_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        used_cat_ids.add(row["cat_id"])

# Step 2: Filter categories.csv based on used cat_ids
filtered_rows = []
with open(cat_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        if row["id"] in used_cat_ids:
            filtered_rows.append(row)

# Step 3: Write new categories file
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(filtered_rows)

print(f"✅ Created {output_file} with only used categories.")

book_url="https://www.goodreads.com/book/show/23824599"
book_url_local=''
random_header={
            "User-Agent": random.choice(LIST_OF_USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp",
            "Referer": "https://www.google.com/"
        }

bookd=scrape_book(book_url,book_url_local, random_header)


import csv
import re

def merge_authors(tbl_author_file="tbl_author.csv",
                  authors_final_file="authors_final.csv",
                  output_file="update_authors_final.csv"):
    """
    Merge tbl_author.csv and authors_final.csv into update_authors_final.csv.
    Rules:
      - Match on id
      - Update info if NULL or 'No Description available'
      - For URLs, prefer one starting with 'https://www', else non-empty one
      - Collapse multiple spaces in names into a single space
      - If id only exists in one file, keep that row
    """
    
    def clean_name(name: str) -> str:
        return re.sub(r"\s+", " ", name.strip())

    def pick_url(url1, url2):
        if url1 and url1.startswith("https://www"):
            return url1
        if url2 and url2.startswith("https://www"):
            return url2
        return url1 or url2 or ""

    # Load both files into dicts keyed by id
    tbl_authors = {}
    with open(tbl_author_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["name"] = clean_name(row["name"])
            tbl_authors[row["id"]] = row

    authors_final = {}
    with open(authors_final_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["name"] = clean_name(row["name"])
            authors_final[row["id"]] = row

    # Merge keys from both
    all_ids = set(tbl_authors.keys()) | set(authors_final.keys())
    merged = {}

    for aid in all_ids:
        row1 = tbl_authors.get(aid)
        row2 = authors_final.get(aid)

        if row1 and row2:
            # Merge case
            merged_row = row2.copy()

            # Update info
            if merged_row["info"] in (None, "", "NULL", "No Description available"):
                merged_row["info"] = row1["info"]

            # Update URLs
            for field in ["facebook_url", "instagram_url", "youtube_url", "website_url"]:
                merged_row[field] = pick_url(merged_row.get(field, ""), row1.get(field, ""))

            # Update image if missing
            if not merged_row.get("image") and row1.get("image"):
                merged_row["image"] = row1["image"]

            merged_row["name"] = clean_name(merged_row["name"])
            merged[aid] = merged_row

        elif row1:  # Only in tbl_author.csv
            merged[aid] = row1
        else:       # Only in authors_final.csv
            merged[aid] = row2

    # Write merged file
    fieldnames = ["id", "name", "info", "image", 
                  "facebook_url", "instagram_url", 
                  "youtube_url", "website_url", "status"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for aid in sorted(merged.keys(), key=lambda x: int(x)):
            writer.writerow(merged[aid])

    print(f"✅ Merged authors written to {output_file}")
    
merge_authors()

import csv
import os

CSV_FILE = "goodreads_books.csv"
OUTPUT_FILE = "goodreads_added.csv"

# Step 1: Load existing titles from goodreads_added.csv (if file exists)
already_added = set()
if os.path.isfile(OUTPUT_FILE):
    with open(OUTPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            already_added.add(row["Title"].strip().lower())  # normalize case/spacing

# Step 2: Process goodreads_books.csv
with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row["Title"].strip()
        author = row["Author"].strip()
        link = row["Link"].strip()

        # Skip if title already processed
        if title.lower() in already_added:
            print(f"Skipping (already added): {title} by {author}")
            continue

        print(f"Processing: {title} by {author}: {link}")

        search_query = f"{title} by {author}"
        successful_download = Ocean_of_pdf_search_books_by_Author_in_one(
            search_query,
            first_n_books=1,
            folder_name="goodreads_books"
        )

        if successful_download:
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as out_f:
                writer = csv.DictWriter(out_f, fieldnames=["Title", "Author", "Link"])
                writer.writerow({
                    "Title": title,
                    "Author": author,
                    "Link": link
                })
            already_added.add(title.lower())  # update set immediately



import os

path = r"C:\cracks\My_App\epub-library-manager\upload"

result = []

for name in os.listdir(path):
    folder_path = os.path.join(path, name)
    if os.path.isdir(folder_path):
        # Count only .pdf and .epub files inside the folder (not subfolders)
        count = sum(
            1 for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith((".pdf", ".epub"))
        )
        
        if count < 10:
            result.append(name.replace("_", " "))

for folder in result:
    print(f"Searching for: {folder} books")
    Ocean_of_pdf_search_books_by_Author(search_query=folder,first_n_books=5)






