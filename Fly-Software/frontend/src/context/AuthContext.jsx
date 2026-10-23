import { createContext, useState, useEffect, useContext } from 'react';
import api from '../api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkUserStatus();
  }, []);

  const checkUserStatus = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const response = await api.get('accounts/profile/');
        setUser(response.data);
      } catch (error) {
        console.error("Failed to fetch user profile", error);
        localStorage.removeItem('access_token');
        setUser(null);
      }
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    const response = await api.post('accounts/login/', { username, password });
    localStorage.setItem('access_token', response.data.access);
    await checkUserStatus();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
