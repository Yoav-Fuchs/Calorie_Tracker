import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Trash2, LogOut } from 'lucide-react';

function Dashboard() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [dailyStats, setDailyStats] = useState({
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  });
  
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  
  const baseUrl = import.meta.env.VITE_API_URL || 'https://calorie-tracker-deco.onrender.com';
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/auth');
      return;
    }
    fetchLogs(token);
  }, [navigate]);

  useEffect(() => {
    // Recalculate daily stats when logs change
    const newStats = logs.reduce((acc, log) => ({
      calories: acc.calories + (log.nutrition?.calories || 0),
      protein: acc.protein + (log.nutrition?.protein_g || 0),
      carbs: acc.carbs + (log.nutrition?.carbs_g || 0),
      fat: acc.fat + (log.nutrition?.fat_g || 0)
    }), { calories: 0, protein: 0, carbs: 0, fat: 0 });
    
    setDailyStats(newStats);
  }, [logs]);

  const fetchLogs = async (token) => {
    try {
      const response = await fetch(`${baseUrl}/logs`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/auth');
        return;
      }
      const data = await response.json();
      setLogs(data);
    } catch (error) {
      console.error("Error fetching logs", error);
    }
  };

  const handleDelete = async (logId) => {
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${baseUrl}/logs/${logId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        setLogs(logs.filter(log => log.id !== logId));
      }
    } catch (error) {
      console.error("Error deleting log", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/auth');
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${baseUrl}/analyze-food`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });
      
      if (response.status === 401) {
        localStorage.removeItem('token');
        navigate('/auth');
        return;
      }
      
      const data = await response.json();
      
      if (data.items && data.items.length > 0) {
        setLogs(prev => [...data.items, ...prev]);
      }
    } catch (error) {
      console.error('Error analyzing image:', error);
      alert('Failed to analyze image. Please try again.');
    } finally {
      setIsProcessing(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Dashboard</h1>
        <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LogOut size={18} /> Logout
        </button>
      </header>

      <main className="main-content">
        <div className="stats-card glass-panel">
          <div className="stat-item highlight">
            <span className="stat-value">{Math.round(dailyStats.calories)}</span>
            <span className="stat-label">kcal</span>
          </div>
          <div className="macros-row">
            <div className="macro-item protein">
              <span className="macro-value">{Math.round(dailyStats.protein)}g</span>
              <span className="macro-label">Protein</span>
            </div>
            <div className="macro-item carbs">
              <span className="macro-value">{Math.round(dailyStats.carbs)}g</span>
              <span className="macro-label">Carbs</span>
            </div>
            <div className="macro-item fat">
              <span className="macro-value">{Math.round(dailyStats.fat)}g</span>
              <span className="macro-label">Fat</span>
            </div>
          </div>
        </div>

        <div className="logs-section">
          <h2>Recent Meals</h2>
          <div className="logs-list">
            {logs.length === 0 && (
              <div className="empty-state">
                <p>No meals logged yet today.</p>
                <p>Snap a photo to get started!</p>
              </div>
            )}
            
            {logs.map((log) => (
              <div key={log.id} className="log-item card fade-in">
                <div className="log-info">
                  <h3>{log.name}</h3>
                  <div className="log-macros">
                    <span>🔥 {Math.round(log.nutrition?.calories || 0)} kcal</span>
                    <span>🥩 {Math.round(log.nutrition?.protein_g || 0)}g P</span>
                  </div>
                </div>
                <button 
                  onClick={() => handleDelete(log.id)}
                  className="delete-button"
                  style={{ background: 'none', border: 'none', color: '#e74c3c', cursor: 'pointer', padding: '0.5rem' }}
                >
                  <Trash2 size={20} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </main>

      <div className="fab-container">
        <button 
          className={`fab-button ${isProcessing ? 'processing' : ''}`}
          onClick={() => fileInputRef.current?.click()}
          disabled={isProcessing}
        >
          <Camera size={28} />
          {isProcessing && <div className="spinner"></div>}
        </button>
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*"
          capture="environment"
          style={{ display: 'none' }}
        />
      </div>
    </div>
  );
}

export default Dashboard;
