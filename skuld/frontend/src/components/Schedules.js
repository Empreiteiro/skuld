import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Schedules.css';

function Schedules() {
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
                        <label htmlFor="cronExpression">Cron Expression</label>
                        <input
                            type="text"
                            id="cronExpression"
                            name="cronExpression"
                            value={newSchedule.cronExpression}
                            onChange={handleChange}
                            required
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
                            placeholder="{\n  'Content-Type': 'application/json'\n}"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="body">Body</label>
                        <textarea
                            id="body"
                            name="body"
                            value={newSchedule.body}
                            onChange={handleChange}
                            rows="3"
                        />
                    </div>

                    <div className="form-actions">
                        <button type="submit" className="submit-button">Create Schedule</button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Schedules; 