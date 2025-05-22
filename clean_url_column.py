import pandas as pd

def clean_url_column(input_csv, output_csv):
    """
    Modifies the 'sub_cat_image' column to include 'upload/' prefix
    if it is not already present.
    """
    try:
        df = pd.read_csv(input_csv)

        # Safely modify 'sub_cat_image' with 'upload/' prefix if needed
        df['sub_cat_image'] = df['sub_cat_image'].apply(
            lambda x: f"upload/{x}" if pd.notnull(x) and not str(x).startswith("upload/") else x
        )

        # Save the modified DataFrame
        df.to_csv(output_csv, index=False)
        print(f"Successfully saved modified data to: {output_csv}")
    
    except Exception as e:
        print(f"Error processing file {input_csv}: {e}")

def clean_url_column1(input_csv, output_csv):
    """
    Replaces 'uploads\' with 'upload\' in the 'url' column,
    sets 'url_type' to 'local', and disables download.
    """
    try:
        df = pd.read_csv(input_csv)

        # Safely replace 'uploads\' with 'upload\' in 'url' column
        df['url'] = df['url'].apply(
            lambda x: x.replace('uploads\\', 'upload\\') if pd.notnull(x) else x
        )

        # Set default values for other columns
        df['url_type'] = 'local'
        df['download_enable'] = 0

        # Save the modified DataFrame
        df.to_csv(output_csv, index=False)
        print(f"Successfully saved modified data to: {output_csv}")
    
    except Exception as e:
        print(f"Error processing file {input_csv}: {e}")
        
def count_rows_in_csv(file_path):
    """
    Counts the number of rows in a CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        int: The number of rows in the CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        return len(df)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

        
#clean_url_column1('books_final_redone.csv', 'books_final_redone1.csv')
clean_url_column('subcategories.csv', 'subcategories1.csv')
row_count = count_rows_in_csv('subcategories1.csv')
print(f"Total rows in subcategories1.csv: {row_count}")