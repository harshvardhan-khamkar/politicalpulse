import React, { useState } from 'react';
import { Loader2, CheckCircle2, AlertCircle, Twitter, MessageSquare, Newspaper, Brain, Image, ShieldCheck } from 'lucide-react';
import api from '../api/api';

// ─── Action config ────────────────────────────────────────────────────────────

const ACTIONS = [
    {
        id: 'twitter',
        label: 'Trigger Twitter Scrape',
        icon: Twitter,
        method: 'post',
        endpoint: '/admin/scrape/twitter',
        color: 'text-sky-600',
        bg: 'bg-sky-50 hover:bg-sky-100 border-sky-200',
    },
    {
        id: 'reddit',
        label: 'Trigger Reddit Scrape',
        icon: MessageSquare,
        method: 'post',
        endpoint: '/admin/scrape/reddit',
        color: 'text-orange-600',
        bg: 'bg-orange-50 hover:bg-orange-100 border-orange-200',
    },
    {
        id: 'news',
        label: 'Fetch News',
        icon: Newspaper,
        method: 'post',
        endpoint: '/admin/fetch/news',
        color: 'text-blue-600',
        bg: 'bg-blue-50 hover:bg-blue-100 border-blue-200',
    },
    {
        id: 'sentiment',
        label: 'Run Sentiment Analysis',
        icon: Brain,
        method: 'post',
        endpoint: '/admin/analyze/sentiment',
        color: 'text-purple-600',
        bg: 'bg-purple-50 hover:bg-purple-100 border-purple-200',
    },
    {
        id: 'wordcloud',
        label: 'Generate Wordcloud',
        icon: Image,
        method: 'post',
        endpoint: '/admin/generate/wordcloud',
        color: 'text-teal-600',
        bg: 'bg-teal-50 hover:bg-teal-100 border-teal-200',
    },
    {
        id: 'status',
        label: 'Check Admin Status',
        icon: ShieldCheck,
        method: 'get',
        endpoint: '/admin/status',
        color: 'text-gray-600',
        bg: 'bg-gray-50 hover:bg-gray-100 border-gray-200',
    },
];

// ─── Single Action Button + Result ────────────────────────────────────────────

const ActionPanel = ({ action }) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);   // { ok: bool, data: any }
    const Icon = action.icon;

    const run = async () => {
        setLoading(true);
        setResult(null);
        try {
            const res = action.method === 'post'
                ? await api.post(action.endpoint)
                : await api.get(action.endpoint);
            setResult({ ok: true, data: res.data });
        } catch (e) {
            setResult({
                ok: false,
                data: e.response?.data ?? { error: e.message },
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${action.bg}`}>
                        <Icon className={`w-4 h-4 ${action.color}`} />
                    </div>
                    <span className="text-sm font-semibold text-gray-800">{action.label}</span>
                </div>

                <button
                    onClick={run}
                    disabled={loading}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-lg border text-sm font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${action.bg} ${action.color}`}
                >
                    {loading
                        ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Running...</>
                        : 'Run'
                    }
                </button>
            </div>

            {result && (
                <div className={`border-t px-4 py-3 ${result.ok ? 'border-green-100 bg-green-50' : 'border-red-100 bg-red-50'}`}>
                    <div className={`flex items-center gap-1.5 text-xs font-semibold mb-2 ${result.ok ? 'text-green-600' : 'text-red-600'}`}>
                        {result.ok
                            ? <><CheckCircle2 className="w-3.5 h-3.5" /> Success</>
                            : <><AlertCircle className="w-3.5 h-3.5" /> Failed</>
                        }
                    </div>
                    <pre className="text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap break-words max-h-48 font-mono leading-relaxed">
                        {JSON.stringify(result.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

// ─── Page ─────────────────────────────────────────────────────────────────────

const AdminDashboardPage = () => (
    <div className="space-y-6 max-w-3xl">
        <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Control Panel</h1>
            <p className="text-sm text-gray-400 mt-1">Trigger backend jobs and monitor system actions.</p>
        </div>

        <div className="space-y-4">
            {ACTIONS.map(action => (
                <ActionPanel key={action.id} action={action} />
            ))}
        </div>
    </div>
);

export default AdminDashboardPage;
