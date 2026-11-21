import React, { createContext, useContext, useState, useEffect } from 'react';
import API from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token') || null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If token exists, load user profile
    const loadCurrentUser = async () => {
      if (token) {
        try {
          const res = await API.get('/auth/me');
          setUser(res.data);
        } catch (err) {
          console.error("Auth session invalid:", err);
          logout();
        }
      }
      setLoading(false);
    };
    loadCurrentUser();
  }, [token]);

  const login = async (email, password) => {
    const res = await API.post('/auth/login', { email, password });
    const { access_token, user_id, email: userEmail } = res.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    setUser({ id: user_id, email: userEmail });
    return res.data;
  };

  const register = async (email, password) => {
    const res = await API.post('/auth/register', { email, password });
    const { access_token, user_id, email: userEmail } = res.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    setUser({ id: user_id, email: userEmail });
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
