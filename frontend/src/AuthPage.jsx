import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const endpoint = isLogin ? '/login' : '/register';
    const baseUrl = import.meta.env.VITE_API_URL || 'https://calorie-tracker-deco.onrender.com';

    try {
      let response;
      if (isLogin) {
        // OAuth2 Password Request Form format
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData,
        });
      } else {
        response = await fetch(`${baseUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      if (isLogin) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        navigate('/');
      } else {
        // Automatically switch to login after registration
        setIsLogin(true);
        setError('Registration successful! Please log in.');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="card" style={{ maxWidth: '400px', width: '100%', padding: '2rem' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: 'var(--text)' }}>
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h2>
        
        {error && (
          <div style={{ padding: '0.75rem', marginBottom: '1rem', backgroundColor: error.includes('successful') ? 'rgba(46, 204, 113, 0.2)' : 'rgba(231, 76, 60, 0.2)', color: error.includes('successful') ? '#2ecc71' : '#e74c3c', borderRadius: '8px', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text)' }}
            />
          </div>
          <button type="submit" className="primary-button" style={{ marginTop: '1rem' }}>
            {isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span 
            onClick={() => setIsLogin(!isLogin)} 
            style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {isLogin ? 'Sign up' : 'Login'}
          </span>
        </p>
      </div>
    </div>
  );
}

export default AuthPage;
