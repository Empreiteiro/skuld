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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

def get_db():
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Habilitar foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

def init_db():
    try:
        logger.info("Initializing database...")
        conn = get_db()
        c = conn.cursor()
        
        # Create schedules table
        c.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cronExpression TEXT NOT NULL,
                url TEXT NOT NULL,
                method TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create executions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduleId INTEGER NOT NULL,
                scheduleName TEXT NOT NULL,
                status TEXT NOT NULL,
                response TEXT,
                executedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scheduleId) REFERENCES schedules(id)
            )
        ''')
        
        conn.commit()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        conn.close()

def execute_request(schedule):
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

def log_execution(schedule_id, schedule_name, status, response):
    logger.info(f"Logging execution for schedule {schedule_name} with status {status}")
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO executions (scheduleId, scheduleName, status, response)
            VALUES (?, ?, ?, ?)
        ''', (schedule_id, schedule_name, status, response))
        conn.commit()
        logger.info(f"Execution logged successfully for schedule {schedule_name}")
    except Exception as e:
        logger.error(f"Error logging execution: {str(e)}")
    finally:
        conn.close()

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
        conn = get_db()
        c = conn.cursor()
        
        # Verificar integridade do banco
        c.execute("PRAGMA integrity_check")
        result = c.fetchone()
        
        if result[0] != 'ok':
            logger.error("Database integrity check failed")
            # Se falhou, tentar reparar usando o backup
            conn.close()
            
            backup_path = os.path.join(os.path.dirname(__file__), 'schedules.db.backup')
            db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
            
            if os.path.exists(backup_path):
                os.replace(backup_path, db_path)
                logger.info("Restored database from backup")
            else:
                # Se não há backup, recriar o banco
                os.remove(db_path)
                logger.info("Recreating database")
            
            # Reinicializar o banco
            init_db()
        else:
            logger.info("Database integrity check passed")
            conn.close()
    except Exception as e:
        logger.error(f"Error checking database integrity: {str(e)}")
        # Em caso de erro, recriar o banco
        db_path = os.path.join(os.path.dirname(__file__), 'schedules.db')
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()

