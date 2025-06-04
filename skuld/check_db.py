import sqlite3
import json
from datetime import datetime

def dump_db():
    with sqlite3.connect('schedules.db') as conn:
        conn.row_factory = sqlite3.Row
        
        # Get schedules
        cursor = conn.execute('SELECT * FROM schedules')
        schedules = [dict(row) for row in cursor.fetchall()]
        
        # Get executions
        cursor = conn.execute('SELECT * FROM executions ORDER BY executedAt DESC LIMIT 10')
        executions = [dict(row) for row in cursor.fetchall()]
        
        data = {
            'schedules': schedules,
            'executions': executions
        }
        
        # Convert to JSON with proper datetime handling
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        print(json.dumps(data, indent=2, cls=DateTimeEncoder))

if __name__ == '__main__':
    dump_db() 