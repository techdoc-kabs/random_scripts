DB_PATH = "users_db.db"
import os
import re

DB_LINE = 'DB_PATH = "users_db.db"\n'

def insert_db_path_top(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check if DB_PATH already defined anywhere
    for line in lines:
        if re.match(r"^\s*DB_PATH\s*=", line):
            return False  # Already exists

    # Insert DB_PATH as the very first line
    lines.insert(0, DB_LINE)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True

def main():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                inserted = insert_db_path_top(path)
                if inserted:
                    print(f"Inserted DB_PATH at top of {path}")
                else:
                    print(f"DB_PATH already exists in {path}")

if __name__ == "__main__":
    main()
