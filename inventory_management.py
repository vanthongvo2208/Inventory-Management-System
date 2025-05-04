import sqlite3
from database import connect_db
import datetime

# Add product to inventory
def add_product(product_id, name, category, initial_quantity, unit_price, units_sold, db_name="inventory.db"):
    conn = connect_db(db_name)
    cursor = conn.cursor()

    # Calculate remaining_quantity based on initial_quantity and units_sold
    remaining_quantity = initial_quantity - units_sold

    # Insert data into FullData table, including remaining_quantity and actual units_sold
    cursor.execute("""
        INSERT INTO FullData (product_id, date, product_category, product_name, units_sold, unit_price, total_revenue, initial_quantity, remaining_quantity) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_id, datetime.date.today().strftime('%m/%d/%Y'), category, name, units_sold, unit_price, units_sold * unit_price, initial_quantity, remaining_quantity))

    # Insert inventory information into Inventory table with remaining_quantity
    current_date = datetime.date.today().strftime('%m/%d/%Y')
    cursor.execute("""
        INSERT INTO Inventory (product_id, inventory_date, quantity, remaining_quantity) 
        VALUES (?, ?, ?, ?)
    """, (product_id, current_date, initial_quantity, remaining_quantity))

    conn.commit()
    conn.close()

# Delete product from inventory
def delete_product(product_id, db_name="inventory.db"):
    conn = connect_db(db_name)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM Inventory WHERE product_id = ?", (product_id,))
    conn.commit()
    print(f"Product with ID {product_id} deleted successfully.")
    conn.close()

# Update product quantity in the Inventory table
def update_inventory(product_id, units_sold, db_name="inventory.db"):
    conn = connect_db(db_name)
    cursor = conn.cursor()
    
    # Get the current quantity from the Inventory table
    cursor.execute("SELECT quantity FROM Inventory WHERE product_id = ? ORDER BY inventory_id DESC LIMIT 1", (product_id,))
    current_quantity = cursor.fetchone()
    
    if current_quantity is None:
        print(f"No inventory record found for product ID {product_id}.")
        return
    
    # Calculate new inventory quantity
    new_quantity = current_quantity[0] - units_sold
    if new_quantity < 0:
        print("Insufficient inventory!")
        return
    
    cursor.execute("INSERT INTO Inventory (product_id, inventory_date, quantity) VALUES (?, ?, ?)",
                   (product_id, datetime.date.today(), new_quantity))
    
    print(f"Inventory updated for product ID {product_id}. New quantity: {new_quantity}.")
    conn.commit()
    conn.close()
