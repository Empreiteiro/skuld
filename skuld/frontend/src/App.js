import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import './App.css';
import EditSchedule from './components/EditSchedule';
import Logs from './components/Logs';
import NewSchedule from './components/NewSchedule';
import Schedules from './components/Schedules';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Schedules />} />
            <Route path="/schedules" element={<Schedules />} />
            <Route path="/schedules/new" element={<NewSchedule />} />
            <Route path="/schedules/edit/:id" element={<EditSchedule />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 