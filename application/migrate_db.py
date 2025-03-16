import sqlite3
import os
import sys

def migrate_database():
    """
    Add gray_percentage column to car_log table if it doesn't exist.
    """
    # Use the database file we found
    db_paths = [
        './instance/car_logs.db',
        './application/instance/car_logs.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Found database at: {db_path}")
            
            # Connect to the database
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check table schema to see table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"Tables in database: {tables}")
                
                # Try to find the car_log table (it might be named differently)
                table_name = None
                for table in tables:
                    if 'car_log' in table[0].lower():
                        table_name = table[0]
                        break
                
                if not table_name:
                    print(f"Could not find car_log table in {db_path}")
                    continue
                
                print(f"Found table: {table_name}")
                
                # Check if gray_percentage column exists
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]
                print(f"Columns in {table_name}: {column_names}")
                
                if 'gray_percentage' not in column_names:
                    print(f"Adding gray_percentage column to {table_name} table...")
                    # Add the column with a default value of NULL
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN gray_percentage FLOAT")
                    conn.commit()
                    print("Successfully added gray_percentage column.")
                else:
                    print("Column gray_percentage already exists. No migration needed.")
                
                conn.close()
                print(f"Successfully migrated database: {db_path}")
            except Exception as e:
                print(f"Error migrating database {db_path}: {e}")
    
    return True

if __name__ == "__main__":
    if migrate_database():
        print("Database migration completed successfully.")
    else:
        print("Database migration failed.")
        sys.exit(1) 