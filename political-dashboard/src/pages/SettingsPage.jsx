import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, LogOut } from 'lucide-react';
import api from '../api/api';

const Field = ({ label, value }) => (
    <div className="grid grid-cols-2 gap-4 py-3 border-b border-gray-100 last:border-0">
        <span className="text-sm text-gray-500">{label}</span>
        <span className="text-sm font-medium text-gray-900">{value ?? '—'}</span>
    </div>
);

const SectionHeader = ({ title }) => (
    <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-4">{title}</p>
);

const SettingsPage = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const { data } = await api.get('/auth/me');
                setUser(data);
            } catch (e) {
                if (e.response?.status === 401) {
                    localStorage.removeItem('access_token');
                    navigate('/login');
                } else {
                    setError(e.response?.data?.detail || 'Failed to load profile.');
                }
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        navigate('/login');
    };

    return (
        <div className="max-w-3xl space-y-10">
            {/* Page title */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                <p className="text-sm text-gray-400 mt-1">Manage your account preferences.</p>
            </div>

            {loading && (
                <div className="flex items-center gap-3 text-blue-600">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="text-sm font-medium">Loading profile...</span>
                </div>
            )}

            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {!loading && user && (
                <>
                    {/* Account Information */}
                    <section>
                        <SectionHeader title="Account Information" />
                        <div className="divide-y divide-gray-100 rounded-xl border border-gray-100 bg-white px-5 py-1 shadow-sm">
                            <Field label="Username" value={user.username} />
                            <Field label="Email" value={user.email} />
                            <Field label="Role" value={user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : null} />
                        </div>
                    </section>

                    {/* Divider */}
                    <hr className="border-gray-100" />

                    {/* Security */}
                    <section>
                        <SectionHeader title="Security" />
                        <div className="flex flex-col items-start gap-2">
                            <button
                                onClick={handleLogout}
                                className="flex items-center gap-2 bg-red-50 hover:bg-red-100 text-red-600 font-semibold text-sm px-5 py-2.5 rounded-lg border border-red-100 transition-colors duration-200"
                            >
                                <LogOut className="w-4 h-4" />
                                Log Out
                            </button>
                            <p className="text-xs text-gray-400">
                                You will be signed out and redirected to the login page.
                            </p>
                        </div>
                    </section>
                </>
            )}
        </div>
    );
};

export default SettingsPage;
