import React, { useEffect, useState } from 'react';
import './Messages.css';

function ReceivedMessages() {
  const [receivedMessages, setReceivedMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});
  const [filters, setFilters] = useState({
    start: '',
    end: '',
    bufferId: '',
    forwardedId: '',
    status: ''
  });

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/messages/received');
      const data = await response.json();
      setReceivedMessages(data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
    setLoading(false);
  };

  const toggleExpand = (id) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderMessageContent = (message) => {
    try {
      const data = JSON.parse(message.message_data);
      return (
        <pre className="message-content">{JSON.stringify(data, null, 2)}</pre>
      );
    } catch (e) {
      return <pre className="message-content">{message.message_data}</pre>;
    }
  };

  // Filtro local
  const filteredMessages = receivedMessages.filter(msg => {
    // Intervalo de data/hora
    const receivedAt = new Date(msg.received_at);
    if (filters.start && receivedAt < new Date(filters.start)) return false;
    if (filters.end && receivedAt > new Date(filters.end)) return false;
    // Buffer ID
    if (filters.bufferId && String(msg.buffer_id) !== filters.bufferId) return false;
    // Forwarded ID
    if (filters.forwardedId && String(msg.forwarded_id || '') !== filters.forwardedId) return false;
    // Status
    const status = msg.status || (msg.processed ? 'processed' : 'pending');
    if (filters.status && status !== filters.status) return false;
    return true;
  });

  return (
    <div className="messages">
      <div className="header">
        <h1>Received Messages</h1>
      </div>
      <div className="messages-filter-card">
        <form className="messages-filter-form" onSubmit={e => e.preventDefault()}>
          <div className="filter-group">
            <label>Received from:</label>
            <input type="datetime-local" value={filters.start} onChange={e => setFilters(f => ({ ...f, start: e.target.value }))} />
          </div>
          <div className="filter-group">
            <label>to:</label>
            <input type="datetime-local" value={filters.end} onChange={e => setFilters(f => ({ ...f, end: e.target.value }))} />
          </div>
          <div className="filter-group">
            <label>Buffer ID:</label>
            <input type="text" value={filters.bufferId} onChange={e => setFilters(f => ({ ...f, bufferId: e.target.value }))} placeholder="Buffer ID" />
          </div>
          <div className="filter-group">
            <label>Forwarded ID:</label>
            <input type="text" value={filters.forwardedId} onChange={e => setFilters(f => ({ ...f, forwardedId: e.target.value }))} placeholder="Forwarded ID" />
          </div>
          <div className="filter-group">
            <label>Status:</label>
            <select value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="processed">Processed</option>
              <option value="cancelled">Cancelled</option>
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
                <th>Buffer ID</th>
                <th>Forwarded ID</th>
                <th>Source</th>
                <th>Received</th>
                <th>Content</th>
              </tr>
            </thead>
            <tbody>
              {filteredMessages.map(message => (
                <tr key={message.id} className="messages-row">
                  <td>{message.id}</td>
                  <td>
                    <span className={`status ${message.status || (message.processed ? 'processed' : 'pending')}`}>
                      {message.status === 'cancelled'
                        ? 'Cancelled'
                        : message.processed
                          ? 'Processed'
                          : 'Pending'}
                    </span>
                  </td>
                  <td>{message.buffer_id}</td>
                  <td>{message.forwarded_id || '-'}</td>
                  <td>{message.source}</td>
                  <td>{new Date(message.received_at).toLocaleString()}</td>
                  <td>
                    <button className="expand-btn icon-btn" onClick={() => toggleExpand(message.id)} title={expanded[message.id] ? 'Hide content' : 'Show content'}>
                      {expanded[message.id] ? (
                        <span>&#9650;</span>
                      ) : (
                        <span>&#128269;</span>
                      )}
                    </button>
                    {expanded[message.id] && (
                      <div style={{ marginTop: 8 }}>{renderMessageContent(message)}</div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ReceivedMessages; 