import os
import sys
import sqlite3
import time
import glob

def find_database():
    """
    Find the SQLite database file by searching in common locations.
    """
    possible_locations = [
        "car_logs.db",
        "application/car_logs.db",
        "instance/car_logs.db",
        "../car_logs.db"
    ]
    
    # Search for any .db files if specific file not found
    for location in possible_locations:
        if os.path.exists(location):
            return location
    
    # Fall back to searching for any SQLite database
    db_files = glob.glob("*.db") + glob.glob("application/*.db") + glob.glob("instance/*.db")
    if db_files:
        return db_files[0]
    
    return None

def setup_database(db_path):
    """
    Create a new database file with the required table structure if it doesn't exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create car_log table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS car_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_id TEXT NOT NULL,
        date TEXT NOT NULL,
        expected_part TEXT NOT NULL,
        actual_part TEXT NOT NULL,
        original_image_path TEXT NOT NULL,
        result_image_path TEXT NOT NULL,
        outcome TEXT NOT NULL,
        gray_percentage REAL
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {db_path}")
    return True

def cleanup_database():
    """
    Delete all entries in the database except for the most recent 3.
    """
    print("\n=== DATABASE CLEANUP UTILITY ===")
    
    # Find the database
    db_path = find_database()
    if not db_path:
        print("No database file found. Would you like to create one? (y/n)")
        if input().lower() in ['y', 'yes']:
            db_path = "car_logs.db"
            setup_database(db_path)
        else:
            print("Operation cancelled.")
            return False
    else:
        print(f"Using database at: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the car_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='car_log'")
        if not cursor.fetchone():
            print("The car_log table doesn't exist in the database.")
            setup_database(db_path)
            print("No entries to delete in the newly created table.")
            return True
        
        # Count total entries
        cursor.execute("SELECT COUNT(*) FROM car_log")
        total_entries = cursor.fetchone()[0]
        print(f"Found {total_entries} entries in car_log table")
        
        if total_entries <= 3:
            print("There are 3 or fewer entries in the database. No cleanup needed.")
            return True
        
        # Get IDs of entries to preserve (most recent 3)
        cursor.execute("SELECT id FROM car_log ORDER BY id DESC LIMIT 3")
        preserved_ids = [row[0] for row in cursor.fetchall()]
        
        # Confirm with user
        entries_to_delete = total_entries - 3
        print(f"This will delete {entries_to_delete} entries, keeping the 3 most recent.")
        print(f"Entries to preserve: {preserved_ids}")
        
        confirm = input("Do you want to proceed? (y/n): ")
        if confirm.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return False
        
        # Create backup
        backup_path = f"car_logs_backup_{int(time.time())}.db"
        with open(db_path, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        print(f"Created backup at {backup_path}")
        
        # Check if there are any preserved IDs
        if preserved_ids:
            # Delete entries
            preserved_ids_str = ', '.join(str(id) for id in preserved_ids)
            cursor.execute(f"DELETE FROM car_log WHERE id NOT IN ({preserved_ids_str})")
        else:
            # Delete all entries if no preserved IDs
            cursor.execute("DELETE FROM car_log")
            
        deleted_count = cursor.rowcount
        
        # Commit changes
        conn.commit()
        
        print(f"Successfully deleted {deleted_count} entries.")
        print(f"Database now contains {total_entries - deleted_count} entries.")
        
        # Optimize database
        cursor.execute("VACUUM")
        print("Database optimized.")
        
        return True
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    success = cleanup_database()
    if success:
        print("Database cleanup completed successfully.")
    else:
        print("Database cleanup failed.")
        sys.exit(1) 