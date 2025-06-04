import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Schedules.css';

function NewSchedule() {
    const navigate = useNavigate();
    const [newSchedule, setNewSchedule] = useState({
        name: '',
        description: '',
        url: '',
        cronExpression: '',
        method: 'GET',
        headers: '',
        body: ''
    });
    const [feedback, setFeedback] = useState({ type: '', message: '' });

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

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFeedback({ type: '', message: '' });

        try {
            const response = await fetch('http://localhost:5000/api/schedules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: newSchedule.name,
                    description: newSchedule.description,
                    url: newSchedule.url,
                    cronExpression: newSchedule.cronExpression,
                    method: newSchedule.method,
                    headers: newSchedule.headers ? JSON.parse(newSchedule.headers) : {},
                    body: newSchedule.body
                }),
            });

            if (response.ok) {
                setFeedback({
                    type: 'success',
                    message: 'Schedule created successfully!'
                });
                
                // Limpa o formulário
                setNewSchedule({
                    name: '',
                    description: '',
                    url: '',
                    cronExpression: '',
                    method: 'GET',
                    headers: '',
                    body: ''
                });

                // Redireciona após 2 segundos
                setTimeout(() => {
                    navigate('/schedules');
                }, 2000);
            } else {
                const errorData = await response.json();
                setFeedback({
                    type: 'error',
                    message: errorData.error || 'Failed to create schedule'
                });
            }
        } catch (error) {
            console.error('Error creating schedule:', error);
            setFeedback({
                type: 'error',
                message: 'Error creating schedule. Please try again.'
            });
        }
    };

    const handleChange = (e) => {
        setNewSchedule({
            ...newSchedule,
            [e.target.name]: e.target.value
        });
    };

    const handleCronPatternChange = (e) => {
        const selectedPattern = e.target.value;
        setNewSchedule(prev => ({
            ...prev,
            cronExpression: selectedPattern
        }));
    };

    return (
        <div className="schedules-container">
            <div className="page-header">
                <h1>Create New Schedule</h1>
            </div>

            <div className="content-section">
                {feedback.message && (
                    <div className={`feedback-message ${feedback.type}`}>
                        {feedback.message}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="schedule-form">
                    <div className="form-group">
                        <label htmlFor="name">Name</label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            value={newSchedule.name}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">Description</label>
                        <textarea
                            id="description"
                            name="description"
                            value={newSchedule.description}
                            onChange={handleChange}
                            rows="3"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="url">URL</label>
                        <input
                            type="url"
                            id="url"
                            name="url"
                            value={newSchedule.url}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="cronPattern">Cron Pattern</label>
                        <select
                            id="cronPattern"
                            value={newSchedule.cronExpression}
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
                        <label htmlFor="cronExpression">Custom Cron Expression</label>
                        <input
                            type="text"
                            id="cronExpression"
                            name="cronExpression"
                            value={newSchedule.cronExpression}
                            onChange={handleChange}
                            required
                            placeholder="*/5 * * * *"
                        />
                        <small className="helper-text">
                            Examples: */5 * * * * (every 5 minutes), 0 0 * * * (daily at midnight)
                        </small>
                    </div>

                    <div className="form-group">
                        <label htmlFor="method">Method</label>
                        <select
                            id="method"
                            name="method"
                            value={newSchedule.method}
                            onChange={handleChange}
                        >
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="headers">Headers (JSON)</label>
                        <textarea
                            id="headers"
                            name="headers"
                            value={newSchedule.headers}
                            onChange={handleChange}
                            rows="3"
                            placeholder='{"Content-Type": "application/json"}'
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="body">Body (JSON)</label>
                        <textarea
                            id="body"
                            name="body"
                            value={newSchedule.body}
                            onChange={handleChange}
                            rows="5"
                            placeholder='{"key": "value"}'
                        />
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="submit-button">
                            Create Schedule
                        </button>
                        <button 
                            type="button" 
                            className="cancel-button"
                            onClick={() => navigate('/schedules')}
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default NewSchedule; 