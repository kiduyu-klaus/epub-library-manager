def scrape_goodreads_books_raw(url, author_name, book_title=None):
    try:
        print(f"🔍 Scraping Goodreads raw for: {book_title} by {author_name} from {url}")
        headers = {
            "User-Agent": random.choice(LIST_OF_USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp",
            "Referer": "https://www.google.com/"
        }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response:
            source = response.read()

        soup = BeautifulSoup(source, "html.parser")
        book_containers = soup.find_all(
            'tr', itemtype='http://schema.org/Book')

        if not book_containers:
            book_containers = soup.find_all(
                'tr', {'itemtype': 'http://schema.org/Book'})
        if not book_containers:
            return None

        book_matches = []
        search_query = extract_search_query(url)
        search_title = book_title if book_title else search_query

        for container in book_containers:
            try:
                title_element = container.find('a', class_='bookTitle')
                if not title_element:
                    continue
                title_link = title_element.get("href")
                raw_title = title_element.text.strip()
                if not title_link:
                    continue

                cleaned_title = remove_parentheses_content(raw_title)
                authors = [a.text.strip()
                           for a in container.find_all('a', class_='authorName')]
                complete_book_url = clean_url(GOODREADS_URL + title_link)
                author_match = is_author_match(author_name, authors)
                title_similarity = calculate_similarity_score(
                    search_title, raw_title)
                score = 0.7 * (1.0 if author_match else 0.0) + \
                    0.3 * title_similarity

                # --- Extract rating info ---
                rating_span = container.find('span', class_='minirating')
                avg_rating, total_ratings = 0.0, 0
                if rating_span:
                    try:
                        rating_text = rating_span.text.strip()
                        avg_rating_match = re.search(
                            r'([\d.]+) avg rating', rating_text)
                        total_ratings_match = re.search(
                            r'— ([\d,]+) ratings', rating_text)
                        if avg_rating_match:
                            avg_rating = float(avg_rating_match.group(1))
                        if total_ratings_match:
                            total_ratings = int(
                                total_ratings_match.group(1).replace(',', ''))
                    except Exception:
                        pass

                book_matches.append({
                    'title': raw_title,
                    'cleaned_title': cleaned_title,
                    'authors': authors,
                    'url': complete_book_url,
                    'author_match': author_match,
                    'title_similarity': title_similarity,
                    'score': score,
                    'avg_rating': avg_rating,
                    'total_ratings': total_ratings
                })

            except Exception as e:
                print(f"Error processing container: {e}")

        # --- Sort first by score, then by avg_rating, then total_ratings ---
        book_matches.sort(key=lambda x: (
            x['score'], x['avg_rating'], x['total_ratings']), reverse=True)

        # --- Pick the best valid match ---
        for match in book_matches:
            if match['avg_rating'] > 0 and match['total_ratings'] >= 30:
                print(
                    f"✅ Best valid match: '{match['title']}' | Avg Rating: {match['avg_rating']} | Total Ratings: {match['total_ratings']}")
                return match['url']

        # If only one book is available, return it regardless of ratings
        if len(book_matches) == 1:
            match = book_matches[0]
            print(
                f"✅ Only one match available: '{match['title']}' | Avg Rating: {match.get('avg_rating', 0)} | Total Ratings: {match.get('total_ratings', 0)}")
            return match['url']

        return None

    except Exception as e:
        print(f"Error scraping Goodreads books: {e}")
        return None

task:
    Sort first by total_ratings and pick the one with highest total_ratings.
    