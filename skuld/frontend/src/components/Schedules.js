import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Schedules.css';

const EditIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" fill="none"/>
    <path stroke="currentColor" strokeWidth="2" fill="none"
      d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 8.6 15a1.65 1.65 0 0 0-1.82-.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 15 8.6a1.65 1.65 0 0 0 1.82.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 15z"
    />
  </svg>
);

const TrashIcon = () => (
  <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2" /></svg>
);

function Schedules() {
    const navigate = useNavigate();
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/schedules');
            const data = await response.json();
            setSchedules(data);
            setError(null);
        } catch (err) {
            setError('Failed to load schedules.');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActive = async (id, currentActive) => {
        try {
            await fetch(`http://localhost:5000/api/schedules/${id}/active`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: !currentActive })
            });
            fetchSchedules();
        } catch (err) {
            alert('Failed to update schedule status.');
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this schedule?')) return;
        try {
            await fetch(`http://localhost:5000/api/schedules/${id}`, {
                method: 'DELETE'
            });
            fetchSchedules();
        } catch (err) {
            alert('Failed to delete schedule.');
        }
    };

    const handleDuplicate = async (sch) => {
        const newSchedule = {
            ...sch,
            name: `Copy of ${sch.name}`,
        };
        // Remove id from the new schedule
        delete newSchedule.id;
        try {
            await fetch('http://localhost:5000/api/schedules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSchedule)
            });
            fetchSchedules();
        } catch (err) {
            alert('Failed to duplicate schedule.');
        }
    };

    return (
        <div className="schedules-container">
            <div className="page-header">
                <h1>Schedules</h1>
                <button 
                    className="create-button"
                    onClick={() => navigate('/schedules/new')}
                >
                    Create New Schedule
                </button>
            </div>
            <div className="content-section">
                {loading && <div>Loading schedules...</div>}
                {error && <div className="feedback-message error">{error}</div>}
                {!loading && !error && (
                    <table className="schedules-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>URL</th>
                                <th>Cron</th>
                                <th>Method</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {schedules.map(sch => (
                                <tr key={sch.id}>
                                    <td>{sch.id}</td>
                                    <td>{sch.name}</td>
                                    <td>{sch.url}</td>
                                    <td>{sch.cronExpression}</td>
                                    <td>{sch.method}</td>
                                    <td>
                                        <button 
                                            className={sch.active ? 'active-btn' : 'inactive-btn'}
                                            style={{
                                                backgroundColor: sch.active ? '#28a745' : '#dc3545',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                padding: '4px 12px',
                                                fontWeight: 600
                                            }}
                                            onClick={() => handleToggleActive(sch.id, sch.active)}
                                        >
                                            {sch.active ? 'Active' : 'Inactive'}
                                        </button>
                                    </td>
                                    <td>
                                        <button onClick={() => navigate(`/schedules/edit/${sch.id}`)} className="icon-btn" title="Edit">
                                            <span role="img" aria-label="edit">📝</span>
                                        </button>
                                        <button onClick={() => handleDuplicate(sch)} className="icon-btn" title="Duplicate">
                                            <span role="img" aria-label="duplicate">📄</span>
                                        </button>
                                        <button onClick={() => handleDelete(sch.id)} className="icon-btn" title="Delete">
                                            <span role="img" aria-label="delete">🗑️</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}

export default Schedules; 