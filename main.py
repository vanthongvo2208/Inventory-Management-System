import sqlite3
import tkinter as tk
from tkinter import messagebox, Toplevel, Text, Entry, Label, Button, ttk, Frame, OptionMenu, StringVar
import matplotlib.pyplot as plt
import pandas as pd
import random
from datetime import datetime
from database import connect_db
from inventory_management import delete_product, add_product
from forecasting import forecast_inventory

# Add and update the 'remaining_quantity' column in both 'FullData' and 'Inventory' tables
def add_remaining_quantity_column():
    try:
        # Connect to your SQLite database
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()
        
        # Add remaining_quantity column to FullData table if not exists
        cursor.execute("ALTER TABLE FullData ADD COLUMN remaining_quantity INTEGER")
        
        # Calculate remaining_quantity for FullData table and update it
        cursor.execute("""
            UPDATE FullData
            SET remaining_quantity = initial_quantity - units_sold
            WHERE initial_quantity IS NOT NULL AND units_sold IS NOT NULL
        """)
        
        # Add remaining_quantity column to Inventory table if not exists
        cursor.execute("ALTER TABLE Inventory ADD COLUMN remaining_quantity INTEGER")
        
        # Update remaining_quantity in Inventory table based on FullData sales information
        cursor.execute("""
            UPDATE Inventory
            SET remaining_quantity = (
                SELECT remaining_quantity 
                FROM FullData 
                WHERE FullData.product_id = Inventory.product_id
            )
        """)
        
        # Commit the changes
        conn.commit()
        
        # Verify the updates
        full_data = cursor.execute("SELECT * FROM FullData LIMIT 5").fetchall()
        inventory_data = cursor.execute("SELECT * FROM Inventory LIMIT 5").fetchall()
        
        print("Sample FullData with Remaining Quantity:")
        for row in full_data:
            print(row)
        
        print("\nSample Inventory with Remaining Quantity:")
        for row in inventory_data:
            print(row)
        
        # Close the connection
        conn.close()
        print("Remaining quantity column added and updated successfully in both tables.")

    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Call the function to add and update remaining_quantity column
add_remaining_quantity_column()

