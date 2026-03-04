import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../api/api';

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true); // true on first mount while we rehydrate

    // ── Rehydrate on mount: if token exists, fetch /auth/me ──────────────────
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            setLoading(false);
            return;
        }
        api.get('/auth/me')
            .then(({ data }) => setUser(data))
            .catch(() => {
                // Token invalid / expired — clear it silently
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_role');
                setUser(null);
            })
            .finally(() => setLoading(false));
    }, []);

    // ── login(token) ─────────────────────────────────────────────────────────
    // Call this after a successful POST /auth/login with the token from the response.
    const login = useCallback(async (token) => {
        localStorage.setItem('access_token', token);
        try {
            const { data } = await api.get('/auth/me');
            localStorage.setItem('user_role', data.role ?? '');
            setUser(data);
            return data;
        } catch (e) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            setUser(null);
            throw e;
        }
    }, []);

    // ── logout() ──────────────────────────────────────────────────────────────
    const logout = useCallback(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        setUser(null);
    }, []);

    const isAuthenticated = !!user;
    const isAdmin = user?.is_admin === true || user?.role === 'admin';

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, isAdmin, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

// ─── Hook ─────────────────────────────────────────────────────────────────────

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
};

export default AuthContext;
