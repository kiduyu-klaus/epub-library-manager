import re
import mysql.connector

# ==== MySQL Connection (XAMPP) ====
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="final_klaus_ebooks_library"
)
cursor = conn.cursor()

def fix_author_names():
    """
    Check all authors' names for multiple spaces, fix them, update MySQL, and print changes.
    """
    cursor.execute("SELECT id, name FROM authors")
    rows = cursor.fetchall()

    for author_id, name in rows:
        # Collapse multiple spaces into one
        fixed_name = re.sub(r"\s{2,}", " ", name.strip())

        if fixed_name != name:
            cursor.execute("UPDATE authors SET name = %s WHERE id = %s", (fixed_name, author_id))
            print(f"✅ Updated author_id={author_id} | Old: '{name}' | New: '{fixed_name}'")

    conn.commit()
    print("🔄 All problematic author names fixed and updated.")

# Example run
fix_author_names()