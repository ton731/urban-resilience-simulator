import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import GeneratePage from './pages/GeneratePage';
import MapPage from './pages/MapPage';
import './App.css';

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          <Route path="/generate" element={<GeneratePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/" element={<Navigate to="/generate" replace />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;