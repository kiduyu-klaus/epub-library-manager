if pdf is more than 10mb but epub is less than, return the epub form , check the filename_input: 
    
def get_download_forms(book_url, scraper):
    """
    Fetch all download form details (id, filename) from a book page.
    Returns only EPUB forms if available, otherwise returns other formats.
    Skips forms if EPUB or PDF size > 10 MB.
    """
    try:
        response = scraper.get(book_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Failed to fetch {book_url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")

    # --- Extract file sizes ---
    def extract_size_in_mb(size_text):
        """
        Extract file size in MB from text like "24 MB" or "1.5 GB".
        Returns size in MB as float, or None if cannot parse.
        """
        import re
        
        # Clean the text and look for size patterns
        size_text = size_text.strip().upper()
        
        # Match patterns like "24 MB", "1.5 GB", "500 KB", etc.
        match = re.search(r'(\d+\.?\d*)\s*(MB|GB|KB)', size_text)
        
        if not match:
            return None
        
        size_value = float(match.group(1))
        unit = match.group(2)
        
        # Convert to MB
        if unit == "KB":
            return size_value / 1024
        elif unit == "MB":
            return size_value
        elif unit == "GB":
            return size_value * 1024
        
        return None

    entry_content = soup.find("div", class_="entry-content")
    if not entry_content:
        print(f"[!] Could not find entry-content div in {book_url}")
        #eturn []
        
    ul_tag = entry_content.find("ul")
    if not ul_tag:
        print(f"[!] Could not find ul tag in entry-content div in {book_url}")
        #eturn []
    #rint(ul_tag)
        # Extract file sizes
        
    pdf_size_mb = 0
    epub_size_mb = 0
    full_book_name = "Unknown"

    for li in ul_tag.find_all("li"):
        strong_text = li.find("strong")
        if strong_text:
            #rint(strong_text)
            text = strong_text.get_text().strip()
            if "Full Book Name" in text or "Full Book Name:" in text:
                full_book_name = li.get_text().replace(text, "").strip()
                #rint(full_book_name)
            if "PDF File Size" in text or "PDF File Size:" in text:
                # Extract size from the span or remaining text
                size_text = li.get_text().replace(text, "").strip()
                pdf_size_mb = extract_size_in_mb(size_text)
                #rint(size_text)
            elif "EPUB File Size:" in text or "EPUB File Size" in text:
                # Extract size from the span or remaining text
                size_text = li.get_text().replace(text, "").strip()
                epub_size_mb = extract_size_in_mb(size_text)

    # --- Skip if larger than 10 MB ---
    if pdf_size_mb > 10 and  epub_size_mb > 10:
        print(f"[!] Skipping {full_book_name} (PDF: {pdf_size_mb} MB, EPUB: {epub_size_mb} MB) too large")
        return []

    # --- Process forms ---
    forms = soup.find_all("form", action="https://oceanofpdf.com/Fetching_Resource.php")
    epub_forms, other_forms = [], []

    for form in forms:
        id_input = form.find("input", {"name": "id"})
        filename_input = form.find("input", {"name": "filename"})
        
        if id_input and filename_input:
            file_ext = filename_input["value"].split(".")[-1].lower()
            form_data = {
                "id": id_input["value"],
                "filename": filename_input["value"]
            }
            if file_ext == "epub":
                epub_forms.append(form_data)
            else:
                other_forms.append(form_data)

    time.sleep(3)  # throttle requests
    return epub_forms if epub_forms else other_forms

