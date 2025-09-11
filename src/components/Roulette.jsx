import React, { useState, useEffect, useRef } from 'react';
import './Roulette.css';

const Roulette = ({ names, onSpinComplete }) => {
  const [isSpinning, setIsSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [selectedName, setSelectedName] = useState('');
  const wheelRef = useRef(null);

  const spin = () => {
    if (isSpinning || names.length === 0) return;

    setIsSpinning(true);
    setSelectedName('');

    // Calculate random rotation (multiple full rotations + random angle)
    const fullRotations = 5 + Math.random() * 5; // 5-10 full rotations
    const randomAngle = Math.random() * 360;
    const totalRotation = rotation + (fullRotations * 360) + randomAngle;

    setRotation(totalRotation);

    // Calculate which name will be selected
    const anglePerName = 360 / names.length;
    const finalAngle = totalRotation % 360;
    const selectedIndex = Math.floor((360 - finalAngle) / anglePerName) % names.length;
    const winner = names[selectedIndex];

    // Complete spin after animation
    setTimeout(() => {
      setIsSpinning(false);
      setSelectedName(winner);
      if (onSpinComplete) {
        onSpinComplete(winner);
      }
    }, 4000); // Match CSS animation duration
  };

  const reset = () => {
    setRotation(0);
    setSelectedName('');
  };

  return (
    <div className="roulette-container">
      <div className="roulette-wheel-container">
        <div 
          ref={wheelRef}
          className="roulette-wheel"
          style={{ 
            transform: `rotate(${rotation}deg)`,
            transition: isSpinning ? 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)' : 'none'
          }}
        >
          {names.map((name, index) => {
            const angle = (360 / names.length) * index;
            const isEven = index % 2 === 0;
            
            return (
              <div
                key={index}
                className={`roulette-segment ${isEven ? 'even' : 'odd'}`}
                style={{
                  transform: `rotate(${angle}deg)`,
                  transformOrigin: '50% 50%'
                }}
              >
                <div 
                  className="segment-text"
                  style={{
                    transform: `rotate(${-angle}deg)`,
                    transformOrigin: '50% 50%'
                  }}
                >
                  {name}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Pointer */}
        <div className="roulette-pointer"></div>
        
        {/* Center circle */}
        <div className="roulette-center"></div>
      </div>

      <div className="roulette-controls">
        <button 
          className="spin-button"
          onClick={spin}
          disabled={isSpinning || names.length === 0}
        >
          {isSpinning ? 'Spinning...' : 'SPIN!'}
        </button>
        
        <button 
          className="reset-button"
          onClick={reset}
          disabled={isSpinning}
        >
          Reset
        </button>
      </div>

      {selectedName && (
        <div className="winner-display">
          <h2>🎉 Winner: {selectedName} 🎉</h2>
        </div>
      )}

      {names.length === 0 && (
        <div className="no-names-message">
          <p>No names available. Please add some names to spin the roulette!</p>
        </div>
      )}
    </div>
  );
};

export default Roulette;
