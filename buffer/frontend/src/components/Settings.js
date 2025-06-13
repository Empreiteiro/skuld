import React, { useEffect, useState } from 'react';
import './Settings.css';

function Settings() {
    const [timezone, setTimezone] = useState('UTC');
    const [message, setMessage] = useState({ type: '', text: '' });

    useEffect(() => {
        fetchTimezone();
    }, []);

    const fetchTimezone = async () => {
        try {
            const response = await fetch('/api/settings/timezone');
            const data = await response.json();
            setTimezone(data.timezone);
        } catch (error) {
            console.error('Error fetching timezone:', error);
            setMessage({
                type: 'error',
                text: 'Failed to load timezone settings'
            });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage({ type: '', text: '' });

        try {
            const response = await fetch('/api/settings/timezone', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ timezone }),
            });

            if (response.ok) {
                setMessage({
                    type: 'success',
                    text: 'Timezone updated successfully!'
                });
            } else {
                const errorData = await response.json();
                setMessage({
                    type: 'error',
                    text: errorData.error || 'Failed to update timezone'
                });
            }
        } catch (error) {
            console.error('Error updating timezone:', error);
            setMessage({
                type: 'error',
                text: 'Error updating timezone. Please try again.'
            });
        }
    };

    return (
        <div className="settings-container">
            <div className="page-header">
                <h1>Settings</h1>
            </div>

            <div className="settings-section">
                <h3>Timezone Settings</h3>
                <p>Configure your local timezone for proper date and time display.</p>

                {message.text && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <select
                        className="form-select"
                        value={timezone}
                        onChange={(e) => setTimezone(e.target.value)}
                    >
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">Eastern Time (ET)</option>
                        <option value="America/Chicago">Central Time (CT)</option>
                        <option value="America/Denver">Mountain Time (MT)</option>
                        <option value="America/Los_Angeles">Pacific Time (PT)</option>
                        <option value="America/Sao_Paulo">Brasília Time (BRT)</option>
                        <option value="Europe/London">London Time (GMT)</option>
                        <option value="Europe/Paris">Central European Time (CET)</option>
                        <option value="Asia/Tokyo">Japan Time (JST)</option>
                        <option value="Australia/Sydney">Australian Eastern Time (AET)</option>
                    </select>

                    <button type="submit" className="save-button">
                        Save Changes
                    </button>
                </form>
            </div>
        </div>
    );
}

export default Settings; 