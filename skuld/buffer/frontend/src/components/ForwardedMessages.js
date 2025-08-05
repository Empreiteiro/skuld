import React, { useEffect, useState } from 'react';
import './Messages.css';

function ForwardedMessages() {
  const [forwardedMessages, setForwardedMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    start: '',
    end: '',
    config: '',
    status: ''
  });
  const [expanded, setExpanded] = useState({});

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/messages/forwarded');
      const data = await response.json();
      setForwardedMessages(data);
    } catch (error) {
      console.error('Error fetching forwarded messages:', error);
    }
    setLoading(false);
  };

  // Obter lista única de configs
  const configOptions = Array.from(new Set(forwardedMessages.map(m => m.forwarding_config_name))).filter(Boolean);

  // Filtro local
  const filteredMessages = forwardedMessages.filter(msg => {
    // Intervalo de data/hora
    const forwardedAt = new Date(msg.forwarded_at);
    if (filters.start && forwardedAt < new Date(filters.start)) return false;
    if (filters.end && forwardedAt > new Date(filters.end)) return false;
    // Config
    if (filters.config && msg.forwarding_config_name !== filters.config) return false;
    // Status
    if (filters.status && msg.status !== filters.status) return false;
    return true;
  });

  const toggleExpand = (id, field) => {
    setExpanded(prev => ({ ...prev, [id]: { ...prev[id], [field]: !prev[id]?.[field] } }));
  };

  const renderJsonSummary = (obj, maxLen = 60) => {
    if (!obj) return '-';
    let str = '';
    try {
      str = typeof obj === 'string' ? obj : JSON.stringify(obj);
    } catch {
      str = String(obj);
    }
    if (str.length > maxLen) {
      return str.slice(0, maxLen) + '...';
    }
    return str;
  };

  return (
    <div className="messages">
      <div className="header">
        <h1>Forwarded Messages</h1>
      </div>
      <div className="messages-filter-card">
        <form className="messages-filter-form" onSubmit={e => e.preventDefault()}>
          <div className="filter-group">
            <label>Forwarded from:</label>
            <input type="datetime-local" value={filters.start} onChange={e => setFilters(f => ({ ...f, start: e.target.value }))} />
          </div>
          <div className="filter-group">
            <label>to:</label>
            <input type="datetime-local" value={filters.end} onChange={e => setFilters(f => ({ ...f, end: e.target.value }))} />
          </div>
          <div className="filter-group">
            <label>Config:</label>
            <select value={filters.config} onChange={e => setFilters(f => ({ ...f, config: e.target.value }))}>
              <option value="">All</option>
              {configOptions.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Status:</label>
            <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
              <option value="">All</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>
          </div>
        </form>
      </div>
      {loading ? (
        <div className="loading">Loading messages...</div>
      ) : (
        <div className="messages-table-card">
          <table className="messages-table modern">
            <thead>
              <tr>
                <th>ID</th>
                <th>Status</th>
                <th>Config</th>
                <th>Forwarded</th>
                <th>Content</th>
                <th>Headers</th>
                <th>Response</th>
              </tr>
            </thead>
            <tbody>
              {filteredMessages.map(message => {
                let content = '-';
                let headers = '-';
                let response = '-';
                try {
                  const resp = JSON.parse(message.response);
                  content = resp.sent?.payload;
                  headers = resp.sent?.headers;
                  response = resp.response;
                } catch (e) {
                  content = '-';
                  headers = '-';
                  response = message.response;
                }
                return (
                  <tr key={message.id} className="messages-row">
                    <td>{message.id}</td>
                    <td>
                      <span className={`status ${message.status}`}>
                        {message.status}
                      </span>
                    </td>
                    <td>{message.forwarding_config_name}</td>
                    <td>{new Date(message.forwarded_at).toLocaleString()}</td>
                    <td>
                      <button className="expand-btn icon-btn" onClick={() => toggleExpand(message.id, 'content')} title={expanded[message.id]?.content ? 'Hide content' : 'Show content'}>
                        {expanded[message.id]?.content ? (
                          <span>&#9650;</span>
                        ) : (
                          <span>&#128269;</span>
                        )}
                      </button>
                      {expanded[message.id]?.content && (
                        <div style={{ marginTop: 8 }}><pre className="message-content">{JSON.stringify(content, null, 2)}</pre></div>
                      )}
                    </td>
                    <td>
                      <button className="expand-btn icon-btn" onClick={() => toggleExpand(message.id, 'headers')} title={expanded[message.id]?.headers ? 'Hide headers' : 'Show headers'}>
                        {expanded[message.id]?.headers ? (
                          <span>&#9650;</span>
                        ) : (
                          <span>&#128269;</span>
                        )}
                      </button>
                      {expanded[message.id]?.headers && (
                        <div style={{ marginTop: 8 }}><pre className="message-content">{JSON.stringify(headers, null, 2)}</pre></div>
                      )}
                    </td>
                    <td>
                      <button className="expand-btn icon-btn" onClick={() => toggleExpand(message.id, 'response')} title={expanded[message.id]?.response ? 'Hide response' : 'Show response'}>
                        {expanded[message.id]?.response ? (
                          <span>&#9650;</span>
                        ) : (
                          <span>&#128269;</span>
                        )}
                      </button>
                      {expanded[message.id]?.response && (
                        <div style={{ marginTop: 8 }}><pre className="message-content">{typeof response === 'object' ? JSON.stringify(response, null, 2) : response}</pre></div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ForwardedMessages; 