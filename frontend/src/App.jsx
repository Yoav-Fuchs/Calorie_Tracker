import React, { useState, useRef } from 'react';

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [dailyStats, setDailyStats] = useState({
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  });
  
  const fileInputRef = useRef(null);

  const todayDate = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  const handleCameraClick = () => {
    // Open file picker
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('https://calorie-tracker-deco.onrender.com/analyze-food', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      if (data.items && data.items.length > 0) {
        // Just take the first item for demonstration
        const item = data.items[0];
        
        const newLog = {
          id: Date.now(),
          name: item.name,
          calories: Math.round(item.nutrition.calories),
          time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
        };
        
        setLogs([newLog, ...logs]);
        setDailyStats(prev => ({
          calories: prev.calories + Math.round(item.nutrition.calories),
          protein: prev.protein + Math.round(item.nutrition.protein_g),
          carbs: prev.carbs + Math.round(item.nutrition.carbs_g),
          fat: prev.fat + Math.round(item.nutrition.fat_g)
        }));
      }
    } catch (error) {
      console.error('Error analyzing food:', error);
      alert('Failed to analyze food. Ensure the backend is running at http://127.0.0.1:8000');
    } finally {
      setIsProcessing(false);
      // Reset input
      e.target.value = null;
    }
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="header animate-enter delay-1">
        <div>
          <h1>Welcome, User</h1>
          <p>Let's track your nutrition</p>
        </div>
        <div className="date-badge">{todayDate}</div>
      </header>

      {/* Main Stats Card */}
      <section className="glass-card animate-enter delay-2">
        <h2>Calories Today</h2>
        <div className="main-stat">
          <span className="number">{dailyStats.calories}</span>
          <span className="unit">/ 2,200 kcal</span>
        </div>
        
        <div className="macros-grid">
          <div className="macro-item protein">
            <span className="macro-label">Protein</span>
            <span className="macro-value">{dailyStats.protein}g</span>
          </div>
          <div className="macro-item carbs">
            <span className="macro-label">Carbs</span>
            <span className="macro-value">{dailyStats.carbs}g</span>
          </div>
          <div className="macro-item fat">
            <span className="macro-label">Fat</span>
            <span className="macro-value">{dailyStats.fat}g</span>
          </div>
        </div>
      </section>

      {/* Activity Feed */}
      <h3 className="section-title animate-enter delay-3">Today's Meals</h3>
      <div className="activity-feed animate-enter delay-3">
        {logs.length === 0 ? (
          <p style={{textAlign: 'center', color: 'var(--text-secondary)', marginTop: '2rem'}}>
            No meals logged yet. Tap the camera to start!
          </p>
        ) : (
          logs.map(log => (
            <div key={log.id} className="food-item">
              <div className="food-info">
                <h4>{log.name}</h4>
                <p>{log.time}</p>
              </div>
              <div className="food-calories">
                {log.calories} kcal
              </div>
            </div>
          ))
        )}
      </div>

      {/* Floating Camera Button */}
      <div className="fab-container">
        <input 
          type="file" 
          accept="image/*" 
          capture="environment" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
        <button 
          className="fab" 
          onClick={handleCameraClick} 
          aria-label="Take Photo"
          disabled={isProcessing}
          style={{ opacity: isProcessing ? 0.7 : 1, animation: isProcessing ? 'none' : 'pulse 3s infinite' }}
        >
          {isProcessing ? (
            // Simple loading spinner
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="spinner">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
            </svg>
          ) : (
            // Camera Icon
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
              <circle cx="12" cy="13" r="4"></circle>
            </svg>
          )}
        </button>
      </div>
      {/* Add a tiny style block just for the spinner rotation */}
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spinner { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}

export default App;
