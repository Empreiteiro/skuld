import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import './Schedules.css';

function EditSchedule() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [schedule, setSchedule] = useState(null);
    const [feedback, setFeedback] = useState({ type: '', message: '' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`http://localhost:5000/api/schedules`)
            .then(res => res.json())
            .then(data => {
                const found = data.find(s => String(s.id) === String(id));
                setSchedule(found);
                setLoading(false);
            });
    }, [id]);

    const handleChange = (e) => {
        setSchedule({
            ...schedule,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setFeedback({ type: '', message: '' });
        try {
            const response = await fetch(`http://localhost:5000/api/schedules/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(schedule)
            });
            if (response.ok) {
                setFeedback({ type: 'success', message: 'Schedule updated successfully!' });
                setTimeout(() => navigate('/schedules'), 1500);
            } else {
                const errorData = await response.json();
                setFeedback({ type: 'error', message: errorData.error || 'Failed to update schedule' });
            }
        } catch (err) {
            setFeedback({ type: 'error', message: 'Error updating schedule. Please try again.' });
        }
    };

    if (loading || !schedule) return <div className="schedules-container">Loading...</div>;

    return (
        <div className="schedules-container">
            <div className="page-header">
                <h1>Edit Schedule</h1>
            </div>
            <div className="content-section">
                {feedback.message && (
                    <div className={`feedback-message ${feedback.type}`}>{feedback.message}</div>
                )}
                <form onSubmit={handleSubmit} className="schedule-form">
                    <div className="form-group">
                        <label htmlFor="name">Name</label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            value={schedule.name}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="description">Description</label>
                        <textarea
                            id="description"
                            name="description"
                            value={schedule.description || ''}
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
                            value={schedule.url}
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
                            value={schedule.cronExpression}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="method">Method</label>
                        <select
                            id="method"
                            name="method"
                            value={schedule.method}
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
                            value={schedule.headers || ''}
                            onChange={handleChange}
                            rows="3"
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="body">Body</label>
                        <textarea
                            id="body"
                            name="body"
                            value={schedule.body || ''}
                            onChange={handleChange}
                            rows="3"
                        />
                    </div>
                    <div className="form-actions">
                        <button type="submit" className="submit-button">Save Changes</button>
                        <button type="button" className="cancel-button" onClick={() => navigate('/schedules')}>Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default EditSchedule; 