# Define the standardize_date_format function here
def standardize_date_format():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Update Inventory table dates to %m/%d/%Y
    cursor.execute("SELECT product_id, inventory_date, quantity FROM Inventory")
    rows = cursor.fetchall()
    for row in rows:
        product_id, inventory_date, quantity = row
        try:
            # Check if the date is in %Y-%m-%d format and convert it
            standardized_date = datetime.strptime(inventory_date, '%Y-%m-%d').strftime('%m/%d/%Y')
            cursor.execute("UPDATE Inventory SET inventory_date = ? WHERE product_id = ? AND inventory_date = ?", 
                           (standardized_date, product_id, inventory_date))
        except ValueError:
            # If it's already in %m/%d/%Y format, ignore it
            continue

    # Update FullData table dates to %m/%d/%Y
    cursor.execute("SELECT product_id, date FROM FullData")
    rows = cursor.fetchall()
    for row in rows:
        product_id, date = row
        try:
            # Check if the date is in %Y-%m-%d format and convert it
            standardized_date = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%Y')
            cursor.execute("UPDATE FullData SET date = ? WHERE product_id = ? AND date = ?", 
                           (standardized_date, product_id, date))
        except ValueError:
            # If it's already in %m/%d/%Y format, ignore it
            continue

    conn.commit()
    conn.close()
    print("Date format standardized to %m/%d/%Y in Inventory and FullData tables.")

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Warehouse Management System")
        
        # Login greeting
        Label(root, text="Login successful! Welcome, User.", font=("Arial", 12)).pack(pady=10)       
        
        # Display monthly inventory quantity button
        Button(root, text="Display monthly inventory quantity", command=self.show_monthly_inventory, width=30).pack(pady=5)
        
        # Display sales chart button
        Button(root, text="Display sales chart", command=self.show_sales_chart, width=30).pack(pady=5)
        
        # Forecast next month's sales quantity button
        Button(root, text="Forecast next month's sales quantity", command=self.forecast_inventory, width=30).pack(pady=5)
        
        # Display FullData button
        Button(root, text="Display FullData", command=self.show_full_data, width=30).pack(pady=5)
        
        # Add new product button
        Button(root, text="Add new product", command=self.add_product_form, width=30).pack(pady=5)
        
        # Update product button
        Button(root, text="Update product", command=self.update_inventory_form, width=30).pack(pady=5)
        
        # Delete product button
        Button(root, text="Delete product", command=self.delete_product_form, width=30).pack(pady=5)

        Button(root, text="Exit", command=self.exit_application, width=30).pack(pady=5)

    # Display the total monthly inventory quantity    
    def show_monthly_inventory(self):
        try:
            conn = connect_db()# Connect to the database
             # Query to calculate total inventory quantity for the current month
            query = """
                SELECT SUBSTR(inventory_date, 1, 2) || '/' || SUBSTR(inventory_date, 7, 4) AS month, 
                       SUM(remaining_quantity) AS total_quantity
                FROM Inventory
                WHERE SUBSTR(inventory_date, 1, 2) || '/' || SUBSTR(inventory_date, 7, 4) = 
                      strftime('%m/%Y', 'now')
                GROUP BY month
            """

            # Execute the query and load data into a DataFrame
            df = pd.read_sql_query(query, conn) 
            conn.close() # Close the database connection
            
            # Check if there's data for the current month
            if df.empty:
                messagebox.showinfo("Monthly Inventory", "No inventory data for this month.")
            else:
                total_quantity = df['total_quantity'].iloc[0]
                messagebox.showinfo("Monthly Inventory", f"Inventory quantity for the current month: {total_quantity}")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to display monthly inventory: {e}")

    # Display sales chart with total monthly revenue
    def show_sales_chart(self):
        try:
            conn = connect_db()
            # Query to calculate total revenue by sale date
            query = "SELECT sale_date, SUM(total_revenue) AS total_revenue FROM Sales GROUP BY sale_date"
            sales_data = pd.read_sql_query(query, conn)
            conn.close()

            # Check if there's sales data to display
            if sales_data.empty:
                messagebox.showinfo("Sales Chart", "No sales data to display.")
                return

            # Convert 'sale_date' to datetime format and aggregate monthly
            sales_data['sale_date'] = pd.to_datetime(sales_data['sale_date'], format='%m/%d/%Y')
            sales_data = sales_data.resample('M', on='sale_date').sum().reset_index()

            # Plotting the aggregated monthly data
            plt.figure(figsize=(10, 6))
            plt.bar(sales_data['sale_date'].dt.strftime('%m/%Y'), sales_data['total_revenue'], color='skyblue')
            plt.xlabel("Month")
            plt.ylabel("Total Revenue")
            plt.title("Monthly Sales Revenue Over Time")
            plt.xticks(rotation=45, ha="right")

            # Adding labels for each bar
            for index, value in enumerate(sales_data['total_revenue']):
                plt.text(index, value, f"{value:.2f}", ha='center', va='bottom')
            
            plt.tight_layout() # Adjust layout to fit everything neatly
            plt.show() # Display the chart

        except Exception as e:
            messagebox.showerror("Error", f"Unable to display sales chart: {e}")

    # Define function to display all data from FullData table with search and sort functionality
    def show_full_data(self):

        # Define function for applying search based on selected column and search term
        def apply_search():
            search_value = search_entry.get() # Get search term from entry box
            column = search_column.get() # Get selected column for search

            # Construct search query with LIKE for partial matching
            query = f"SELECT * FROM FullData WHERE {column} LIKE ?"
            search_term = f"%{search_value}%"

            conn = connect_db()
            df = pd.read_sql_query(query, conn, params=(search_term,))
            conn.close()

            # Display search results in the GUI
            display_data(df)

        # Define function for applying sort based on selected column and order
        def apply_sort():
            sort_column = sort_column_var.get() # Get selected column for sorting
            sort_order = sort_order_var.get() # Get selected sort order (ASC or DESC)

            conn = connect_db()
            query = f"SELECT * FROM FullData ORDER BY {sort_column} {sort_order}"
            df = pd.read_sql_query(query, conn)
            conn.close()
    
            # Display sorted data in the GUI
            display_data(df)

        # Define function for updating the GUI with current DataFrame data
        def display_data(dataframe):
            """Update the display with the current DataFrame."""
            if dataframe.empty:
                messagebox.showinfo("FullData", "No matching data found.")
            else:
                for widget in result_frame.winfo_children(): # Clear any previous data from result frame
                    widget.destroy()
            
                text = Text(result_frame, wrap='none') # Create text widget for displaying data
                text.insert('1.0', dataframe.to_string(index=False)) # Insert DataFrame content into text widget
                text.pack(fill='both', expand=True) # Pack and expand text widget to fit frame

        # Create a new window for displaying FullData
        top = Toplevel(self.root)
        top.title("Display FullData")

        # Maximize window to full screen
        top.state("zoomed")

        # Get column names from FullData table for search and sort options
        conn = connect_db()
        initial_df = pd.read_sql_query("SELECT * FROM FullData", conn)
        columns = initial_df.columns.tolist()
        conn.close()

        # Set up search section with options for selecting column and entering search term
        Label(top, text="Search by:").grid(row=0, column=0, sticky="w")
        search_column = StringVar(top)
        search_column.set(columns[0])  # Default to the first column
        search_column_menu = OptionMenu(top, search_column, *columns)
        search_column_menu.grid(row=0, column=1)

        search_entry = Entry(top) # Entry widget for entering search term
        search_entry.grid(row=0, column=2)

        search_button = Button(top, text="Apply Search", command=apply_search) # Button to apply search
        search_button.grid(row=0, column=3)

        # Set up sort section with options for selecting column and sort order
        Label(top, text="Sort by:").grid(row=1, column=0, sticky="w") # Label for sort section
        sort_column_var = StringVar(top)
        sort_column_var.set(columns[0])  # Default to the first column
        sort_column_menu = OptionMenu(top, sort_column_var, *columns)
        sort_column_menu.grid(row=1, column=1)

        sort_order_var = StringVar(top)
        sort_order_var.set("ASC")  # Default to ascending order
        sort_order_menu = OptionMenu(top, sort_order_var, "ASC", "DESC")
        sort_order_menu.grid(row=1, column=2)

        sort_button = Button(top, text="Apply Sort", command=apply_sort)
        sort_button.grid(row=1, column=3)

         # Frame to display the search or sort results
        result_frame = Frame(top)
        result_frame.grid(row=2, column=0, columnspan=4, sticky="nsew")
        top.grid_rowconfigure(2, weight=1)
        top.grid_columnconfigure(3, weight=1)

        # Display initial unsorted data
        display_data(initial_df)

    # Define function to create form for adding a new product
    def add_product_form(self):
        
        # Create a new top-level window for the product form
        form = Toplevel(self.root)
        form.title("Add New Product")

        # Product Category input field
        Label(form, text="Product Category:").grid(row=0, column=0)
        category_entry = Entry(form)
        category_entry.grid(row=0, column=1)

        # Product Name input field
        Label(form, text="Product Name:").grid(row=1, column=0)
        name_entry = Entry(form)
        name_entry.grid(row=1, column=1)

        # Units Sold input field
        Label(form, text="Units Sold:").grid(row=2, column=0)
        sold_entry = Entry(form)
        sold_entry.grid(row=2, column=1)

        # Unit Price input field
        Label(form, text="Unit Price:").grid(row=3, column=0)
        price_entry = Entry(form)
        price_entry.grid(row=3, column=1)

        # Initial Quantity input field
        Label(form, text="Initial Quantity:").grid(row=4, column=0)
        quantity_entry = Entry(form)
        quantity_entry.grid(row=4, column=1)

        # Function to handle product addition
        def submit():
            product_id = random.randint(10000, 99999)  # Generate a random product ID
            product_category = category_entry.get().title() # Get and capitalize product category
            product_name = name_entry.get().title() # Get and capitalize product name
            units_sold = int(sold_entry.get()) # Get units sold as integer
            unit_price = float(price_entry.get())  # Get unit price as float
            initial_quantity = int(quantity_entry.get()) # Get initial quantity as integer
            current_date = datetime.now().strftime('%m/%d/%Y') # Get the current date

            # Connect to the database and insert product data
            conn = connect_db()
            cursor = conn.cursor()
            add_product(product_id, product_name, product_category, initial_quantity, unit_price, units_sold)

            # Insert product information into Products table
            cursor.execute("""
                INSERT INTO Products (product_id, product_name, product_category, initial_quantity) 
                VALUES (?, ?, ?, ?)
            """, (product_id, product_name, product_category, initial_quantity))
                
            # Insert initial sales data into Sales table
            cursor.execute("""
                INSERT INTO Sales (product_id, sale_date, units_sold, unit_price, total_revenue) 
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, current_date, units_sold, unit_price, units_sold * unit_price))

            
            conn.commit()
            conn.close()

            # Show success message and close form
            messagebox.showinfo("Add Product", f"Product with ID {product_id} has been added successfully.")
            form.destroy()

        Button(form, text="Add Product", command=submit).grid(row=5, column=1)

    # Define function to create a form for updating product information
    def update_inventory_form(self):
        
        # Create a new top-level window for the update form
        form = Toplevel(self.root)
        form.title("Update Product") # Set the window title

        # Product ID input field
        Label(form, text="Product ID:").grid(row=0, column=0)
        product_id_entry = Entry(form)
        product_id_entry.grid(row=0, column=1)

        # Units Sold input field
        Label(form, text="Units Sold:").grid(row=1, column=0)
        sold_entry = Entry(form)
        sold_entry.grid(row=1, column=1)

        # Unit Price input field
        Label(form, text="Unit Price:").grid(row=2, column=0)
        price_entry = Entry(form)
        price_entry.grid(row=2, column=1)

        # Initial Quantity input field
        Label(form, text="Initial Quantity:").grid(row=3, column=0)
        quantity_entry = Entry(form)
        quantity_entry.grid(row=3, column=1)

        # Function to handle the update submission
        def submit_update():
            product_id = int(product_id_entry.get()) # Get product ID as integer
            units_sold = int(sold_entry.get()) # Get units sold as integer
            unit_price = float(price_entry.get()) # Get unit price as float
            initial_quantity = int(quantity_entry.get()) # Get initial quantity as integer

            conn = connect_db()
            cursor = conn.cursor()

            # Check if the product ID exists
            cursor.execute("SELECT product_id FROM Products WHERE product_id = ?", (product_id,))
            result = cursor.fetchone()

            if result:
                # Update product details in FullData table
                cursor.execute("""
                    UPDATE FullData 
                    SET units_sold = ?, unit_price = ?, initial_quantity = ? 
                    WHERE product_id = ?
                """, (units_sold, unit_price, initial_quantity, product_id))

                # Recalculate remaining_quantity for FullData
                cursor.execute("""
                    UPDATE FullData 
                    SET remaining_quantity = initial_quantity - units_sold 
                    WHERE product_id = ?
                """, (product_id,))

                # Update quantity and remaining_quantity in Inventory table
                cursor.execute("""
                    UPDATE Inventory
                    SET quantity = ?, remaining_quantity = ?
                    WHERE product_id = ?
                """, (initial_quantity, initial_quantity - units_sold, product_id))

                # Update units sold, unit price, and total revenue in Sales table
                cursor.execute("""
                    UPDATE Sales
                    SET units_sold = ?, unit_price = ?, total_revenue = ?
                    WHERE product_id = ?
                """, (units_sold, unit_price, units_sold * unit_price, product_id))

                # Update initial quantity in Products table
                cursor.execute("""
                    UPDATE Products
                    SET initial_quantity = ?
                    WHERE product_id = ?
                """, (initial_quantity, product_id))
                     
                conn.commit()
                messagebox.showinfo("Update Product", f"Product with ID {product_id} has been updated successfully.")
                form.destroy()

            else:
                # Show an error if the product ID does not exist
                messagebox.showerror("Error", f"Product ID {product_id} does not exist.")

            conn.close()

        Button(form, text="Update Product", command=submit_update).grid(row=4, column=1)

    # Function to delete product
    def delete_product_form(self):
        
        # Create a new top-level window for the delete form
        form = Toplevel(self.root)
        form.title("Delete Product")

        # Product ID input field
        Label(form, text="Product ID:").grid(row=0, column=0)
        product_id_entry = Entry(form)
        product_id_entry.grid(row=0, column=1)

        # Function to handle product deletion
        def submit_delete():
            product_id = int(product_id_entry.get()) # Get product ID as integer

            conn = connect_db()
            cursor = conn.cursor()

            # Check if the product ID exists
            cursor.execute("SELECT product_id FROM Products WHERE product_id = ?", (product_id,))
            result = cursor.fetchone()

            if result:
                # Proceed with deletion if the product exists
                cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM Inventory WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM Sales WHERE product_id = ?", (product_id,))
                cursor.execute("DELETE FROM FullData WHERE product_id = ?", (product_id,))
                conn.commit()            
                messagebox.showinfo("Delete Product", f"Product with ID {product_id} has been deleted successfully.")
                form.destroy()
            else:
                # Show an error if the product ID does not exist
                messagebox.showerror("Error", f"Product ID {product_id} does not exist.")

            conn.close()

        Button(form, text="Delete Product", command=submit_delete).grid(row=1, column=1)

    # Function to forecast inventory for a product without displaying chart.
    def forecast_inventory(self):

        # Create a new top-level window for the forecast form
        form = Toplevel(self.root)
        form.title("Inventory Forecast")

        # Product ID input field
        Label(form, text="Product ID:").grid(row=0, column=0)
        product_id_entry = Entry(form)
        product_id_entry.grid(row=0, column=1)

        # Label to display the error or success message for forecast results
        message_label = Label(form, text="", fg="red")
        message_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # Function to handle inventory forecasting
        def submit_forecast():
            product_id = int(product_id_entry.get()) # Get product ID as integer
            forecast_df = forecast_inventory(product_id) # Get forecast data for the product

            # Check if forecast data is available
            if isinstance(forecast_df, list) or forecast_df.empty:
                
                # Display error message if no data is available
                message_label.config(text=f"No data available for product ID {product_id}.")
            else:
                # Display forecasted inventory data in a message box
                forecast_text = "Inventory forecast for the next 10 days:\n"
                for _, row in forecast_df.iterrows():
                    forecast_text += f"{row['date'].strftime('%m/%d/%Y')}: {row['forecasted_quantity']}\n"
                messagebox.showinfo("Inventory Forecast", forecast_text)
                form.destroy() # Close the forecast form window

        Button(form, text="Forecast", command=submit_forecast).grid(row=1, column=1)

    # Exit the application and ensure all changes are saved.
    def exit_application(self):

        # Confirm exit and close the application if confirmed
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()  # Exit the Tkinter main loop
            self.root.destroy()  # Destroy all Tkinter windows

#Display login window and verify credentials.    
def login():

    # Function to check the entered credentials
    def check_credentials():
        username = username_entry.get() # Get entered username
        password = password_entry.get() # Get entered password

        # Connect to the database and validate credentials
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone() # Fetch the result if credentials are valid
        conn.close()

        # If credentials are correct, proceed to main app; otherwise, show error
        if result:
            login_window.destroy()  # Close login window if successful
            show_main_app()  # Show main app window after login
        else:
            messagebox.showerror("Error", "Incorrect username or password!")

    # Create the login window
    login_window = Toplevel(root)
    login_window.title("Login")

    # Username input field
    Label(login_window, text="Username").pack(pady=5)
    username_entry = Entry(login_window)
    username_entry.pack(pady=5)

    # Password input field (with hidden characters)
    Label(login_window, text="Password").pack(pady=5)
    password_entry = Entry(login_window, show="*")
    password_entry.pack(pady=5)
    
    Button(login_window, text="Login", command=check_credentials).pack(pady=10)

def show_main_app():
    # Create and show the main application interface
    main_app = InventoryApp(root)
    root.deiconify()  # Show the main window

# Initialize Tkinter root window, but hide it initially
root = tk.Tk()
root.withdraw()  # Hide the main window until login is successful
root.title("Warehouse Management System")

# Call the login function when the application starts
login()

# Start the Tkinter main loop
root.mainloop()



