import React, { useState, useEffect } from 'react';
import Roulette from './components/Roulette';
import NameManager from './components/NameManager';
import apiService from './services/api';
import './App.css';

function App() {
  const [names, setNames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastWinner, setLastWinner] = useState('');

  useEffect(() => {
    loadNames();
  }, []);

  const loadNames = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedNames = await apiService.fetchNames();
      setNames(fetchedNames);
    } catch (err) {
      setError('Failed to load names from server. Using mock data.');
      console.error('Error loading names:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpinComplete = (winner) => {
    setLastWinner(winner);
    console.log('Winner selected:', winner);
  };

  const handleNameAdded = async (newName) => {
    try {
      await apiService.addName(newName);
      setNames(prev => [...prev, newName]);
    } catch (err) {
      // If API fails, just add locally for demo
      setNames(prev => [...prev, newName]);
      console.error('Error adding name to server:', err);
    }
  };

  const handleNameRemoved = async (nameToRemove) => {
    try {
      await apiService.removeName(nameToRemove);
      setNames(prev => prev.filter(name => name !== nameToRemove));
    } catch (err) {
      // If API fails, just remove locally for demo
      setNames(prev => prev.filter(name => name !== nameToRemove));
      console.error('Error removing name from server:', err);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading names...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎯 Name Roulette 🎯</h1>
        <p>Spin the wheel to randomly select a name!</p>
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}
      </header>

      <main className="app-main">
        <div className="roulette-section">
          <Roulette 
            names={names} 
            onSpinComplete={handleSpinComplete}
          />
        </div>

        <div className="management-section">
          <NameManager
            names={names}
            onNameAdded={handleNameAdded}
            onNameRemoved={handleNameRemoved}
            onRefresh={loadNames}
          />
        </div>
      </main>

      {lastWinner && (
        <div className="last-winner">
          <h3>Last Winner: {lastWinner}</h3>
        </div>
      )}

      <footer className="app-footer">
        <p>Built with React • Ready for backend integration</p>
      </footer>
    </div>
  );
}

export default App;
