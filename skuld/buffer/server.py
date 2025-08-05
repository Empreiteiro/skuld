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
import json

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
                        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS buffer_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        filter_field TEXT NOT NULL,
                        max_size INTEGER NOT NULL DEFAULT 10,
                        max_time INTEGER NOT NULL DEFAULT 60,
                        reset_timer_on_message BOOLEAN NOT NULL DEFAULT 0,
                        active BOOLEAN NOT NULL DEFAULT 1,
                        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS forwarding_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        buffer_config_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        method TEXT NOT NULL DEFAULT 'POST',
                        headers TEXT,
                        fields TEXT,
                        active BOOLEAN NOT NULL DEFAULT 1,
                        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (buffer_config_id) REFERENCES buffer_configs(id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS received_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_data TEXT NOT NULL,
                        source TEXT NOT NULL,
                        received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        processed BOOLEAN NOT NULL DEFAULT 0
                    );
                    CREATE TABLE IF NOT EXISTS forwarded_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        received_message_id INTEGER NOT NULL,
                        forwarding_config_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        response TEXT,
                        forwarded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (received_message_id) 
                            REFERENCES received_messages(id) 
                            ON DELETE CASCADE,
                        FOREIGN KEY (forwarding_config_id) 
                            REFERENCES forwarding_configs(id) 
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
                
                # Verificar se as colunas existem
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(schedules)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Adicionar coluna active se não existir
                if 'active' not in column_names:
                    logger.info("Adding active column to schedules table...")
                    conn.execute('ALTER TABLE schedules ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1')
                    logger.info("Active column added successfully")
                
                # Adicionar colunas headers e body se não existirem
                if 'headers' not in column_names:
                    logger.info("Adding headers column to schedules table...")
                    conn.execute('ALTER TABLE schedules ADD COLUMN headers TEXT')
                    logger.info("Headers column added successfully")
                
                if 'body' not in column_names:
                    logger.info("Adding body column to schedules table...")
                    conn.execute('ALTER TABLE schedules ADD COLUMN body TEXT')
                    logger.info("Body column added successfully")
                
                # Verificar se o banco está acessível
                cursor.execute("SELECT COUNT(*) FROM schedules")
                count = cursor.fetchone()[0]
                logger.info(f"Database is accessible. Found {count} schedules.")
                
                # Verificar se as colunas existem em forwarding_configs
                cursor.execute("PRAGMA table_info(forwarding_configs)")
                fwd_columns = cursor.fetchall()
                fwd_column_names = [col[1] for col in fwd_columns]
                if 'buffer_config_id' not in fwd_column_names:
                    logger.info("Adding buffer_config_id column to forwarding_configs table...")
                    conn.execute('ALTER TABLE forwarding_configs ADD COLUMN buffer_config_id INTEGER REFERENCES buffer_configs(id) ON DELETE CASCADE')
                    logger.info("buffer_config_id column added successfully")
                if 'fields' not in fwd_column_names:
                    logger.info("Adding fields column to forwarding_configs table...")
                    conn.execute('ALTER TABLE forwarding_configs ADD COLUMN fields TEXT')
                    logger.info("fields column added successfully")
                
                # Verificar se as colunas existem em buffer_configs
                cursor.execute("PRAGMA table_info(buffer_configs)")
                buf_columns = cursor.fetchall()
                buf_column_names = [col[1] for col in buf_columns]
                if 'max_size' not in buf_column_names:
                    logger.info("Adding max_size column to buffer_configs table...")
                    conn.execute('ALTER TABLE buffer_configs ADD COLUMN max_size INTEGER NOT NULL DEFAULT 10')
                    logger.info("max_size column added successfully")
                if 'max_time' not in buf_column_names:
                    logger.info("Adding max_time column to buffer_configs table...")
                    conn.execute('ALTER TABLE buffer_configs ADD COLUMN max_time INTEGER NOT NULL DEFAULT 60')
                    logger.info("max_time column added successfully")
                if 'reset_timer_on_message' not in buf_column_names:
                    logger.info("Adding reset_timer_on_message column to buffer_configs table...")
                    conn.execute('ALTER TABLE buffer_configs ADD COLUMN reset_timer_on_message BOOLEAN NOT NULL DEFAULT 0')
                    logger.info("reset_timer_on_message column added successfully")
                
                # Adicionar coluna buffer_id em received_messages se não existir
                cursor.execute("PRAGMA table_info(received_messages)")
                rm_columns = cursor.fetchall()
                rm_column_names = [col[1] for col in rm_columns]
                if 'buffer_id' not in rm_column_names:
                    logger.info("Adding buffer_id column to received_messages table...")
                    conn.execute('ALTER TABLE received_messages ADD COLUMN buffer_id INTEGER')
                    logger.info("buffer_id column added successfully")
                
                # Adicionar coluna forwarded_id em received_messages se não existir
                if 'forwarded_id' not in rm_column_names:
                    logger.info("Adding forwarded_id column to received_messages table...")
                    conn.execute('ALTER TABLE received_messages ADD COLUMN forwarded_id INTEGER')
                    logger.info("forwarded_id column added successfully")
                
                # Adicionar coluna template em forwarding_configs se não existir
                if 'template' not in fwd_column_names:
                    logger.info("Adding template column to forwarding_configs table...")
                    conn.execute('ALTER TABLE forwarding_configs ADD COLUMN template TEXT')
                    logger.info("template column added successfully")
                
                # Adicionar coluna status em received_messages se não existir
                if 'status' not in rm_column_names:
                    logger.info("Adding status column to received_messages table...")
                    conn.execute('ALTER TABLE received_messages ADD COLUMN status TEXT')
                    logger.info("status column added successfully")
                
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
            # Preparar headers
            headers = {}
            if schedule.get('headers'):
                try:
                    headers = json.loads(schedule['headers'])
                except json.JSONDecodeError:
                    logger.error(f"Invalid headers JSON for schedule {schedule['name']}")
                    headers = {}

            # Preparar body
            body = None
            if schedule.get('body'):
                try:
                    body = json.loads(schedule['body'])
                except json.JSONDecodeError:
                    logger.error(f"Invalid body JSON for schedule {schedule['name']}")
                    body = schedule['body']

            response = requests.request(
                method=schedule['method'],
                url=schedule['url'],
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) else None,
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
                    SET name = ?, cronExpression = ?, url = ?, method = ?, headers = ?, body = ?
                    WHERE id = ?
                ''', (
                    data['name'],
                    data['cronExpression'],
                    data['url'],
                    data['method'],
                    data.get('headers', ''),
                    data.get('body', ''),
                    id
                ))
                
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
                        'headers': data.get('headers', ''),
                        'body': data.get('body', ''),
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
    
    # Webhook endpoint to receive messages
    @app.route('/api/webhook', methods=['POST'])
    def receive_message():
        return jsonify({'error': 'Use /api/webhook/<buffer_id> to send messages to a buffer.'}), 400

    # Webhook endpoint to receive messages for a specific buffer config
    @app.route('/api/webhook/<int:buffer_id>', methods=['POST'])
    def receive_message_for_buffer(buffer_id):
        try:
            message_data = request.get_json()
            if not message_data:
                return jsonify({'error': 'No message data provided'}), 400

            with db_pool.get_connection() as conn:
                # Check if buffer config exists and is active
                cursor = conn.execute('SELECT * FROM buffer_configs WHERE id = ? AND active = 1', (buffer_id,))
                buffer_config = cursor.fetchone()
                if not buffer_config:
                    return jsonify({'error': 'Buffer config not found or inactive'}), 404
                buffer_config = dict(buffer_config)
                key_field = buffer_config['filter_field']
                max_size = buffer_config['max_size']
                max_time = buffer_config['max_time']
                if key_field not in message_data:
                    return jsonify({'error': f'Message missing key field: {key_field}'}), 400
                key_value = str(message_data[key_field])
                # Store the message with buffer_id
                cursor = conn.execute(
                    'INSERT INTO received_messages (message_data, source, buffer_id) VALUES (?, ?, ?)',
                    (json.dumps(message_data), request.remote_addr, buffer_id)
                )
                message_id = cursor.lastrowid
                conn.commit()
            # Buffer the message
            buffer_message(buffer_id, key_value, message_id, message_data, max_size, max_time)
            return jsonify({'status': 'buffered', 'message_id': message_id}), 201
        except Exception as e:
            logger.error(f"Error receiving message for buffer {buffer_id}: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Buffer configuration endpoints
    @app.route('/api/buffer-configs', methods=['GET'])
    def get_buffer_configs():
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM buffer_configs ORDER BY createdAt DESC')
                configs = [dict(row) for row in cursor.fetchall()]
                return jsonify(configs)
        except Exception as e:
            logger.error(f"Error getting buffer configs: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/buffer-configs', methods=['POST'])
    def create_buffer_config():
        try:
            data = request.get_json()
            required_fields = ['name', 'filter_field']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400

            with db_pool.get_connection() as conn:
                cursor = conn.execute(
                    '''INSERT INTO buffer_configs 
                       (name, filter_field, max_size, max_time, reset_timer_on_message) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (data['name'], data['filter_field'], 
                     data.get('max_size', 10), data.get('max_time', 60),
                     int(data.get('reset_timer_on_message', False)))
                )
                config_id = cursor.lastrowid
                conn.commit()
                return jsonify({'id': config_id, 'status': 'success'}), 201
        except Exception as e:
            logger.error(f"Error creating buffer config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/buffer-configs/<int:id>', methods=['PUT'])
    def update_buffer_config(id):
        try:
            data = request.get_json()
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM buffer_configs WHERE id = ?', (id,))
                config = cursor.fetchone()
                if not config:
                    return jsonify({'error': 'Buffer config not found'}), 404
                config = dict(config)
                name = data.get('name', config.get('name', ''))
                filter_field = data.get('filter_field', config.get('filter_field', ''))
                max_size = data.get('max_size', config.get('max_size', 10))
                max_time = data.get('max_time', config.get('max_time', 60))
                reset_timer_on_message = int(data.get('reset_timer_on_message', config.get('reset_timer_on_message', 0)))
                conn.execute('''
                    UPDATE buffer_configs
                    SET name = ?, filter_field = ?, max_size = ?, max_time = ?, reset_timer_on_message = ?
                    WHERE id = ?
                ''', (
                    name,
                    filter_field,
                    max_size,
                    max_time,
                    reset_timer_on_message,
                    id
                ))
                conn.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            logger.error(f"Error updating buffer config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/buffer-configs/<int:id>', methods=['DELETE'])
    def delete_buffer_config(id):
        try:
            with db_pool.get_connection() as conn:
                conn.execute('DELETE FROM buffer_configs WHERE id = ?', (id,))
                conn.commit()
            return jsonify({'status': 'deleted'}), 200
        except Exception as e:
            logger.error(f"Error deleting buffer config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Forwarding configuration endpoints
    @app.route('/api/forwarding-configs', methods=['GET'])
    def get_forwarding_configs():
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM forwarding_configs ORDER BY createdAt DESC')
                configs = [dict(row) for row in cursor.fetchall()]
                return jsonify(configs)
        except Exception as e:
            logger.error(f"Error getting forwarding configs: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/forwarding-configs', methods=['POST'])
    def create_forwarding_config():
        try:
            data = request.get_json()
            required_fields = ['name', 'url', 'buffer_config_id']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400

            with db_pool.get_connection() as conn:
                cursor = conn.execute(
                    '''INSERT INTO forwarding_configs 
                       (name, url, method, headers, buffer_config_id, fields, template) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (data['name'], data['url'], 
                     data.get('method', 'POST'),
                     json.dumps(data.get('headers', {})),
                     data['buffer_config_id'],
                     ','.join(data.get('fields', [])) if isinstance(data.get('fields', []), list) else (data.get('fields') or ''),
                     data.get('template', ''))
                )
                config_id = cursor.lastrowid
                conn.commit()
                return jsonify({'id': config_id, 'status': 'success'}), 201
        except Exception as e:
            logger.error(f"Error creating forwarding config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/forwarding-configs/<int:id>', methods=['PUT'])
    def update_forwarding_config(id):
        try:
            data = request.get_json()
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM forwarding_configs WHERE id = ?', (id,))
                config = cursor.fetchone()
                if not config:
                    return jsonify({'error': 'Forwarding config not found'}), 404
                config = dict(config)
                name = data.get('name', config.get('name', ''))
                url = data.get('url', config.get('url', ''))
                method = data.get('method', config.get('method', 'POST'))
                headers = json.dumps(data.get('headers', json.loads(config.get('headers', '{}'))))
                buffer_config_id = data.get('buffer_config_id', config.get('buffer_config_id'))
                fields = data.get('fields', config.get('fields', ''))
                template = data.get('template', config.get('template', ''))
                active = int(data.get('active', config.get('active', 1)))
                conn.execute('''
                    UPDATE forwarding_configs
                    SET name = ?, url = ?, method = ?, headers = ?, buffer_config_id = ?, fields = ?, template = ?, active = ?
                    WHERE id = ?
                ''', (
                    name, url, method, headers, buffer_config_id, fields, template, active, id
                ))
                conn.commit()
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            logger.error(f"Error updating forwarding config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/forwarding-configs/<int:id>', methods=['DELETE'])
    def delete_forwarding_config(id):
        try:
            with db_pool.get_connection() as conn:
                conn.execute('DELETE FROM forwarding_configs WHERE id = ?', (id,))
                conn.commit()
            return jsonify({'status': 'deleted'}), 200
        except Exception as e:
            logger.error(f"Error deleting forwarding config: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Message history endpoints
    @app.route('/api/messages/received', methods=['GET'])
    def get_received_messages():
        try:
            with db_pool.get_connection() as conn:
                # Adicionar forwarded_id ao select se existir
                cursor = conn.execute('''
                    SELECT *, (SELECT id FROM forwarded_messages WHERE received_message_id = received_messages.id ORDER BY id DESC LIMIT 1) as forwarded_id
                    FROM received_messages 
                    ORDER BY received_at DESC 
                    LIMIT 100
                ''')
                messages = [dict(row) for row in cursor.fetchall()]
                return jsonify(messages)
        except Exception as e:
            logger.error(f"Error getting received messages: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/messages/forwarded', methods=['GET'])
    def get_forwarded_messages():
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT fm.*, fc.name as forwarding_config_name 
                    FROM forwarded_messages fm
                    JOIN forwarding_configs fc ON fm.forwarding_config_id = fc.id
                    ORDER BY fm.forwarded_at DESC 
                    LIMIT 100
                ''')
                messages = [dict(row) for row in cursor.fetchall()]
                return jsonify(messages)
        except Exception as e:
            logger.error(f"Error getting forwarded messages: {str(e)}")
            return jsonify({'error': str(e)}), 500

    import threading
    buffer_store = {}
    buffer_timers = {}
    buffer_lock = threading.Lock()

    def flush_buffer(buffer_id, key_value):
        logger.info(f"[FLUSH] Disparando flush_buffer para buffer_id={buffer_id}, key_value={key_value}")
        with buffer_lock:
            buffer_key = (buffer_id, key_value)
            messages = buffer_store.pop(buffer_key, [])
            timer = buffer_timers.pop(buffer_key, None)
            
            if not messages:
                logger.info(f"[FLUSH] Nenhuma mensagem para encaminhar em buffer_id={buffer_id}, key_value={key_value}")
                return
                
            if timer:
                logger.info(f"[FLUSH] Cancelando timer para buffer_id={buffer_id}, key_value={key_value}")
                timer.cancel()
            
            logger.info(f"[FLUSH] Encaminhando {len(messages)} mensagens para buffer_id={buffer_id}, key_value={key_value}")
            try:
                with db_pool.get_connection() as conn:
                    # Get active forwarding configs for this buffer
                    cursor = conn.execute('SELECT * FROM forwarding_configs WHERE active = 1 AND buffer_config_id = ?', (buffer_id,))
                    forwarding_configs = [dict(row) for row in cursor.fetchall()]
                    if not forwarding_configs:
                        # Nenhuma regra de encaminhamento: marcar como cancelada
                        for msg in messages:
                            conn.execute('UPDATE received_messages SET processed = 1, status = ? WHERE id = ?', ('cancelled', msg['message_id']))
                        conn.commit()
                        logger.info(f"[FLUSH] Nenhuma regra de encaminhamento ativa para buffer_id={buffer_id}. Mensagens marcadas como canceladas.")
                        return

                    # Para cada regra de encaminhamento ativa
                    for fw_config in forwarding_configs:
                        try:
                            headers = json.loads(fw_config['headers']) if fw_config['headers'] else {}
                            # Obter o campo-chave
                            cursor2 = conn.execute('SELECT filter_field FROM buffer_configs WHERE id = ?', (buffer_id,))
                            row2 = cursor2.fetchone()
                            key_field = row2['filter_field'] if row2 else None
                            key_value = messages[0]['data'][key_field] if key_field else None
                            if fw_config['template'] and key_field:
                                # Usar template para o valor de cada mensagem
                                template = fw_config['template']
                                content_list = []
                                for msg in messages:
                                    data = msg['data']
                                    msg_payload = template
                                    for k, v in data.items():
                                        msg_payload = msg_payload.replace(f'{{{{{k}}}}}', str(v))
                                    # O resultado do template é o valor do array
                                    try:
                                        rendered = json.loads(msg_payload)
                                    except Exception:
                                        rendered = msg_payload
                                    content_list.append(rendered)
                                payload = {key_field: key_value, 'content': content_list}
                            elif key_field:
                                # Sem template: pegar o campo conteudo de cada mensagem
                                content_list = [msg['data'].get('conteudo') for msg in messages]
                                payload = {key_field: key_value, 'content': content_list}
                            else:
                                # fallback
                                to_forward = [msg['data'] for msg in messages]
                                payload = {'content': to_forward}

                            logger.info(f"[FLUSH] Enviando para {fw_config['url']} com payload: {json.dumps(payload)}")
                            response = requests.request(
                                method=fw_config['method'],
                                url=fw_config['url'],
                                json=payload,
                                headers=headers
                            )
                            # Salvar o payload enviado e a resposta real
                            response_text = json.dumps({
                                'sent': {
                                    'payload': payload,
                                    'headers': headers
                                },
                                'response': {
                                    'status_code': response.status_code,
                                    'text': response.text
                                }
                            })
                            
                            # Criar apenas um registro em forwarded_messages para o grupo
                            cursor_fwd = conn.execute(
                                '''INSERT INTO forwarded_messages 
                                   (received_message_id, forwarding_config_id, status, response) 
                                   VALUES (?, ?, ?, ?)''',
                                (messages[0]['message_id'], fw_config['id'], 'success' if response.ok else 'error', response_text)
                            )
                            forwarded_id = cursor_fwd.lastrowid
                            
                            # Atualizar todas as mensagens recebidas do grupo
                            for msg in messages:
                                conn.execute('UPDATE received_messages SET processed = 1, forwarded_id = ?, status = ? WHERE id = ?', 
                                           (forwarded_id, 'success' if response.ok else 'error', msg['message_id']))
                            
                            conn.commit()
                            logger.info(f"[FLUSH] Mensagens encaminhadas com sucesso para {fw_config['url']}")
                            
                        except Exception as e:
                            logger.error(f"[FLUSH] Erro ao encaminhar mensagens para {fw_config['url']}: {str(e)}")
                            # Marcar mensagens como erro
                            for msg in messages:
                                conn.execute('UPDATE received_messages SET processed = 1, status = ? WHERE id = ?', ('error', msg['message_id']))
                            conn.commit()
                            
            except Exception as e:
                logger.error(f"[FLUSH] Erro ao processar mensagens: {str(e)}")
                # Marcar mensagens como erro
                try:
                    with db_pool.get_connection() as conn:
                        for msg in messages:
                            conn.execute('UPDATE received_messages SET processed = 1, status = ? WHERE id = ?', ('error', msg['message_id']))
                        conn.commit()
                except Exception as db_error:
                    logger.error(f"[FLUSH] Erro ao marcar mensagens como erro: {str(db_error)}")

    def buffer_message(buffer_id, key_value, message_id, message_data, max_size, max_time):
        buffer_key = (buffer_id, key_value)
        with buffer_lock:
            if buffer_key not in buffer_store:
                buffer_store[buffer_key] = []
            buffer_store[buffer_key].append({'message_id': message_id, 'data': message_data})
            logger.info(f"[BUFFER] Mensagem adicionada ao buffer_id={buffer_id}, key_value={key_value}. Total: {len(buffer_store[buffer_key])}")
            
            # Verificar se deve resetar o timer
            should_reset_timer = False
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT reset_timer_on_message FROM buffer_configs WHERE id = ?', (buffer_id,))
                config = cursor.fetchone()
                if config:
                    should_reset_timer = bool(config['reset_timer_on_message'])
            
            # Se deve resetar o timer ou não existe timer, criar um novo
            if should_reset_timer or buffer_key not in buffer_timers:
                if buffer_key in buffer_timers:
                    logger.info(f"[TIMER] Cancelando timer existente para buffer_id={buffer_id}, key_value={key_value}")
                    buffer_timers[buffer_key].cancel()
                logger.info(f"[TIMER] Iniciando novo timer de {max_time}s para buffer_id={buffer_id}, key_value={key_value}")
                timer = threading.Timer(max_time, flush_buffer, args=(buffer_id, key_value))
                buffer_timers[buffer_key] = timer
                timer.start()
            
            # Check if buffer is full
            if len(buffer_store[buffer_key]) >= max_size:
                logger.info(f"[FLUSH] Buffer cheio para buffer_id={buffer_id}, key_value={key_value}. Disparando flush_buffer.")
                flush_buffer(buffer_id, key_value)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 