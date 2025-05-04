import sqlite3
import pandas as pd

def connect_db(db_name="inventory.db"):
    # Establish a connection to the specified SQLite database
    return sqlite3.connect(db_name)

def create_tables(db_name="inventory.db"):
    # Create necessary tables in the database if they do not already exist
    conn = connect_db(db_name)
    cursor = conn.cursor()
    
    # Create Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT,
        product_category TEXT,
        initial_quantity INTEGER,
        UNIQUE(product_id)
    )
    ''')

    # Create Sales table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_date TEXT,
        units_sold INTEGER,
        unit_price REAL,
        total_revenue REAL,
        FOREIGN KEY (product_id) REFERENCES Products (product_id),
        UNIQUE(product_id, sale_date)
    )
    ''')

    # Create Inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        inventory_date TEXT,
        quantity INTEGER,
        FOREIGN KEY (product_id) REFERENCES Products (product_id),
        UNIQUE(product_id, inventory_date)
    )
    ''')

    # Create FullData table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS FullData (
        product_id INTEGER,
        date TEXT,
        product_category TEXT,
        product_name TEXT,
        units_sold INTEGER,
        unit_price REAL,
        total_revenue REAL,
        initial_quantity INTEGER,
        UNIQUE(product_id, date)
    )
    ''')

    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    # Add default user account
    cursor.execute("INSERT OR IGNORE INTO Users (username, password) VALUES (?, ?)", ('account', 'password'))

    print("Tables created successfully.")
    conn.commit()
    conn.close()

def load_data_from_csv(csv_file, db_name="inventory.db"):
    # Read data from CSV
    df = pd.read_csv(csv_file)
    
    # Connect to the database
    conn = connect_db(db_name)
    cursor = conn.cursor()

    # Add data to Products table
    products_data = df[['Product ID', 'Product Name', 'Product Category', 'Initial_Quantity']].drop_duplicates()
    products_data.columns = ['product_id', 'product_name', 'product_category', 'initial_quantity']
    products_data.to_sql('Products', conn, if_exists='replace', index=False)
    
    # Add data to Sales table
    sales_data = df[['Product ID', 'Date', 'Units Sold', 'Unit Price', 'Total Revenue']]
    sales_data.columns = ['product_id', 'sale_date', 'units_sold', 'unit_price', 'total_revenue']
    sales_data.to_sql('Sales', conn, if_exists='replace', index=False)

    # Initialize Inventory table with initial quantities if needed
    inventory_data = products_data[['product_id', 'initial_quantity']].copy()
    inventory_data['inventory_date'] = pd.to_datetime('today').strftime('%m/%d/%Y')
    inventory_data.rename(columns={'initial_quantity': 'quantity'}, inplace=True)
    inventory_data = inventory_data[['product_id', 'inventory_date', 'quantity']]
    inventory_data.to_sql('Inventory', conn, if_exists='replace', index=False)

    # Add data to FullData table
    full_data = df.rename(columns={
        'Product ID': 'product_id',
        'Date': 'date',
        'Product Category': 'product_category',
        'Product Name': 'product_name',
        'Units Sold': 'units_sold',
        'Unit Price': 'unit_price',
        'Total Revenue': 'total_revenue',
        'Initial_Quantity': 'initial_quantity'
    })
    full_data.to_sql('FullData', conn, if_exists='replace', index=False)

    print("Data loaded into the database successfully.")
    conn.commit()
    conn.close()

# Only create tables when this module is imported or run
create_tables()
