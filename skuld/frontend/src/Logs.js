import { format } from 'date-fns';
import { enUS } from 'date-fns/locale';
import React, { useEffect, useState } from 'react';
import './Logs.css';

const Logs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedResponse, setSelectedResponse] = useState(null);

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const response = await fetch('http://localhost:3001/api/executions');
            if (!response.ok) {
                throw new Error('Error loading logs');
            }
            const data = await response.json();
            setLogs(data);
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return format(new Date(dateString), 'MM/dd/yyyy HH:mm:ss', { locale: enUS });
    };

    const handleViewResponse = (response) => {
        setSelectedResponse(response);
    };

    const closeModal = () => {
        setSelectedResponse(null);
    };

    if (loading) {
        return <div className="logs-container">Loading...</div>;
    }

    if (error) {
        return <div className="logs-container">Error: {error}</div>;
    }

    if (logs.length === 0) {
        return <div className="logs-container">No logs found</div>;
    }

    return (
        <div className="logs-container">
            <h2>Execution History</h2>
            <table className="logs-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Schedule</th>
                        <th>Status</th>
                        <th>Date/Time</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {logs.map((log) => (
                        <tr key={log.id} className={log.status === 'error' ? 'error-row' : 'success-row'}>
                            <td>{log.id}</td>
                            <td>{log.scheduleId}</td>
                            <td>{log.status}</td>
                            <td>{formatDate(log.executedAt)}</td>
                            <td>
                                <button 
                                    className="view-response-btn" 
                                    onClick={() => handleViewResponse(log.response)}
                                >
                                    View Response
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {selectedResponse && (
                <div className="modal">
                    <div className="modal-content">
                        <h3>Response Details</h3>
                        <pre>{JSON.stringify(JSON.parse(selectedResponse), null, 2)}</pre>
                        <button className="close-modal-btn" onClick={closeModal}>
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Logs; 