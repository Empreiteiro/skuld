import sqlite3

def check_schema():
    with sqlite3.connect('schedules.db') as conn:
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            print(f"Table: {table[1]}")
            cursor.execute(f"PRAGMA table_info({table[1]});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            print()

if __name__ == '__main__':
    check_schema() 