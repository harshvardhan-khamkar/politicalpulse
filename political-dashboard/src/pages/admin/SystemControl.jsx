import React, { useState } from 'react';
import { Twitter, MessageSquare, Newspaper, Brain, Loader2, CheckCircle2, AlertCircle, Play } from 'lucide-react';
import api from '../../api/api';

// ─── Action config ────────────────────────────────────────────────────────────

const ACTIONS = [
    {
        id: 'twitter',
        label: 'Trigger Twitter Scrape',
        description: 'Scrape latest political tweets and store in database.',
        icon: Twitter,
        endpoint: '/admin/scrape/twitter',
        iconColor: 'text-sky-500',
        iconBg: 'bg-sky-50',
        btnColor: 'bg-sky-600 hover:bg-sky-700 shadow-sky-200',
    },
    {
        id: 'reddit',
        label: 'Trigger Reddit Scrape',
        description: 'Pull recent political subreddit posts and comments.',
        icon: MessageSquare,
        endpoint: '/admin/scrape/reddit',
        iconColor: 'text-orange-500',
        iconBg: 'bg-orange-50',
        btnColor: 'bg-orange-500 hover:bg-orange-600 shadow-orange-200',
    },
    {
        id: 'news',
        label: 'Fetch News',
        description: 'Pull latest political news from configured sources.',
        icon: Newspaper,
        endpoint: '/admin/fetch/news',
        iconColor: 'text-blue-500',
        iconBg: 'bg-blue-50',
        btnColor: 'bg-blue-600 hover:bg-blue-700 shadow-blue-200',
    },
    {
        id: 'sentiment',
        label: 'Run Sentiment Analysis',
        description: 'Analyse sentiment on recent social and news data.',
        icon: Brain,
        endpoint: '/admin/analyze/sentiment',
        iconColor: 'text-purple-500',
        iconBg: 'bg-purple-50',
        btnColor: 'bg-purple-600 hover:bg-purple-700 shadow-purple-200',
    },
];

// ─── Single Control Card ──────────────────────────────────────────────────────

const ControlCard = ({ action }) => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null); // { ok, data }
    const Icon = action.icon;

    const run = async () => {
        setLoading(true);
        setResult(null);
        try {
            const { data } = await api.post(action.endpoint);
            setResult({ ok: true, data });
        } catch (e) {
            setResult({ ok: false, data: e.response?.data ?? { error: e.message } });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
            {/* Card body */}
            <div className="p-5 flex-1">
                <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${action.iconBg}`}>
                        <Icon className={`w-5 h-5 ${action.iconColor}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 text-sm">{action.label}</h3>
                        <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{action.description}</p>
                    </div>
                </div>

                <button
                    onClick={run}
                    disabled={loading}
                    className={`mt-4 w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-white text-sm font-semibold transition-all shadow-sm disabled:opacity-60 disabled:cursor-not-allowed ${action.btnColor}`}
                >
                    {loading
                        ? <><Loader2 className="w-4 h-4 animate-spin" /> Running...</>
                        : <><Play className="w-3.5 h-3.5" /> Run</>
                    }
                </button>
            </div>

            {/* Result panel */}
            {result && (
                <div className={`border-t px-5 py-4 ${result.ok ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                    <div className={`flex items-center gap-1.5 text-xs font-semibold mb-2 ${result.ok ? 'text-green-600' : 'text-red-600'}`}>
                        {result.ok
                            ? <><CheckCircle2 className="w-3.5 h-3.5" /> Success</>
                            : <><AlertCircle className="w-3.5 h-3.5" /> Failed</>
                        }
                    </div>
                    <pre className="text-xs text-gray-700 font-mono whitespace-pre-wrap break-words max-h-40 overflow-y-auto leading-relaxed">
                        {JSON.stringify(result.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};

// ─── Page ─────────────────────────────────────────────────────────────────────

const SystemControl = () => (
    <div className="space-y-6">
        <div>
            <h1 className="text-2xl font-bold text-gray-900">System Controls</h1>
            <p className="text-sm text-gray-400 mt-1">Trigger backend jobs manually. Each action runs independently.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {ACTIONS.map(action => (
                <ControlCard key={action.id} action={action} />
            ))}
        </div>
    </div>
);

export default SystemControl;
