import sqlite3
import pandas as pd

# Connect to (or create) the database
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# Create tables if they don’t exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS internal_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    part_name TEXT NOT NULL,
    materials_used TEXT NOT NULL,
    recyclable TEXT CHECK(recyclable IN ('Yes', 'No')) NOT NULL,
    reusable TEXT CHECK(reusable IN ('Yes', 'No')) NOT NULL,
    recycling_process TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS recyclable_item_value (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    part_name TEXT NOT NULL,
    materials_used TEXT NOT NULL,
    estimated_value TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES internal_parts(id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS recycling_centers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    center_name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact TEXT,
    working_hours TEXT,
    website TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reusable_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    part_name TEXT NOT NULL,
    reuse_potential TEXT NOT NULL,
    estimated_value TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES internal_parts(id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS resale_donate_areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL,
    center_name TEXT NOT NULL,
    address TEXT NOT NULL,
    contact TEXT,
    working_hours TEXT,
    website TEXT
);
""")

# Function to insert unique records from CSV
def insert_csv_data(csv_file, table_name, conn):
    try:
        df = pd.read_csv(csv_file)

        # Ensure column names match table structure
        columns = [col.lower().replace(" ", "_") for col in df.columns]
        df.columns = columns  

        # Check for duplicates before inserting
        existing_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        if not existing_df.empty:
            df = df[~df[columns[0]].isin(existing_df[columns[0]])]  # Avoid duplicates

        if not df.empty:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            print(f" Data from {csv_file} successfully inserted into {table_name}.")
        else:
            print(f" No new data to insert into {table_name} from {csv_file}.")
    
    except Exception as e:
        print(f" Error inserting data into {table_name}: {e}")

# Insert CSV data while avoiding overwriting existing records
insert_csv_data("internal_parts.csv", "internal_parts", conn)
insert_csv_data("recyclable_values.csv", "recyclable_item_value", conn)
insert_csv_data("recycling_centers.csv", "recycling_centers", conn)
insert_csv_data("reusable_parts.csv", "reusable_parts", conn)
insert_csv_data("resale_centers.csv", "resale_donate_areas", conn)

# Commit and close
conn.commit()
conn.close()

print(" Database setup and CSV import complete.")
