import React, { useEffect, useState } from 'react';
import './Schedules.css';

function ExistingSchedules() {
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/schedules');
            const data = await response.json();
            setSchedules(data);
            setError(null);
        } catch (error) {
            console.error('Error fetching schedules:', error);
            setError('Failed to load schedules. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this schedule?')) {
            return;
        }

        try {
            const response = await fetch(`/api/schedules/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await fetchSchedules();
            } else {
                const data = await response.json();
                setError(data.error || 'Failed to delete schedule');
            }
        } catch (error) {
            console.error('Error deleting schedule:', error);
            setError('Error deleting schedule. Please try again.');
        }
    };

    const handleToggle = async (id, currentState) => {
        try {
            const response = await fetch(`/api/schedules/${id}/toggle`, {
                method: 'POST'
            });

            if (response.ok) {
                await fetchSchedules();
            } else {
                const data = await response.json();
                setError(data.error || `Failed to ${currentState ? 'deactivate' : 'activate'} schedule`);
            }
        } catch (error) {
            console.error('Error toggling schedule:', error);
            setError('Error updating schedule status. Please try again.');
        }
    };

    if (loading) {
        return (
            <div className="schedules-container">
                <div className="loading-spinner">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="schedules-container">
                <div className="error-message">{error}</div>
            </div>
        );
    }

    return (
        <div className="schedules-container">
            <div className="page-header">
                <h1>Existing Schedules</h1>
            </div>

            <div className="content-section">
                <div className="schedules-table">
                    {schedules.length === 0 ? (
                        <div className="empty-state">
                            No schedules found. Create your first schedule to get started.
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Description</th>
                                    <th>URL</th>
                                    <th>Cron Expression</th>
                                    <th>Method</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {schedules.map((schedule) => (
                                    <tr key={schedule.id}>
                                        <td>{schedule.name}</td>
                                        <td>{schedule.description}</td>
                                        <td>{schedule.url}</td>
                                        <td>{schedule.cronExpression}</td>
                                        <td>{schedule.method}</td>
                                        <td>
                                            <button
                                                className={`status-badge ${schedule.active ? 'active' : 'inactive'}`}
                                                onClick={() => handleToggle(schedule.id, schedule.active)}
                                            >
                                                {schedule.active ? 'Active' : 'Inactive'}
                                            </button>
                                        </td>
                                        <td>
                                            <button
                                                className="delete-button"
                                                onClick={() => handleDelete(schedule.id)}
                                                title="Delete Schedule"
                                            >
                                                Delete
                                            </button>
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

export default ExistingSchedules; 