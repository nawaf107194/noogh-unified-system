import React, { createContext, useState, useContext, useEffect } from 'react';
import dashboardAPI from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('noogh_token'));
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (token) {
            loadUser();
        } else {
            setLoading(false);
        }
    }, [token]);

    const loadUser = async () => {
        try {
            const userData = await dashboardAPI.getCurrentUser();
            setUser(userData);
            setError(null);
        } catch (err) {
            console.error('Failed to load user:', err);
            // Token might be expired or invalid
            logout();
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        try {
            setError(null);
            const data = await dashboardAPI.login(username, password);

            setToken(data.access_token);
            localStorage.setItem('noogh_token', data.access_token);

            // Load user info after successful login
            await loadUser();

            return { success: true };
        } catch (err) {
            const errorMsg = err.message || 'Login failed';
            setError(errorMsg);
            return { success: false, error: errorMsg };
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        setError(null);
        localStorage.removeItem('noogh_token');
    };

    const value = {
        user,
        token,
        loading,
        error,
        login,
        logout,
        isAuthenticated: !!token && !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
