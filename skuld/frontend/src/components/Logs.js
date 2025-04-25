import React, { useEffect, useState } from 'react';
import './Logs.css';

function Logs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchLogs();
        // Atualiza os logs a cada 30 segundos
        const interval = setInterval(fetchLogs, 30000);
        return () => clearInterval(interval);
    }, []);

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
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        return new Date(dateString).toLocaleString(undefined, options);
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
                                {logs.map((log, index, logsArray) => (
                                    <tr 
                                        key={log.id}
                                        className={`
                                            ${isFirstInGroup(log, index, logsArray) ? 'group-start' : ''}
                                            ${isLastInGroup(log, index, logsArray) ? 'group-end' : ''}
                                        `}
                                    >
                                        <td>{formatDateTime(log.executedAt)}</td>
                                        <td>{log.scheduleId}</td>
                                        <td>{log.scheduleName}</td>
                                        <td>
                                            <span className={`status-badge ${log.status}`}>
                                                {log.status}
                                            </span>
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