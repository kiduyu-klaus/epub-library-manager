import os
import re

def find_bad_folders(root_path):
    bad_folders = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        for dirname in dirnames:
            if re.search(r"\s{2,}", dirname):  # 2 or more spaces
                full_path = os.path.join(dirpath, dirname)
                bad_folders.append(full_path)

    return bad_folders


# Example usage
root = r"C:\cracks\My_App\epub-library-manager\upload"  # Change to your root path
bad_folders = find_bad_folders(root)

if bad_folders:
    print("⚠️ Found folders with multiple spaces:")
    for folder in bad_folders:
        print(" -", folder)
else:
    print("✅ No bad folders found")





def fix_bad_folders(root_path):
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            if re.search(r"\s{2,}", dirname):
                old_path = os.path.join(dirpath, dirname)
                new_dirname = re.sub(r"\s{2,}", " ", dirname)  # collapse spaces
                new_path = os.path.join(dirpath, new_dirname)

                # Avoid overwriting if already exists
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    print(f"✅ Renamed: {old_path} → {new_path}")
                else:
                    print(f"⚠️ Skipped (already exists): {new_path}")
                    
fix_bad_folders(root)