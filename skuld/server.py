from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from croniter import croniter
from contextlib import contextmanager
import threading
import time
from queue import Queue
import functools

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

# Pool de conexões
class DatabaseConnectionPool:
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self.thread_local = threading.local()
        
        # Inicializar o pool com conexões
        for _ in range(max_connections):
            self.connections.put(self._create_connection())
    
    def _create_connection(self):
        db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
        conn = sqlite3.connect(
            db_path,
            timeout=60.0,
            isolation_level=None,
            check_same_thread=False  # Permitir uso em diferentes threads
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 60000")
        return conn
    
    @contextmanager
    def get_connection(self):
        connection = None
        try:
            # Tentar obter uma conexão do pool
            connection = self.connections.get(timeout=10)
            yield connection
        finally:
            # Devolver a conexão ao pool se ela foi obtida
            if connection is not None:
                try:
                    # Fazer rollback de qualquer transação pendente
                    connection.rollback()
                except Exception:
                    # Se houver erro no rollback, recriar a conexão
                    connection = self._create_connection()
                finally:
                    # Devolver a conexão ao pool
                    self.connections.put(connection)

# Criar pool global
db_pool = DatabaseConnectionPool()

# Decorator para retry
def with_retry(max_retries=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_error = e
                    if "database is locked" in str(e):
                        time.sleep(delay * (attempt + 1))
                        continue
                    raise
                except Exception as e:
                    raise
            raise last_error
        return wrapper
    return decorator

def get_db():
    try:
        with db_pool.get_connection() as conn:
            return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def init_db():
    try:
        logger.info("Initializing database...")
        with db_pool.get_connection() as conn:
            try:
                # Criar tabelas se não existirem
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        cronExpression TEXT NOT NULL,
                        url TEXT NOT NULL,
                        method TEXT NOT NULL,
                        active BOOLEAN NOT NULL DEFAULT 1,
                        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS executions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scheduleId INTEGER NOT NULL,
                        scheduleName TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response TEXT,
                        executedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (scheduleId) 
                            REFERENCES schedules(id) 
                            ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL UNIQUE,
                        value TEXT NOT NULL,
                        updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                logger.info("Database tables created successfully")
                
                # Verificar se a coluna active existe
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(schedules)")
                columns = cursor.fetchall()
                has_active = any(col[1] == 'active' for col in columns)
                
                if not has_active:
                    logger.info("Adding active column to schedules table...")
                    conn.execute('ALTER TABLE schedules ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1')
                    logger.info("Active column added successfully")
                else:
                    logger.info("Database tables already exist with correct schema")
                
                # Verificar se o banco está acessível
                cursor.execute("SELECT COUNT(*) FROM schedules")
                count = cursor.fetchone()[0]
                logger.info(f"Database is accessible. Found {count} schedules.")
                
            except sqlite3.Error as e:
                logger.error(f"Database error during initialization: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def execute_request(schedule):
    logger.info(f"Checking execution for schedule: {schedule['name']}")
    try:
        # Verificar se o agendamento está ativo
        with db_pool.get_connection() as conn:
            cursor = conn.execute('SELECT active FROM schedules WHERE id = ?', (schedule['id'],))
            result = cursor.fetchone()
            if not result or not result['active']:
                logger.info(f"Schedule {schedule['name']} is inactive, skipping execution")
                return False

        logger.info(f"Executing request for schedule: {schedule['name']}")
        try:
            response = requests.request(
                method=schedule['method'],
                url=schedule['url'],
                timeout=30  # Adiciona um timeout de 30 segundos
            )
            response.raise_for_status()  # Levanta exceção para status codes >= 400
            
            log_execution(
                schedule['id'],
                schedule['name'],
                'success',
                response.text
            )
            
            logger.info(f"Successfully executed schedule: {schedule['name']}")
            return True
        except requests.exceptions.RequestException as error:
            error_message = str(error)
            logger.error(f"Error executing schedule {schedule['name']}: {error_message}")
            
            log_execution(
                schedule['id'],
                schedule['name'],
                'error',
                error_message
            )
            return False
    except Exception as e:
        logger.error(f"Unexpected error in execute_request for schedule {schedule['name']}: {str(e)}")
        return False

def log_execution(schedule_id, schedule_name, status, response):
    logger.info(f"Logging execution for schedule {schedule_name} with status {status}")
    try:
        with db_pool.get_connection() as conn:
            conn.execute('''
                INSERT INTO executions (scheduleId, scheduleName, status, response)
                VALUES (?, ?, ?, ?)
            ''', (schedule_id, schedule_name, status, response))
            logger.info(f"Execution logged successfully for schedule {schedule_name}")
    except Exception as e:
        logger.error(f"Error logging execution: {str(e)}")

def validate_schedule(data):
    required_fields = ['name', 'cronExpression', 'url', 'method']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not data[field]:
            raise ValueError(f"Field cannot be empty: {field}")
    
    # Validate cron expression
    if not croniter.is_valid(data['cronExpression']):
        raise ValueError("Invalid cron expression")
    
    # Validate method
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE']
    if data['method'] not in valid_methods:
        raise ValueError(f"Invalid method. Must be one of: {', '.join(valid_methods)}")
    
    # Validate URL format
    if not data['url'].startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")

def check_db_integrity():
    try:
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar integridade do banco
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] != 'ok':
                logger.error("Database integrity check failed")
                # Se falhou, tentar reparar usando o backup
                
                backup_path = os.path.join(os.path.dirname(__file__), 'schedules.db.backup')
                db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
                
                if os.path.exists(backup_path):
                    os.replace(backup_path, db_path)
                    logger.info("Restored database from backup")
                else:
                    # Se não há backup, recriar o banco
                    if os.path.exists(db_path):
                        os.remove(db_path)
                    logger.info("Recreating database")
                
                # Reinicializar o banco
                init_db()
            else:
                logger.info("Database integrity check passed")
    except Exception as e:
        logger.error(f"Error checking database integrity: {str(e)}")
        # Em caso de erro, recriar o banco
        db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()

def export_db_data():
    try:
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Exportar schedules
            cursor.execute('SELECT * FROM schedules')
            schedules = [dict(row) for row in cursor.fetchall()]
            
            # Exportar executions
            cursor.execute('SELECT * FROM executions')
            executions = [dict(row) for row in cursor.fetchall()]
            
            # Salvar em arquivo JSON
            import json
            backup_data = {
                'schedules': schedules,
                'executions': executions
            }
            
            backup_file = os.path.join(os.path.dirname(__file__), 'db_backup.json')
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info("Database data exported successfully")
            return True
    except Exception as e:
        logger.error(f"Error exporting database data: {str(e)}")
        return False

def import_db_data():
    try:
        backup_file = os.path.join(os.path.dirname(__file__), 'db_backup.json')
        if not os.path.exists(backup_file):
            logger.warning("No backup file found")
            return False
        
        # Carregar dados do backup
        import json
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        with db_pool.get_connection() as conn:
            # Limpar tabelas existentes
            conn.execute('DELETE FROM executions')
            conn.execute('DELETE FROM schedules')
            
            # Importar schedules
            for schedule in backup_data.get('schedules', []):
                conn.execute('''
                    INSERT INTO schedules (id, name, cronExpression, url, method, active, createdAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    schedule['id'],
                    schedule['name'],
                    schedule['cronExpression'],
                    schedule['url'],
                    schedule['method'],
                    schedule['active'],
                    schedule['createdAt']
                ))
            
            # Importar executions
            for execution in backup_data.get('executions', []):
                conn.execute('''
                    INSERT INTO executions (id, scheduleId, scheduleName, status, response, executedAt)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    execution['id'],
                    execution['scheduleId'],
                    execution['scheduleName'],
                    execution['status'],
                    execution['response'],
                    execution['executedAt']
                ))
        
        logger.info("Database data imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing database data: {str(e)}")
        return False

def create_app():
    static_folder = os.path.join(os.path.dirname(__file__), 'frontend', 'build')
    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    CORS(app)
    
    # Exportar dados antes de verificar integridade
    export_db_data()
    
    # Verificar integridade do banco
    check_db_integrity()
    init_db()
    
    # Importar dados se necessário
    import_db_data()
    
    logger.info("Flask application created and database initialized")
    
    @app.route('/api/schedules', methods=['GET'])
    def get_schedules():
        try:
            logger.info("Fetching all schedules")
            with db_pool.get_connection() as conn:
                try:
                    cursor = conn.execute('SELECT * FROM schedules ORDER BY id DESC')
                    schedules = [dict(row) for row in cursor.fetchall()]
                    logger.info(f"Retrieved {len(schedules)} schedules successfully")
                    return jsonify(schedules)
                except sqlite3.Error as e:
                    logger.error(f"Database error while fetching schedules: {str(e)}")
                    return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Unexpected error in get_schedules: {str(e)}", exc_info=True)
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
    @app.route('/api/schedules', methods=['POST'])
    @with_retry(max_retries=3)
    def create_schedule():
        try:
            data = request.json
            logger.info(f"Creating new schedule: {data}")
            
            # Validar dados
            if not all(key in data for key in ['name', 'cronExpression', 'url', 'method']):
                return jsonify({'error': 'Missing required fields'}), 400
            
            with db_pool.get_connection() as conn:
                try:
                    cursor = conn.execute('''
                        INSERT INTO schedules (name, cronExpression, url, method, active)
                        VALUES (?, ?, ?, ?, 1)
                    ''', (data['name'], data['cronExpression'], data['url'], data['method']))
                    
                    schedule_id = cursor.lastrowid
                    schedule = {
                        'id': schedule_id,
                        'name': data['name'],
                        'cronExpression': data['cronExpression'],
                        'url': data['url'],
                        'method': data['method'],
                        'active': True
                    }
                    
                    # Adicionar ao scheduler
                    scheduler.add_job(
                        execute_request,
                        CronTrigger.from_crontab(data['cronExpression']),
                        args=[schedule],
                        id=str(schedule_id)
                    )
                    
                    logger.info(f"Schedule created successfully with ID: {schedule_id}")
                    return jsonify(schedule), 201
                    
                except Exception as e:
                    logger.error(f"Error in database operations: {str(e)}")
                    raise
                
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedules/<int:id>', methods=['PUT'])
    def update_schedule(id):
        try:
            data = request.json
            
            with db_pool.get_connection() as conn:
                # Get current schedule data
                cursor = conn.execute('SELECT * FROM schedules WHERE id = ?', (id,))
                current = cursor.fetchone()
                if not current:
                    return jsonify({'error': 'Schedule not found'}), 404
                
                current = dict(current)
                
                # Update schedule
                conn.execute('''
                    UPDATE schedules
                    SET name = ?, cronExpression = ?, url = ?, method = ?
                    WHERE id = ?
                ''', (data['name'], data['cronExpression'], data['url'], data['method'], id))
                
                # Update job in scheduler only if schedule is active
                if current['active']:
                    job_id = str(id)
                    # Remove existing job if it exists
                    if scheduler.get_job(job_id):
                        scheduler.remove_job(job_id)
                        logger.info(f"Removed existing job for schedule {id}")
                    
                    # Create new schedule object with updated data
                    schedule = {
                        'id': id,
                        'name': data['name'],
                        'cronExpression': data['cronExpression'],
                        'url': data['url'],
                        'method': data['method'],
                        'active': current['active']
                    }
                    
                    # Add new job
                    scheduler.add_job(
                        execute_request,
                        CronTrigger.from_crontab(data['cronExpression']),
                        args=[schedule],
                        id=job_id,
                        replace_existing=True
                    )
                    logger.info(f"Added updated job for schedule {id}")
                
                return jsonify({'message': 'Schedule updated successfully'})
        except Exception as e:
            logger.error(f"Error updating schedule {id}: {str(e)}")
            return jsonify({'error': f"Error updating schedule: {str(e)}"}), 500
    
    @app.route('/api/schedules/<int:id>', methods=['DELETE'])
    @with_retry(max_retries=3)
    def delete_schedule(id):
        try:
            logger.info(f"Deleting schedule with ID: {id}")
            
            # Remover o job do scheduler primeiro
            if scheduler.get_job(str(id)):
                scheduler.remove_job(str(id))
                logger.info(f"Job removed from scheduler for ID: {id}")
            
            with db_pool.get_connection() as conn:
                try:
                    # Verificar se o schedule existe
                    cursor = conn.execute('SELECT id FROM schedules WHERE id = ?', (id,))
                    if not cursor.fetchone():
                        return jsonify({'error': 'Schedule not found'}), 404
                    
                    # Remover execuções
                    conn.execute('DELETE FROM executions WHERE scheduleId = ?', (id,))
                    
                    # Remover schedule
                    conn.execute('DELETE FROM schedules WHERE id = ?', (id,))
                    
                    logger.info(f"Schedule {id} and related executions deleted successfully")
                    return jsonify({'message': 'Schedule deleted successfully'})
                    
                except Exception as e:
                    logger.error(f"Error in database operations: {str(e)}")
                    raise
                
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/executions', methods=['GET'])
    def get_executions():
        try:
            logger.info("Fetching all executions")
            with db_pool.get_connection() as conn:
                try:
                    cursor = conn.execute('SELECT * FROM executions ORDER BY executedAt DESC')
                    executions = [dict(row) for row in cursor.fetchall()]
                    logger.info(f"Retrieved {len(executions)} executions successfully")
                    return jsonify(executions)
                except sqlite3.Error as e:
                    logger.error(f"Database error while fetching executions: {str(e)}")
                    return jsonify({'error': f'Database error occurred: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in get_executions: {str(e)}", exc_info=True)
            return jsonify({'error': f'Internal server error: {str(e)}'}), 500

    @app.route('/api/schedules/<int:id>/toggle', methods=['POST'])
    def toggle_schedule(id):
        try:
            with db_pool.get_connection() as conn:
                # Get current schedule data
                cursor = conn.execute('SELECT * FROM schedules WHERE id = ?', (id,))
                schedule = cursor.fetchone()
                if not schedule:
                    return jsonify({'error': 'Schedule not found'}), 404
                
                schedule = dict(schedule)
                new_state = not schedule['active']
                
                # Update state
                conn.execute('UPDATE schedules SET active = ? WHERE id = ?', (new_state, id))
                
                # Update scheduler
                if new_state:
                    # Add to scheduler
                    scheduler.add_job(
                        execute_request,
                        CronTrigger.from_crontab(schedule['cronExpression']),
                        args=[schedule],
                        id=str(id)
                    )
                    logger.info(f"Schedule {id} activated and added to scheduler")
                else:
                    # Remove from scheduler
                    if scheduler.get_job(str(id)):
                        scheduler.remove_job(str(id))
                        logger.info(f"Schedule {id} deactivated and removed from scheduler")
                
                return jsonify({
                    'message': f"Schedule {'activated' if new_state else 'deactivated'} successfully",
                    'active': new_state
                })
                
        except Exception as e:
            logger.error(f"Error toggling schedule {id}: {str(e)}")
            return jsonify({'error': f"Error toggling schedule: {str(e)}"}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        try:
            # Verificar conexão com o banco
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT 1')
            conn.close()
            
            # Verificar scheduler
            scheduler_running = scheduler.running
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'scheduler': 'running' if scheduler_running else 'stopped'
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(static_folder, path)
    
    @app.route('/api/settings/timezone', methods=['GET', 'POST'])
    def handle_timezone():
        if request.method == 'GET':
            try:
                with db_pool.get_connection() as conn:
                    cursor = conn.execute('SELECT value FROM settings WHERE key = ?', ('timezone',))
                    result = cursor.fetchone()
                    if result:
                        return jsonify({'timezone': result['value']})
                    return jsonify({'timezone': 'UTC'})  # Valor padrão
            except Exception as e:
                logger.error(f"Error getting timezone: {str(e)}")
                return jsonify({'error': str(e)}), 500
        elif request.method == 'POST':
            try:
                data = request.get_json()
                if not data or 'timezone' not in data:
                    return jsonify({'error': 'Timezone is required'}), 400
                
                with db_pool.get_connection() as conn:
                    try:
                        conn.execute('''
                            INSERT OR REPLACE INTO settings (key, value)
                            VALUES (?, ?)
                        ''', ('timezone', data['timezone']))
                        conn.commit()  # Garantir que a transação seja commitada
                        return jsonify({'message': 'Timezone updated successfully'})
                    except Exception as e:
                        conn.rollback()  # Em caso de erro, fazer rollback
                        raise
            except Exception as e:
                logger.error(f"Error updating timezone: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedules/<int:id>/active', methods=['PATCH'])
    def patch_schedule_active(id):
        try:
            data = request.get_json()
            if 'active' not in data:
                return jsonify({'error': 'Missing "active" field'}), 400
            active = int(bool(data['active']))
            with db_pool.get_connection() as conn:
                conn.execute('UPDATE schedules SET active = ? WHERE id = ?', (active, id))
                conn.commit()
            return jsonify({'success': True, 'active': bool(active)})
        except Exception as e:
            logger.error(f"Error updating schedule active state: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # Load existing schedules when starting the app
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM schedules WHERE active = 1')
    schedules = [dict(row) for row in c.fetchall()]
    conn.close()
    
    for schedule in schedules:
        scheduler.add_job(
            execute_request,
            CronTrigger.from_crontab(schedule['cronExpression']),
            args=[schedule],
            id=str(schedule['id'])
        )
        logger.info(f"Loaded existing active schedule: {schedule['name']}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 