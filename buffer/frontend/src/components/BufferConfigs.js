import React, { useEffect, useState } from 'react';
import { ReactComponent as TrashIcon } from '../icons/trash.svg';
import './BufferConfigs.css';

function BufferConfigs() {
  const [configs, setConfigs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    filter_field: '',
    max_size: 10,
    max_time: 60,
    reset_timer_on_message: false
  });
  const [editConfig, setEditConfig] = useState(null);

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const response = await fetch('/api/buffer-configs');
      const data = await response.json();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching buffer configs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/buffer-configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        setShowForm(false);
        setFormData({
          name: '',
          filter_field: '',
          max_size: 10,
          max_time: 60,
          reset_timer_on_message: false
        });
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error creating buffer config:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEditClick = (config) => {
    setEditConfig({ ...config });
  };

  const handleEditInputChange = (e) => {
    const { name, value } = e.target;
    setEditConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/buffer-configs/${editConfig.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editConfig),
      });
      if (response.ok) {
        setEditConfig(null);
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error updating buffer config:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this buffer configuration?')) return;
    try {
      const response = await fetch(`/api/buffer-configs/${id}`, { method: 'DELETE' });
      if (response.ok) {
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error deleting buffer config:', error);
    }
  };

  return (
    <div className="buffer-configs">
      <div className="header">
        <h1>Buffer Configurations</h1>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          New Configuration
        </button>
      </div>

      {showForm && (
        <div className="form-overlay">
          <div className="form-container">
            <h2>New Buffer Configuration</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Key Field (for grouping):</label>
                <input
                  type="text"
                  name="filter_field"
                  value={formData.filter_field}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., phone"
                />
              </div>
              <div className="form-group">
                <label>Max Buffer Size:</label>
                <input
                  type="number"
                  name="max_size"
                  value={formData.max_size}
                  onChange={handleInputChange}
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>Max Buffer Time (seconds):</label>
                <input
                  type="number"
                  name="max_time"
                  value={formData.max_time}
                  onChange={handleInputChange}
                  min="1"
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label htmlFor="reset_timer_on_message" style={{ marginBottom: 0, marginRight: 8 }}>
                  Reset timer on each new message (debounce):
                </label>
                <input
                  type="checkbox"
                  id="reset_timer_on_message"
                  name="reset_timer_on_message"
                  checked={formData.reset_timer_on_message}
                  onChange={e => setFormData(prev => ({ ...prev, reset_timer_on_message: e.target.checked }))}
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary">Create</button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="configs-list">
        {configs.map(config => (
          <div key={config.id} className="config-card" onClick={() => handleEditClick(config)} style={{ cursor: 'pointer', position: 'relative' }}>
            <div className="config-header" style={{ position: 'relative' }}>
              <h3>{config.name}</h3>
              <span className={`status ${config.active ? 'active' : 'inactive'}`} style={{ position: 'absolute', top: 0, right: 0 }}>{config.active ? 'Active' : 'Inactive'}</span>
            </div>
            <div className="config-details">
              <p><strong>Key Field:</strong> {config.filter_field}</p>
              <p><strong>Max Size:</strong> {config.max_size}</p>
              <p><strong>Max Time (s):</strong> {config.max_time}</p>
              <p><strong>Reset Timer on Message:</strong> {config.reset_timer_on_message ? 'TRUE' : 'FALSE'}</p>
              <p><strong>Created:</strong> {new Date(config.createdAt).toLocaleString()}</p>
              <p><strong>Webhook URL:</strong> <code>http://127.0.0.1:5000/api/webhook/{config.id}</code></p>
            </div>
            <button
              className="btn-delete"
              title="Delete Buffer"
              onClick={e => { e.stopPropagation(); handleDelete(config.id); }}
              style={{ position: 'absolute', bottom: 12, right: 12, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              <TrashIcon style={{ width: 20, height: 20, color: '#e74c3c' }} />
            </button>
          </div>
        ))}
      </div>

      {editConfig && (
        <div className="form-overlay">
          <div className="form-container">
            <h2>Edit Buffer Configuration</h2>
            <form onSubmit={handleEditSubmit}>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  name="name"
                  value={editConfig.name}
                  onChange={handleEditInputChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Key Field (for grouping):</label>
                <input
                  type="text"
                  name="filter_field"
                  value={editConfig.filter_field}
                  onChange={handleEditInputChange}
                  required
                  placeholder="e.g., phone"
                />
              </div>
              <div className="form-group">
                <label>Max Buffer Size:</label>
                <input
                  type="number"
                  name="max_size"
                  value={editConfig.max_size}
                  onChange={handleEditInputChange}
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>Max Buffer Time (seconds):</label>
                <input
                  type="number"
                  name="max_time"
                  value={editConfig.max_time}
                  onChange={handleEditInputChange}
                  min="1"
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label htmlFor="reset_timer_on_message_edit" style={{ marginBottom: 0, marginRight: 8 }}>
                  Reset timer on each new message (debounce):
                </label>
                <input
                  type="checkbox"
                  id="reset_timer_on_message_edit"
                  name="reset_timer_on_message"
                  checked={!!editConfig.reset_timer_on_message}
                  onChange={e => setEditConfig(prev => ({ ...prev, reset_timer_on_message: e.target.checked }))}
                />
              </div>
              <div className="form-actions">
                <button type="submit" className="btn-primary">Save</button>
                <button type="button" className="btn-secondary" onClick={() => setEditConfig(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default BufferConfigs; 