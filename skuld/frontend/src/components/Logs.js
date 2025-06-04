import { DateTime } from 'luxon';
import React, { useEffect, useState } from 'react';
import './Logs.css';

function Logs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timezone, setTimezone] = useState('UTC');
    // Filtros
    const [filterStatus, setFilterStatus] = useState('');
    const [filterScheduleId, setFilterScheduleId] = useState('');
    const [filterStart, setFilterStart] = useState('');
    const [filterEnd, setFilterEnd] = useState('');

    useEffect(() => {
        fetchLogs();
        fetchTimezone();
        // Atualiza os logs a cada 30 segundos
        const interval = setInterval(fetchLogs, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchTimezone = async () => {
        try {
            const response = await fetch('/api/settings/timezone');
            const data = await response.json();
            setTimezone(data.timezone);
        } catch (error) {
            console.error('Error fetching timezone:', error);
        }
    };

    const fetchLogs = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:5000/api/executions');
            const data = await response.json();
            
            // Ordenar por scheduleId e data de execução (mais recente primeiro)
            const sortedLogs = data.sort((a, b) => {
                if (a.scheduleId !== b.scheduleId) {
                    return a.scheduleId - b.scheduleId;
                }
                return new Date(b.executedAt) - new Date(a.executedAt);
            });
            
            setLogs(sortedLogs);
            setError(null);
        } catch (error) {
            console.error('Error fetching logs:', error);
            setError('Failed to load logs. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const formatDateTime = (dateString) => {
        try {
            // SQLite armazena datas no formato YYYY-MM-DD HH:MM:SS
            const date = DateTime.fromSQL(dateString, { zone: 'utc' });
            if (!date.isValid) {
                // Se falhar, tenta o formato ISO
                const isoDate = DateTime.fromISO(dateString, { zone: 'utc' });
                if (isoDate.isValid) {
                    return isoDate.setZone(timezone).toFormat('MM/dd/yyyy HH:mm:ss ZZZZ');
                }
                throw new Error('Invalid date format');
            }
            return date.setZone(timezone).toFormat('MM/dd/yyyy HH:mm:ss ZZZZ');
        } catch (error) {
            console.error('Error formatting date:', error, 'Date string:', dateString);
            return dateString;
        }
    };

    // Função para determinar se uma linha é a primeira do seu grupo
    const isFirstInGroup = (log, index, logs) => {
        if (index === 0) return true;
        return logs[index - 1].scheduleId !== log.scheduleId;
    };

    // Função para determinar se uma linha é a última do seu grupo
    const isLastInGroup = (log, index, logs) => {
        if (index === logs.length - 1) return true;
        return logs[index + 1].scheduleId !== log.scheduleId;
    };

    // Filtro aplicado aos logs
    const filteredLogs = logs.filter(log => {
        let pass = true;
        if (filterStatus && log.status !== filterStatus) pass = false;
        if (filterScheduleId && String(log.scheduleId) !== String(filterScheduleId)) pass = false;
        if (filterStart && new Date(log.executedAt) < new Date(filterStart)) pass = false;
        if (filterEnd && new Date(log.executedAt) > new Date(filterEnd)) pass = false;
        return pass;
    });
    const sortedLogs = [...filteredLogs].sort((a, b) => new Date(b.executedAt) - new Date(a.executedAt));

    if (loading) {
        return (
            <div className="logs-container">
                <div className="loading-spinner">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="logs-container">
                <div className="error-message">{error}</div>
            </div>
        );
    }

    return (
        <div className="logs-container">
            <div className="page-header">
                <h1>Execution Logs</h1>
                <button className="refresh-button" onClick={fetchLogs}>
                    Refresh
                </button>
            </div>
            <div className="content-section logs-filters-section" style={{marginBottom: 24, padding: '16px 20px'}}>
                <form style={{display: 'flex', gap: 12, flexWrap: 'nowrap', alignItems: 'center'}}>
                    <div className="form-group" style={{minWidth: 100, flex: 1}}>
                        <label>Status
                            <select className="form-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                                <option value="">All</option>
                                <option value="success">Success</option>
                                <option value="error">Error</option>
                            </select>
                        </label>
                    </div>
                    <div className="form-group" style={{minWidth: 80, flex: 1}}>
                        <label>Schedule ID
                            <input type="number" className="form-select" value={filterScheduleId} onChange={e => setFilterScheduleId(e.target.value)} placeholder="Any" min="1" />
                        </label>
                    </div>
                    <div className="form-group" style={{minWidth: 120, flex: 1}}>
                        <label>Start Date
                            <input type="date" className="form-select" value={filterStart} onChange={e => setFilterStart(e.target.value)} />
                        </label>
                    </div>
                    <div className="form-group" style={{minWidth: 120, flex: 1}}>
                        <label>End Date
                            <input type="date" className="form-select" value={filterEnd} onChange={e => setFilterEnd(e.target.value)} />
                        </label>
                    </div>
                    <div className="form-group" style={{flex: '0 0 auto', display: 'flex', alignItems: 'center'}}>
                        <button type="button" className="refresh-button" style={{marginTop: 0, height: 40}} onClick={() => {setFilterStatus('');setFilterScheduleId('');setFilterStart('');setFilterEnd('');}}>Clear Filters</button>
                    </div>
                </form>
            </div>
            <div className="content-section">
                <div className="logs-table">
                    {logs.length === 0 ? (
                        <div className="empty-state">
                            No execution logs found. Logs will appear here when schedules are executed.
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Execution Time</th>
                                    <th>Schedule ID</th>
                                    <th>Schedule Name</th>
                                    <th>Status</th>
                                    <th>Response</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedLogs.map((log) => (
                                    <tr key={log.id}>
                                        <td>{formatDateTime(log.executedAt)}</td>
                                        <td>{log.scheduleId}</td>
                                        <td>{log.scheduleName}</td>
                                        <td>
                                            <span className={`status-badge ${log.status}`}>{log.status}</span>
                                        </td>
                                        <td>
                                            <div className="response-cell">
                                                {log.response ? (
                                                    <details>
                                                        <summary>View Response</summary>
                                                        <pre>{log.response}</pre>
                                                    </details>
                                                ) : (
                                                    <span className="no-response">No response</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Logs;