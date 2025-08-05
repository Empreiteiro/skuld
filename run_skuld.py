#!/usr/bin/env python3
"""
Script para executar o Skuld diretamente
"""

import sys
import os
import sqlite3
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
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

# Connection pool
class DatabaseConnectionPool:
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self.thread_local = threading.local()
        
        # Initialize pool with connections
        for _ in range(max_connections):
            self.connections.put(self._create_connection())
    
    def _create_connection(self):
        db_path = os.path.join('skuld', 'schedules.db')
        conn = sqlite3.connect(
            db_path,
            timeout=60.0,
            isolation_level=None,
            check_same_thread=False
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
            connection = self.connections.get(timeout=10)
            yield connection
        finally:
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    connection = self._create_connection()
                finally:
                    self.connections.put(connection)

# Create global pool
db_pool = DatabaseConnectionPool()

def init_db():
    try:
        logger.info("Initializing database...")
        with db_pool.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    cronExpression TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT NOT NULL,
                    headers TEXT,
                    body TEXT,
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
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Initialize database
    init_db()
    
    @app.route('/api/schedules', methods=['GET'])
    def get_schedules():
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM schedules ORDER BY id DESC')
                schedules = [dict(row) for row in cursor.fetchall()]
                return jsonify(schedules)
        except Exception as e:
            logger.error(f"Error fetching schedules: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/schedules', methods=['POST'])
    def create_schedule():
        try:
            data = request.get_json()
            required_fields = ['name', 'url', 'cronExpression', 'method']
            
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            with db_pool.get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO schedules (name, description, url, cronExpression, method, headers, body)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['name'],
                    data.get('description', ''),
                    data['url'],
                    data['cronExpression'],
                    data['method'],
                    data.get('headers', ''),
                    data.get('body', '')
                ))
                conn.commit()
                
                schedule_id = cursor.lastrowid
                logger.info(f"Created schedule with ID: {schedule_id}")
                
                return jsonify({'message': 'Schedule created successfully', 'id': schedule_id}), 201
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/executions', methods=['GET'])
    def get_executions():
        try:
            with db_pool.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM executions ORDER BY executedAt DESC')
                executions = [dict(row) for row in cursor.fetchall()]
                return jsonify(executions if executions else [])
        except Exception as e:
            logger.error(f"Error fetching executions: {str(e)}")
            return jsonify([]), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'scheduler': 'running' if scheduler.running else 'stopped'
        })
    
    # Serve React app
    @app.route('/')
    def serve_react():
        return send_from_directory('skuld/frontend/build', 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        if path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return send_from_directory('skuld/frontend/build', path)
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("Starting Skuld server on http://localhost:8000")
    app.run(host='localhost', port=8000, debug=True) 