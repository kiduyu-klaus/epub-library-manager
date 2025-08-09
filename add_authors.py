import csv
import logging
import os
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from googlesearch import search
import bs4  # Optional: if you use `bs4.BeautifulSoup` instead of `from bs4 import BeautifulSoup`
import requests
from bs4 import BeautifulSoup
# Constants
GOODREADS_URL = 'https://www.goodreads.com'
import random
# List of user agents for rotation
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

def get_id_number(author_id):
    pattern = re.compile("([^.-]+)")
    aid = pattern.search(author_id).group()
    author_split = aid.split(".")
    return author_split[0]

def get_author_info(soup):
    container = soup.find('div', attrs={'class': 'rightContainer'})
    author_info = {}
    data_div = container.find('br', attrs={'class': 'clear'})
    while data_div:
        if data_div.name:
            data_class = data_div.get('class')[0]
            if data_class == 'aboutAuthorInfo':
                break
            elif data_class == 'dataTitle':
                key = data_div.text.strip()
                author_info[key] = []
            if data_div.text == 'Born':
                data_div = data_div.next_sibling
                author_info[key].append(data_div.strip())
            elif data_div.text == 'Influences':
                data_div = data_div.next_sibling.next_sibling
                data_items = data_div.findAll('span')[-1].findAll('a')
                for data_a in data_items:
                    author_info[key].append(data_a.text.strip())
            elif data_div.text == 'Member Since':
                data_div = data_div.next_sibling.next_sibling
                author_info[key].append(data_div.text.strip())
            else:
                data_items = data_div.find_all('a')
                for data_a in data_items:
                    author_info[key].append(data_a.text.strip())
        data_div = data_div.next_sibling
    return author_info

def get_author_description(soup, id_number):
    cell = soup.find("span", {"id": f"freeTextContainerauthor{id_number}"})
    return cell.text.strip() if cell else None

def get_author_image(soup, author_name):
    cell = soup.find("img", {"alt": author_name, "itemprop": "image"})
    if cell:
        return cell.attrs.get("src")
    return 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/No-Image-Placeholder.svg/1665px-No-Image-Placeholder.svg.png'

def author_youtube_search(author_name):
    try:
        search_txt = author_name + ' channel youtube'
        results = search(search_txt, num_results=10)
        for url in results:
            if 'https://www.youtube.com' in url:
                return url
    except Exception as e:
        print(f"YouTube search error: {e}")
    return ''

def author_instagram_search(author_name):
    try:
        search_txt = author_name + ' instagram official'
        results = search(search_txt, num_results=10)
        for url in results:
            if 'https://www.instagram.com' in url:
                return url
    except Exception as e:
        print(f"Instagram search error: {e}")
    return ''

def author_facebook_search(author_name):
    try:
        search_txt = author_name + ' facebook official'
        results = search(search_txt, num_results=10)
        for url in results:
            if 'https://www.facebook.com' in url:
                return url
    except Exception as e:
        print(f"Facebook search error: {e}")
    return ''

def author_website_search(author_name):
    try:
        search_txt = author_name + ' official website'
        results = search(search_txt, num_results=10)
        for url in results:
            return url  # First valid hit
    except Exception as e:
        print(f"Website search error: {e}")
    return ''

def scrape_author(author_id):
        """
        Scrapes the author information from the Goodreads website.

        Args:
            author_id (str): The author ID.

        Returns:
            dict: A dictionary containing the scraped author information.
        """
        user_agent = random.choice(LIST_OF_USER_AGENTS)  # Select a random user agent
        random_header = {'User-Agent': user_agent}  # Create a header with the selected user agent

        url = "https://www.goodreads.com/author/show/" + author_id

        time.sleep(3)  # Pause execution for 3 seconds

        try:
            source = requests.get(url, headers=random_header).content  # Open the URL and retrieve the HTML source with the header
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

            author_des = get_author_description(soup, id_number)
            if not author_des:  # Check if author_des is empty (None or empty string)
                author_des = "No Author Description"


            

        except AttributeError as e:
            print(f"An AttributeError occurred while scraping author information: {e}")
            return None
     
        #"id","name","description","image","facebook_url","instagram_url","youtube_url","website_url","status"
        return {
            "id": id_number,
            "name": author_name,
            "description": author_des,
            "image": get_author_image(soup, author_name),
            "facebook_url": author_facebook_search(author_name),
            "instagram_url": author_instagram_search(author_name),
            "youtube_url": author_youtube_search(author_name),
            "website_url": author_website_search(author_name),
            "status": '1'
        }

def is_author_id_in_csv(aid, csv_file= 'authors.csv'):
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
    
def append_author_to_csv(file_name, author_data):
    """
    Appends the scraped author data to a CSV file.

    Args:
        file_name (str): The name of the CSV file.
        author_data (dict): A dictionary containing the scraped author information.
    """
    fieldnames = [
        'id', 'name', 'description', 'image',
        'facebook_url', 'instagram_url', 'youtube_url',
        'website_url', 'status'
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
        
csv_file1 = 'authorsoceanofpdf.csv'
csv_file = csv.reader(open('aid1.csv', "r", encoding='utf-8'), delimiter=",")
next(csv_file)
for row in csv_file:
    try:
        if row:
            a_id = row[0].strip()
            if not is_author_id_in_csv(a_id) and not is_author_id_in_local_csv(a_id, csv_file1):
                print('========> adding author id '+a_id)
                author_data = scrape_author(a_id)  # Scrape author data
                append_author_to_csv('authorsoceanofpdf.csv', author_data)
                print(f"+++++++++> {author_data['name']} added")
                time.sleep(3)
            else:
                print(f"{a_id} is already in the CSV file.")
    except Exception as e:
        print(f"Error processing author ID {a_id}: {e}")
        continue