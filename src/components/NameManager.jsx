import React, { useState } from 'react';
import './NameManager.css';

const NameManager = ({ names, onNameAdded, onNameRemoved, onRefresh }) => {
  const [newName, setNewName] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddName = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;

    setIsAdding(true);
    try {
      await onNameAdded(newName.trim());
      setNewName('');
    } catch (error) {
      console.error('Error adding name:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveName = async (name) => {
    try {
      await onNameRemoved(name);
    } catch (error) {
      console.error('Error removing name:', error);
    }
  };

  return (
    <div className="name-manager">
      <div className="name-manager-header">
        <h3>Manage Names ({names.length})</h3>
        <button 
          className="refresh-button"
          onClick={onRefresh}
          title="Refresh names from server"
        >
          🔄 Refresh
        </button>
      </div>

      <form onSubmit={handleAddName} className="add-name-form">
        <div className="input-group">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Enter a name to add..."
            className="name-input"
            disabled={isAdding}
            maxLength={50}
          />
          <button 
            type="submit" 
            className="add-button"
            disabled={!newName.trim() || isAdding}
          >
            {isAdding ? 'Adding...' : 'Add'}
          </button>
        </div>
      </form>

      <div className="names-list">
        {names.length === 0 ? (
          <div className="empty-state">
            <p>No names available. Add some names to get started!</p>
          </div>
        ) : (
          <div className="names-grid">
            {names.map((name, index) => (
              <div key={index} className="name-item">
                <span className="name-text">{name}</span>
                <button
                  className="remove-button"
                  onClick={() => handleRemoveName(name)}
                  title={`Remove ${name}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="name-manager-footer">
        <p>
          💡 Tip: Names are automatically saved and synced with your backend service
        </p>
      </div>
    </div>
  );
};

export default NameManager;
