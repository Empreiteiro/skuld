import React, { useEffect, useState } from 'react';
import { ReactComponent as TrashIcon } from '../icons/trash.svg';
import './ForwardingConfigs.css';

function ForwardingConfigs() {
  const [configs, setConfigs] = useState([]);
  const [bufferConfigs, setBufferConfigs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    method: 'POST',
    headers: '{}',
    buffer_config_id: '',
    fields: '',
    template: ''
  });
  const [editConfig, setEditConfig] = useState(null);

  useEffect(() => {
    fetchConfigs();
    fetchBufferConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      const response = await fetch('/api/forwarding-configs');
      const data = await response.json();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching forwarding configs:', error);
    }
  };

  const fetchBufferConfigs = async () => {
    try {
      const response = await fetch('/api/buffer-configs');
      const data = await response.json();
      setBufferConfigs(data);
    } catch (error) {
      console.error('Error fetching buffer configs:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/forwarding-configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          headers: JSON.parse(formData.headers)
        }),
      });
      if (response.ok) {
        setShowForm(false);
        setFormData({
          name: '',
          url: '',
          method: 'POST',
          headers: '{}',
          buffer_config_id: '',
          fields: '',
          template: ''
        });
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error creating forwarding config:', error);
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
    setEditConfig({
      ...config,
      headers: JSON.stringify(JSON.parse(config.headers || '{}'), null, 2),
      fields: config.fields || '',
      template: config.template || ''
    });
  };

  const handleEditInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditConfig(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/forwarding-configs/${editConfig.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editConfig,
          headers: JSON.parse(editConfig.headers),
          fields: editConfig.fields,
          active: editConfig.active ? 1 : 0
        }),
      });
      if (response.ok) {
        setEditConfig(null);
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error updating forwarding config:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this forwarding configuration?')) return;
    try {
      const response = await fetch(`/api/forwarding-configs/${id}`, { method: 'DELETE' });
      if (response.ok) {
        fetchConfigs();
      }
    } catch (error) {
      console.error('Error deleting forwarding config:', error);
    }
  };

  return (
    <div className="forwarding-configs">
      <div className="header">
        <h1>Forwarding Configurations</h1>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          New Configuration
        </button>
      </div>

      {showForm && (
        <div className="form-overlay">
          <div className="form-container">
            <h2>New Forwarding Configuration</h2>
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
                <label>Buffer Configuration:</label>
                <select
                  name="buffer_config_id"
                  value={formData.buffer_config_id}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select a buffer...</option>
                  {bufferConfigs.map(buffer => (
                    <option key={buffer.id} value={buffer.id}>{buffer.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>URL:</label>
                <input
                  type="url"
                  name="url"
                  value={formData.url}
                  onChange={handleInputChange}
                  required
                  placeholder="https://api.example.com/webhook"
                />
              </div>
              <div className="form-group">
                <label>Method:</label>
                <select
                  name="method"
                  value={formData.method}
                  onChange={handleInputChange}
                >
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>
              <div className="form-group">
                <label>Headers (JSON):</label>
                <textarea
                  name="headers"
                  value={formData.headers}
                  onChange={handleInputChange}
                  placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
                  rows="4"
                />
              </div>
              <div className="form-group">
                <label>Payload Template:</label>
                <textarea
                  name="template"
                  value={formData.template}
                  onChange={handleInputChange}
                  placeholder='Ex: {"phone": "{{phone}}", "conteudo": "Mensagem: {{message}}, ID: {{user_id}}"}'
                  rows="4"
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label htmlFor="active" style={{ marginBottom: 0, marginRight: 8 }}>
                  Active:
                </label>
                <input
                  type="checkbox"
                  id="active"
                  name="active"
                  checked={!!formData.active}
                  onChange={handleInputChange}
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
          <div key={config.id} className="config-card" style={{ position: 'relative', cursor: 'pointer' }} onClick={() => handleEditClick(config)}>
            <div className="config-header">
              <h3>{config.name}</h3>
              <span className={`status ${config.active ? 'active' : 'inactive'}`}>{config.active ? 'Active' : 'Inactive'}</span>
            </div>
            <div className="config-details">
              <p><strong>Buffer:</strong> {bufferConfigs.find(b => b.id === config.buffer_config_id)?.name || config.buffer_config_id}</p>
              <p><strong>URL:</strong> <span style={{ wordBreak: 'break-all' }}>{config.url}</span></p>
              <p><strong>Method:</strong> {config.method}</p>
              <p><strong>Headers:</strong></p>
              <pre className="message-content">{JSON.stringify(JSON.parse(config.headers || '{}'), null, 2)}</pre>
              <p><strong>Created:</strong> {new Date(config.createdAt).toLocaleString()}</p>
            </div>
            <button
              className="btn-delete"
              title="Delete Forwarding"
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
            <h2>Edit Forwarding Configuration</h2>
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
                <label>Buffer Configuration:</label>
                <select
                  name="buffer_config_id"
                  value={editConfig.buffer_config_id}
                  onChange={handleEditInputChange}
                  required
                >
                  <option value="">Select a buffer...</option>
                  {bufferConfigs.map(buffer => (
                    <option key={buffer.id} value={buffer.id}>{buffer.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>URL:</label>
                <input
                  type="url"
                  name="url"
                  value={editConfig.url}
                  onChange={handleEditInputChange}
                  required
                  placeholder="https://api.example.com/webhook"
                />
              </div>
              <div className="form-group">
                <label>Method:</label>
                <select
                  name="method"
                  value={editConfig.method}
                  onChange={handleEditInputChange}
                >
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>
              <div className="form-group">
                <label>Headers (JSON):</label>
                <textarea
                  name="headers"
                  value={editConfig.headers}
                  onChange={handleEditInputChange}
                  placeholder='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
                  rows="4"
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label htmlFor="active_edit" style={{ marginBottom: 0, marginRight: 8 }}>
                  Active:
                </label>
                <input
                  type="checkbox"
                  id="active_edit"
                  name="active"
                  checked={!!editConfig.active}
                  onChange={handleEditInputChange}
                />
              </div>
              <div className="form-group">
                <label>Payload Template:</label>
                <textarea
                  name="template"
                  value={editConfig.template}
                  onChange={handleEditInputChange}
                  placeholder='Ex: {"phone": "{{phone}}", "conteudo": "Mensagem: {{message}}, ID: {{user_id}}"}'
                  rows="4"
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

export default ForwardingConfigs; 