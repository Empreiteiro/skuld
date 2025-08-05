import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';
import BufferConfigs from './components/BufferConfigs';
import ForwardedMessages from './components/ForwardedMessages';
import ForwardingConfigs from './components/ForwardingConfigs';
import ReceivedMessages from './components/ReceivedMessages';
import Sidebar from './components/Sidebar';
import Settings from './Settings';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/buffer-configs" element={<BufferConfigs />} />
            <Route path="/forwarding-configs" element={<ForwardingConfigs />} />
            <Route path="/messages/received" element={<ReceivedMessages />} />
            <Route path="/messages/forwarded" element={<ForwardedMessages />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/" element={<BufferConfigs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 