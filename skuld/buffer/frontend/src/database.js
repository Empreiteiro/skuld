import sqlite3 from 'sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Caminho para o arquivo do banco de dados
const dbPath = join(__dirname, 'schedules.db');

// Flag para controlar se a tabela já foi criada
let tableCreated = false;

// Criar conexão com o banco de dados
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error connecting to database:', err);
    } else {
        console.log('Connected to SQLite database');
        createTable();
    }
});

// Criar tabela de agendamentos
function createTable() {
    if (tableCreated) return Promise.resolve();
    
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            // Criar tabela de agendamentos
            db.run(`
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cronExpression TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT NOT NULL,
                    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            `, (err) => {
                if (err) {
                    console.error('Error creating schedules table:', err);
                    reject(err);
                } else {
                    if (!tableCreated) {
                        console.log('Schedules table created/verified successfully');
                    }
                }
            });

            // Criar tabela de execuções
            db.run(`
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduleId INTEGER NOT NULL,
                    scheduleName TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response TEXT,
                    executedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scheduleId) REFERENCES schedules(id)
                )
            `, (err) => {
                if (err) {
                    console.error('Error creating executions table:', err);
                    reject(err);
                } else {
                    if (!tableCreated) {
                        console.log('Executions table created/verified successfully');
                        tableCreated = true;
                    }
                    resolve();
                }
            });
        });
    });
}

// Funções para manipulação do banco de dados
const database = {
    // Inserir novo agendamento
    insertSchedule: async (schedule) => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.run(
                    'INSERT INTO schedules (name, cronExpression, url, method) VALUES (?, ?, ?, ?)',
                    [schedule.name, schedule.cronExpression, schedule.url, schedule.method],
                    function(err) {
                        if (err) {
                            reject(err);
                        } else {
                            resolve(this.lastID);
                        }
                    }
                );
            });
        } catch (error) {
            console.error('Error inserting schedule:', error);
            throw error;
        }
    },

    // Buscar todos os agendamentos
    getAllSchedules: async () => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.all('SELECT * FROM schedules', [], (err, rows) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(rows);
                    }
                });
            });
        } catch (error) {
            console.error('Error loading schedules:', error);
            throw error;
        }
    },

    // Buscar agendamento por ID
    getScheduleById: async (id) => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.get('SELECT * FROM schedules WHERE id = ?', [id], (err, row) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(row);
                    }
                });
            });
        } catch (error) {
            console.error('Error getting schedule by ID:', error);
            throw error;
        }
    },

    // Atualizar agendamento
    updateSchedule: async (id, schedule) => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.run(
                    'UPDATE schedules SET name = ?, cronExpression = ?, url = ?, method = ? WHERE id = ?',
                    [schedule.name, schedule.cronExpression, schedule.url, schedule.method, id],
                    function(err) {
                        if (err) {
                            reject(err);
                        } else {
                            resolve(this.changes);
                        }
                    }
                );
            });
        } catch (error) {
            console.error('Error updating schedule:', error);
            throw error;
        }
    },

    // Deletar agendamento
    deleteSchedule: async (id) => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.run('DELETE FROM schedules WHERE id = ?', [id], function(err) {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(this.changes);
                    }
                });
            });
        } catch (error) {
            console.error('Error deleting schedule:', error);
            throw error;
        }
    },

    // Registrar execução
    logExecution: async (scheduleId, scheduleName, status, response) => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.run(
                    'INSERT INTO executions (scheduleId, scheduleName, status, response) VALUES (?, ?, ?, ?)',
                    [scheduleId, scheduleName, status, JSON.stringify(response)],
                    function(err) {
                        if (err) {
                            reject(err);
                        } else {
                            resolve(this.lastID);
                        }
                    }
                );
            });
        } catch (error) {
            console.error('Error logging execution:', error);
            throw error;
        }
    },

    // Buscar todas as execuções
    getAllExecutions: async () => {
        try {
            await createTable();
            
            return new Promise((resolve, reject) => {
                db.all('SELECT * FROM executions ORDER BY executedAt DESC', [], (err, rows) => {
                    if (err) {
                        reject(err);
                    } else {
                        resolve(rows);
                    }
                });
            });
        } catch (error) {
            console.error('Error loading executions:', error);
            throw error;
        }
    }
};

export default database; 