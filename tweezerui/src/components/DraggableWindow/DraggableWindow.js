import React, { useState } from 'react';
import Draggable from 'react-draggable';
import { Resizable } from 're-resizable';
import './DraggableWindow.css';

function DraggableWindow({ children, initialSize, defaultPosition, onMinimize }) {
  const [size, setSize] = useState(initialSize);
  const [position, setPosition] = useState(defaultPosition);

  const handleResize = (e, direction, ref, delta, position) => {
    // Update the size state
    setSize({
      width: ref.style.width,
      height: ref.style.height
    });

    // Adjust the position for left and top handles
    if (direction.includes('left')) {
      setPosition(prev => ({
        x: prev.x + delta.width,
        y: prev.y
      }));
    }
    if (direction.includes('top')) {
      setPosition(prev => ({
        x: prev.x,
        y: prev.y + delta.height
      }));
    }
  };

  return (
    <Draggable handle=".window-header" position={position} onStop={(e, data) => setPosition({ x: data.x, y: data.y })}>
      <Resizable
        size={size}
        onResizeStop={handleResize}
        enable={{ top:true, right:true, bottom:true, left:true, topRight:true, bottomRight:true, bottomLeft:true, topLeft:true }}
        minWidth="300px" // Set minimum width
        minHeight="200px" // Set minimum height
        maxWidth="100%"  // Optional: Set maximum width
        maxHeight="100%" // Optional: Set maximum height
      >
        <div className="draggable-window">
          <div className="window-header">
            <button onClick={onMinimize} className="button minimize-button">
              <span className="icon">-</span>
            </button>
          </div>
          <div className="window-content" style={{ overflow: 'auto' }}>
            {children}
          </div>
        </div>
      </Resizable>
    </Draggable>
  );
}

export default DraggableWindow;
