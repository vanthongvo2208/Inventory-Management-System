from database import create_tables, load_data_from_csv

# Path to your CSV file
csv_file_path = "D:/inventory/Online Sales Data.csv"

# Initialize tables and load data from CSV
create_tables()
load_data_from_csv(csv_file_path)

print("Database initialized and data loaded from CSV.")
