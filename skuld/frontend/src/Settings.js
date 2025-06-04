import axios from 'axios';
import React, { useEffect, useState } from 'react';

const Settings = () => {
  const [timezone, setTimezone] = useState('');
  const [availableTimezones, setAvailableTimezones] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    // Load available timezones
    const timezones = Intl.supportedValuesOf('timeZone');
    setAvailableTimezones(timezones);

    // Load current timezone
    axios.get('/api/settings/timezone')
      .then(response => {
        setTimezone(response.data.timezone);
      })
      .catch(error => {
        console.error('Error loading timezone:', error);
      });
  }, []);

  const handleTimezoneChange = (e) => {
    setTimezone(e.target.value);
  };

  const handleSave = () => {
    axios.post('/api/settings/timezone', { timezone })
      .then(response => {
        setMessage('Settings saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      })
      .catch(error => {
        console.error('Error saving timezone:', error);
        setMessage('Error saving settings');
        setTimeout(() => setMessage(''), 3000);
      });
  };

  return (
    <div className="settings-container">
      <h2 className="page-title">Settings</h2>
      
      <div className="settings-section">
        <h3>Timezone</h3>
        <p>Select the timezone for displaying schedules and logs:</p>
        
        <select 
          value={timezone} 
          onChange={handleTimezoneChange}
          className="form-select"
        >
          <option value="">Select a timezone</option>
          {availableTimezones.map(tz => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </div>

      <button 
        onClick={handleSave}
        className="save-button"
        disabled={!timezone}
      >
        Save Settings
      </button>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default Settings; 