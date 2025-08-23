import re
import mysql.connector

# ==== MySQL Connection (XAMPP) ====
conn = mysql.connector.connect(
    host="localhost",     # XAMPP MySQL host
    user="root",          # XAMPP MySQL username
    password="",          # XAMPP MySQL password (empty by default)
    database="final_klaus_ebooks_library"
)
#cursor = conn.cursor()

def fix_book_urls():
    """
    Check all books' URLs for multiple spaces, fix them, update MySQL, and print changes.
    """
    cursor.execute("SELECT id, url FROM books WHERE url IS NOT NULL")
    rows = cursor.fetchall()

    for book_id, url in rows:
        # Collapse multiple spaces into one
        fixed_url = re.sub(r"\s{2,}", " ", url)

        if fixed_url != url:  # Only update if something changed
            cursor.execute("UPDATE books SET url = %s WHERE id = %s", (fixed_url, book_id))
            print(f"✅ Updated book_id={book_id} | Old: '{url}' | New: '{fixed_url}'")

    conn.commit()
    print("🔄 All problematic URLs fixed and updated.")

# Example run
#fix_book_urls()



# ==== MySQL Connection (XAMPP) ====

cursor = conn.cursor(dictionary=True)

def authors_with_few_books(limit=10):
    """
    Find and print authors with fewer than `limit` books total.
    """
    # Fetch all authors
    cursor.execute("SELECT id, name FROM authors")
    authors = cursor.fetchall()

    # Fetch all books with their author_ids
    cursor.execute("SELECT id, author_ids FROM books")
    books = cursor.fetchall()

    # Count books per author
    author_book_count = {author["id"]: 0 for author in authors}

    for book in books:
        if not book["author_ids"]:
            continue
        for aid in book["author_ids"].split(","):  # assume comma-separated
            aid = aid.strip()
            if aid.isdigit():
                aid = int(aid)
                if aid in author_book_count:
                    author_book_count[aid] += 1

    # Print authors with fewer than limit books
    print(f"📚 Authors with fewer than {limit} books:")
    for author in authors:
        count = author_book_count[author["id"]]
        if count < limit:
            print(f" - {author['name']} (id={author['id']}): {count} books")

# Example run
authors_with_few_books(10)