def export_db_data():
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Exportar schedules
        c.execute('SELECT * FROM schedules')
        schedules = [dict(row) for row in c.fetchall()]
        
        # Exportar executions
        c.execute('SELECT * FROM executions')
        executions = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
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
        
        conn = get_db()
        c = conn.cursor()
        
        # Limpar tabelas existentes
        c.execute('DELETE FROM executions')
        c.execute('DELETE FROM schedules')
        
        # Importar schedules
        for schedule in backup_data.get('schedules', []):
            c.execute('''
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
            c.execute('''
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
        
        conn.commit()
        conn.close()
        
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
            conn = get_db()
            c = conn.cursor()
            
            try:
                c.execute('SELECT * FROM schedules ORDER BY id DESC')
                schedules = [dict(row) for row in c.fetchall()]
                logger.info(f"Retrieved {len(schedules)} schedules successfully")
                return jsonify(schedules)
            except sqlite3.Error as e:
                logger.error(f"Database error while fetching schedules: {str(e)}")
                return jsonify({'error': 'Database error occurred'}), 500
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Unexpected error in get_schedules: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/schedules', methods=['POST'])
    def create_schedule():
        try:
            data = request.json
            logger.info(f"Creating new schedule: {data}")
            
            # Validate input data
            try:
                validate_schedule(data)
            except ValueError as e:
                logger.error(f"Validation error: {str(e)}")
                return jsonify({'error': str(e)}), 400
            
            # Test if we can create the cron trigger
            try:
                CronTrigger.from_crontab(data['cronExpression'])
            except Exception as e:
                logger.error(f"Invalid cron expression: {str(e)}")
                return jsonify({'error': f"Invalid cron expression: {str(e)}"}), 400
            
            conn = get_db()
            try:
                c = conn.cursor()
                
                # Start transaction
                c.execute('BEGIN')
                
                # Insert into database with active=True by default
                c.execute('''
                    INSERT INTO schedules (name, cronExpression, url, method, active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (data['name'], data['cronExpression'], data['url'], data['method']))
                schedule_id = c.lastrowid
                
                # Create schedule object
                schedule = {**data, 'id': schedule_id, 'active': True}
                
                # Try to add to scheduler
                try:
                    scheduler.add_job(
                        execute_request,
                        CronTrigger.from_crontab(data['cronExpression']),
                        args=[schedule],
                        id=str(schedule_id)
                    )
                    
                    # If successful, commit transaction
                    conn.commit()
                    logger.info(f"Schedule created successfully with ID: {schedule_id}")
                    return jsonify({'id': schedule_id}), 201
                    
                except Exception as e:
                    # If scheduler fails, rollback transaction
                    conn.rollback()
                    logger.error(f"Error adding job to scheduler: {str(e)}")
                    return jsonify({'error': f"Error creating schedule: {str(e)}"}), 500
                    
            except Exception as e:
                # If database operation fails, rollback transaction
                conn.rollback()
                logger.error(f"Database error: {str(e)}")
                return jsonify({'error': f"Database error: {str(e)}"}), 500
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Unexpected error creating schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedules/<int:id>', methods=['PUT'])
    def update_schedule(id):
        try:
            data = request.json
            conn = get_db()
            c = conn.cursor()
            
            # Get current schedule data
            c.execute('SELECT active FROM schedules WHERE id = ?', (id,))
            current = c.fetchone()
            if not current:
                conn.close()
                return jsonify({'error': 'Schedule not found'}), 404
            
            # Keep the current active state
            active = current['active']
            
            # Update schedule
            c.execute('''
                UPDATE schedules
                SET name = ?, cronExpression = ?, url = ?, method = ?, active = ?
                WHERE id = ?
            ''', (data['name'], data['cronExpression'], data['url'], data['method'], active, id))
            conn.commit()
            
            # Update job in scheduler if schedule is active
            if active:
                if scheduler.get_job(str(id)):
                    scheduler.remove_job(str(id))
            
            schedule = {**data, 'id': id, 'active': active}
            scheduler.add_job(
                execute_request,
                CronTrigger.from_crontab(data['cronExpression']),
                args=[schedule],
                id=str(id)
            )
            
            conn.close()
            return jsonify({'message': 'Schedule updated successfully'})
        except Exception as e:
            logger.error(f"Error updating schedule {id}: {str(e)}")
            return jsonify({'error': f"Error updating schedule: {str(e)}"}), 500
    
    @app.route('/api/schedules/<int:id>', methods=['DELETE'])
    def delete_schedule(id):
        try:
            logger.info(f"Deleting schedule with ID: {id}")
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM schedules WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            
            # Remove job from scheduler
            if scheduler.get_job(str(id)):
                scheduler.remove_job(str(id))
                logger.info(f"Job removed from scheduler for ID: {id}")
            
            return jsonify({'message': 'Schedule deleted successfully'})
        except Exception as e:
            logger.error(f"Error deleting schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/executions', methods=['GET'])
    def get_executions():
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM executions ORDER BY executedAt DESC')
            executions = [dict(row) for row in c.fetchall()]
            conn.close()
            logger.info(f"Retrieved {len(executions)} executions")
            return jsonify(executions)
        except Exception as e:
            logger.error(f"Error getting executions: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/schedules/<int:id>/toggle', methods=['POST'])
    def toggle_schedule(id):
        try:
            conn = get_db()
            c = conn.cursor()
            
            # Get current schedule data
            c.execute('SELECT * FROM schedules WHERE id = ?', (id,))
            schedule = c.fetchone()
            if not schedule:
                conn.close()
                return jsonify({'error': 'Schedule not found'}), 404
            
            schedule = dict(schedule)
            new_state = not schedule['active']
            
            # Update state
            c.execute('UPDATE schedules SET active = ? WHERE id = ?', (new_state, id))
            conn.commit()
            
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
            
            conn.close()
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