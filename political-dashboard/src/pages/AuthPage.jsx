import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Lock, ArrowRight, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../api/api';
import { useAuth } from '../context/AuthContext';

const AuthPage = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();

    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccessMsg('');

        try {
            if (isLogin) {
                const usernameOrEmail = formData.username || formData.email;
                if (!usernameOrEmail) throw new Error('Username or Email is required');
                if (!formData.password) throw new Error('Password is required');

                // FastAPI OAuth2 expects application/x-www-form-urlencoded
                const params = new URLSearchParams();
                params.append('grant_type', 'password');
                params.append('username', usernameOrEmail);
                params.append('password', formData.password);

                const { data } = await api.post('/auth/login', params, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                });

                // Store token + fetch /auth/me → updates AuthContext
                const user = await login(data.access_token);

                setSuccessMsg('Login successful! Redirecting...');
                setTimeout(() => navigate(user?.role === 'admin' ? '/admin' : '/'), 800);

            } else {
                if (formData.password !== formData.confirmPassword) {
                    throw new Error('Passwords do not match');
                }

                await api.post('/auth/register', {
                    username: formData.username,
                    email: formData.email,
                    password: formData.password,
                });

                setSuccessMsg('Registration successful! Please login.');
                setIsLogin(true);
                setFormData({ ...formData, password: '', confirmPassword: '' });
            }
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'An unexpected error occurred';
            setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[85vh] bg-white rounded-3xl overflow-hidden shadow-2xl">
            {/* Left Side - Image */}
            <div className="hidden lg:flex w-1/2 bg-blue-900 relative overflow-hidden">
                <img
                    src="https://images.unsplash.com/photo-1541872703-74c59636a2fd?auto=format&fit=crop&q=80"
                    alt="Political Rally"
                    className="absolute inset-0 w-full h-full object-cover opacity-60 mix-blend-overlay"
                />
                <div className="relative z-10 flex flex-col justify-center px-12 text-white h-full">
                    <h1 className="text-4xl font-bold mb-6 leading-tight">Empowering Democracy Through Data</h1>
                    <p className="text-lg text-blue-100 max-w-lg">
                        Join the platform that brings transparency, real-time analytics, and comprehensive election insights to your fingertips.
                    </p>
                </div>
                <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-blue-500 opacity-20 blur-3xl" />
                <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-red-500 opacity-20 blur-3xl" />
            </div>

            {/* Right Side - Form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative overflow-y-auto">
                <div className="max-w-md w-full">
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-100 text-blue-600 mb-4">
                            <span className="font-bold text-xl">P</span>
                        </div>
                        <h2 className="text-3xl font-bold text-gray-900 mb-2">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h2>
                        <p className="text-gray-500">
                            {isLogin ? 'Enter your credentials to access your dashboard' : 'Get started with your free account today'}
                        </p>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-red-600 font-medium">{error}</p>
                        </div>
                    )}
                    {successMsg && (
                        <div className="mb-6 p-4 rounded-lg bg-green-50 border border-green-100 flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-green-600 font-medium">{successMsg}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {!isLogin && (
                            <div className="relative">
                                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Username</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input type="text" name="username" value={formData.username} onChange={handleChange}
                                        className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                        placeholder="johndoe" required={!isLogin} minLength={3} />
                                </div>
                            </div>
                        )}

                        <div className="relative">
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">
                                {isLogin ? 'Username or Email' : 'Email Address'}
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type={isLogin ? 'text' : 'email'}
                                    name={isLogin ? 'username' : 'email'}
                                    value={isLogin ? formData.username : formData.email}
                                    onChange={handleChange}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                    placeholder={isLogin ? 'john@example.com or johndoe' : 'john@example.com'}
                                    required
                                />
                            </div>
                        </div>

                        <div className="relative">
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input type="password" name="password" value={formData.password} onChange={handleChange}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                    placeholder="••••••••" required minLength={6} />
                            </div>
                        </div>

                        {!isLogin && (
                            <div className="relative">
                                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Confirm Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                    <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange}
                                        className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                        placeholder="••••••••" required={!isLogin} />
                                </div>
                            </div>
                        )}

                        <button type="submit" disabled={loading}
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/30 disabled:opacity-70 disabled:cursor-not-allowed">
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                                <>{isLogin ? 'Sign In' : 'Create Account'}<ArrowRight className="w-5 h-5" /></>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 text-center text-sm text-gray-600">
                        {isLogin ? "Don't have an account? " : 'Already have an account? '}
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(''); setSuccessMsg(''); setFormData({ username: '', email: '', password: '', confirmPassword: '' }); }}
                            className="font-semibold text-blue-600 hover:text-blue-700 transition-colors"
                        >
                            {isLogin ? 'Sign up' : 'Log in'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AuthPage;
