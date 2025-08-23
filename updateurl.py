import mysql.connector

def update_url_type():
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="localhost",         # Change if your DB is on another host
            user="root",     # Replace with your MySQL username
            password="", # Replace with your MySQL password
            database="final_klaus_ebooks_library"
        )
        cursor = conn.cursor()

        # SQL update query
        sql = "UPDATE books SET url_type = %s WHERE url_type = %s"
        values = ("local", "server_url")

        cursor.execute(sql, values)
        conn.commit()

        print(f"✅ {cursor.rowcount} rows updated from 'server_url' → 'local'")

    except mysql.connector.Error as err:
        print(f"⚠️ Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_url_type()
