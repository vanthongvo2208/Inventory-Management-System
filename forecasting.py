import sqlite3
import pandas as pd
from database import connect_db

# Inventory forecast function based on Initial_Quantity and Units Sold from FullData table
def forecast_inventory(product_id, db_name="inventory.db"):
    conn = connect_db(db_name)
    query = "SELECT date, initial_quantity, SUM(units_sold) AS total_units_sold FROM FullData WHERE product_id = ? GROUP BY date"
    df = pd.read_sql_query(query, conn, params=(product_id,))
    conn.close()
    
    # Check inventory data
    if df.empty:
        print(f"No data available for product ID {product_id}.")
        return []
    
    # Calculate current inventory quantity
    initial_quantity = df['initial_quantity'].iloc[0]  # Initial Available Quantity
    total_units_sold = df['total_units_sold'].sum()    # Total quantity sold
    current_inventory = initial_quantity - total_units_sold

    # Calculate average daily consumption rate based on sales volume
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by="date")
    df['daily_units_sold'] = df['total_units_sold'].diff().fillna(df['total_units_sold'].iloc[0])
    avg_daily_usage = df['daily_units_sold'].mean()

    # If there is no consumption rate, keep the value fixed
    if avg_daily_usage <= 0:
        avg_daily_usage = 0

    # Inventory forecast for the next 10 days
    future_dates = pd.date_range(df['date'].iloc[-1] + pd.Timedelta(days=1), periods=10, freq='D')
    forecasted_quantities = [max(0, current_inventory - i * avg_daily_usage) for i in range(10)]
    
    # Create DataFrame containing forecast
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'forecasted_quantity': forecasted_quantities
    })

    # Return forecast data
    return forecast_df
