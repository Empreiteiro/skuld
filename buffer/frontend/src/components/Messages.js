import React, { useEffect, useState } from 'react';
import './Messages.css';

function Messages() {
  const [activeTab, setActiveTab] = useState('received');
  const [receivedMessages, setReceivedMessages] = useState([]);
  const [forwardedMessages, setForwardedMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
  }, [activeTab]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      if (activeTab === 'received') {
        const response = await fetch('/api/messages/received');
        const data = await response.json();
        setReceivedMessages(data);
      } else {
        const response = await fetch('/api/messages/forwarded');
        const data = await response.json();
        setForwardedMessages(data);
      }
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
    setLoading(false);
  };

  const renderMessageContent = (message) => {
    try {
      const data = JSON.parse(message.message_data);
      return (
        <pre className="message-content">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
    } catch (e) {
      return <pre className="message-content">{message.message_data}</pre>;
    }
  };

  return (
    <div className="messages">
      <div className="header">
        <h1>Message History</h1>
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'received' ? 'active' : ''}`}
            onClick={() => setActiveTab('received')}
          >
            Received Messages
          </button>
          <button
            className={`tab ${activeTab === 'forwarded' ? 'active' : ''}`}
            onClick={() => setActiveTab('forwarded')}
          >
            Forwarded Messages
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading messages...</div>
      ) : (
        <div className="messages-list">
          {activeTab === 'received' ? (
            receivedMessages.map(message => (
              <div key={message.id} className="message-card">
                <div className="message-header">
                  <h3>Message #{message.id}</h3>
                  <span className={`status ${message.processed ? 'processed' : 'pending'}`}>
                    {message.processed ? 'Processed' : 'Pending'}
                  </span>
                </div>
                <div className="message-details">
                  <p><strong>Source:</strong> {message.source}</p>
                  <p><strong>Received:</strong> {new Date(message.received_at).toLocaleString()}</p>
                  <p><strong>Content:</strong></p>
                  {renderMessageContent(message)}
                </div>
              </div>
            ))
          ) : (
            forwardedMessages.map(message => (
              <div key={message.id} className="message-card">
                <div className="message-header">
                  <h3>Forward #{message.id}</h3>
                  <span className={`status ${message.status}`}>
                    {message.status}
                  </span>
                </div>
                <div className="message-details">
                  <p><strong>Config:</strong> {message.forwarding_config_name}</p>
                  <p><strong>Forwarded:</strong> {new Date(message.forwarded_at).toLocaleString()}</p>
                  <p><strong>Response:</strong></p>
                  <pre className="message-content">{message.response}</pre>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default Messages; 