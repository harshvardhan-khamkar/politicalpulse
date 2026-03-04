import React, { useState, useEffect, useCallback } from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../../api/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtDate = (str) => {
    if (!str) return '—';
    try { return new Date(str).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch { return str; }
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const SectionCard = ({ title, color, children }) => (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className={`px-5 py-3 border-b border-gray-100 ${color}`}>
            <h2 className="text-xs font-bold uppercase tracking-widest text-white">{title}</h2>
        </div>
        <div className="p-5 grid grid-cols-2 gap-x-8 gap-y-3">
            {children}
        </div>
    </div>
);

const Row = ({ label, value }) => (
    <div className="flex flex-col">
        <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold mb-0.5">{label}</span>
        <span className="text-sm font-bold text-gray-900">
            {value === true ? '✓ Yes' : value === false ? '✗ No' : (value ?? '—')}
        </span>
    </div>
);

// ─── Page ─────────────────────────────────────────────────────────────────────

const AdminDashboard = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchStatus = useCallback(async () => {
        setLoading(true); setError('');
        try {
            const { data } = await api.get('/admin/status');
            setStatus(data);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || 'Failed to fetch status.');
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchStatus(); }, [fetchStatus]);

    const m = status?.metrics;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                    <p className="text-sm text-gray-400 mt-1">Live system metrics from <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">/admin/status</code></p>
                </div>
                <button onClick={fetchStatus} disabled={loading}
                    className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors disabled:opacity-50">
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
                </button>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-blue-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Fetching status...</span>
                </div>
            )}

            {/* Error */}
            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {/* Metric cards */}
            {!loading && !error && status && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">

                    {/* Users */}
                    <SectionCard title="Users" color="bg-blue-600">
                        <Row label="Total Users" value={m?.users?.total ?? 0} />
                        <Row label="Active" value={m?.users?.active ?? 0} />
                        <Row label="Admins" value={m?.users?.admins ?? 0} />
                        <Row label="Registered (7 days)" value={m?.users?.registered_last_7_days ?? 0} />
                    </SectionCard>

                    {/* Polls */}
                    <SectionCard title="Polls" color="bg-violet-600">
                        <Row label="Total Polls" value={m?.polls?.total ?? 0} />
                        <Row label="Active" value={m?.polls?.active ?? 0} />
                        <Row label="Closed" value={m?.polls?.closed ?? 0} />
                        <Row label="Total Votes" value={m?.polls?.total_votes ?? 0} />
                    </SectionCard>

                    {/* Parties */}
                    <SectionCard title="Parties" color="bg-orange-500">
                        <Row label="Total Parties" value={m?.parties?.total_parties ?? 0} />
                        <Row label="Total Leaders" value={m?.parties?.total_leaders ?? 0} />
                        <Row label="With Logo" value={m?.parties?.with_logo_image ?? 0} />
                        <Row label="With ECI Chart" value={m?.parties?.with_eci_chart_image ?? 0} />
                    </SectionCard>

                    {/* Social Media */}
                    <SectionCard title="Social Media" color="bg-sky-500">
                        <Row label="Twitter Posts" value={m?.social_media?.twitter_posts ?? 0} />
                        <Row label="Reddit Posts" value={m?.social_media?.reddit_posts ?? 0} />
                        <Row label="Total Posts" value={m?.social_media?.total_posts ?? 0} />
                        <Row label="Pending Sentiment" value={m?.social_media?.pending_sentiment?.total ?? 0} />
                        <Row label="Latest Twitter" value={fmtDate(m?.social_media?.latest_post_at?.twitter)} />
                        <Row label="Latest Reddit" value={fmtDate(m?.social_media?.latest_post_at?.reddit)} />
                    </SectionCard>

                    {/* Predictions */}
                    <SectionCard title="Predictions" color="bg-emerald-600">
                        <Row label="Total Predictions" value={m?.predictions?.total ?? 0} />
                        <Row label="Valid Now" value={m?.predictions?.valid_now ?? 0} />
                    </SectionCard>

                    {/* News Cache */}
                    <SectionCard title="News Cache" color="bg-pink-500">
                        <Row label="India Politics" value={m?.news_cache?.india_politics?.count ?? 0} />
                        <Row label="India Expired" value={m?.news_cache?.india_politics?.is_expired ?? false} />
                        <Row label="Geopolitics" value={m?.news_cache?.geopolitics?.count ?? 0} />
                        <Row label="Geopolitics Expired" value={m?.news_cache?.geopolitics?.is_expired ?? false} />
                    </SectionCard>

                    {/* Elections */}
                    <SectionCard title="Elections" color="bg-amber-500">
                        <Row label="Total Results" value={m?.elections?.total_results ?? 0} />
                        <Row label="States" value={m?.elections?.states ?? 0} />
                        <Row label="Years" value={m?.elections?.years ?? 0} />
                    </SectionCard>

                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
