import React, { useEffect, useState } from 'react';
import './Schedules.css';

const Schedules = () => {
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        cronExpression: '',
        url: '',
        method: 'GET'
    });

    const cronPatterns = [
        { label: 'Select a pattern...', value: '' },
        { label: 'Every minute', value: '* * * * *' },
        { label: 'Every 5 minutes', value: '*/5 * * * *' },
        { label: 'Every 15 minutes', value: '*/15 * * * *' },
        { label: 'Every 30 minutes', value: '*/30 * * * *' },
        { label: 'Every hour', value: '0 * * * *' },
        { label: 'Every day at midnight', value: '0 0 * * *' },
        { label: 'Every Sunday at midnight', value: '0 0 * * 0' },
        { label: 'Every month on the 1st at midnight', value: '0 0 1 * *' }
    ];

    useEffect(() => {
        loadSchedules();
    }, []);

    const loadSchedules = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/schedules');
            if (!response.ok) {
                throw new Error('Error loading schedules');
            }
            const data = await response.json();
            setSchedules(data);
            setLoading(false);
        } catch (err) {
            setError(err.message);
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:5000/api/schedules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                throw new Error('Error creating schedule');
            }

            await loadSchedules();
            setFormData({
                name: '',
                cronExpression: '',
                url: '',
                method: 'GET'
            });
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDelete = async (id) => {
        try {
            const response = await fetch(`http://localhost:5000/api/schedules/${id}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Error deleting schedule');
            }

            await loadSchedules();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleCronPatternChange = (e) => {
        const selectedPattern = e.target.value;
        setFormData(prev => ({
            ...prev,
            cronExpression: selectedPattern
        }));
    };

    if (loading) {
        return <div className="schedules-container">Loading...</div>;
    }

    if (error) {
        return <div className="schedules-container">Error: {error}</div>;
    }

    return (
        <div className="schedules-container">
            <h2>New Schedule</h2>
            <form onSubmit={handleSubmit} className="schedule-form">
                <div className="form-group">
                    <label htmlFor="name">Name:</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="cronPattern">Cron Pattern:</label>
                    <select
                        id="cronPattern"
                        value={formData.cronExpression}
                        onChange={handleCronPatternChange}
                        className="cron-pattern-select"
                    >
                        {cronPatterns.map((pattern, index) => (
                            <option key={index} value={pattern.value}>
                                {pattern.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="cronExpression">Custom Cron Expression:</label>
                    <input
                        type="text"
                        id="cronExpression"
                        name="cronExpression"
                        value={formData.cronExpression}
                        onChange={handleInputChange}
                        required
                        placeholder="*/5 * * * *"
                    />
                    <small>Example: */5 * * * * (every 5 minutes)</small>
                </div>

                <div className="form-group">
                    <label htmlFor="url">URL:</label>
                    <input
                        type="url"
                        id="url"
                        name="url"
                        value={formData.url}
                        onChange={handleInputChange}
                        required
                        placeholder="https://api.example.com"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="method">Method:</label>
                    <select
                        id="method"
                        name="method"
                        value={formData.method}
                        onChange={handleInputChange}
                        required
                    >
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                </div>

                <button type="submit" className="submit-btn">Create Schedule</button>
            </form>

            <h2>Existing Schedules</h2>
            <div className="schedules-list">
                {schedules.length === 0 ? (
                    <p>No schedules found</p>
                ) : (
                    <table className="schedules-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Cron Expression</th>
                                <th>URL</th>
                                <th>Method</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {schedules.map((schedule) => (
                                <tr key={schedule.id}>
                                    <td>{schedule.id}</td>
                                    <td>{schedule.name}</td>
                                    <td>{schedule.cronExpression}</td>
                                    <td>{schedule.url}</td>
                                    <td>{schedule.method}</td>
                                    <td>
                                        <button
                                            onClick={() => handleDelete(schedule.id)}
                                            className="delete-btn"
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
    );
};

export default Schedules; 