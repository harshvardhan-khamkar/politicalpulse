import React, { useEffect, useState, useCallback } from 'react';
import { Loader2, RefreshCw, Brain, Tags, Activity, Target } from 'lucide-react';
import api from '../api/api';

const StatCard = ({ icon: Icon, label, value, tone }) => (
    <div className={`rounded-2xl border p-5 shadow-sm ${tone}`}>
        <div className="flex items-center gap-2 text-sm font-semibold">
            <Icon className="w-4 h-4" />
            {label}
        </div>
        <div className="mt-3 text-3xl font-bold">{value}</div>
    </div>
);

const InsightsPage = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [data, setData] = useState(null);

    const fetchInsights = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const { data } = await api.get('/nlp/advanced-analysis?days=7&platform=all&document_limit=120&topic_limit=5&sample_limit=8');
            setData(data);
        } catch (err) {
            console.error('Error fetching advanced insights:', err);
            setData(null);
            setError(err.response?.data?.detail || 'Advanced ML analysis is currently unavailable.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchInsights();
    }, [fetchInsights]);

    const sentimentBreakdown = data?.sentiment_breakdown || {};
    const alignmentBreakdown = data?.alignment_breakdown || {};
    const topics = data?.topics || [];
    const documents = data?.documents || [];
    const alignmentTraining = data?.alignment_training;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 border-l-4 border-cyan-500 pl-3">
                        Advanced ML Insights
                    </h1>
                    <p className="text-gray-500 text-sm mt-1 ml-4">
                        Transformer sentiment, BERTopic clustering, and alignment inference on recent discourse.
                    </p>
                </div>
                <button
                    onClick={fetchInsights}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-cyan-50 text-cyan-700 rounded-lg hover:bg-cyan-100 transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh Insights
                </button>
            </div>

            {loading && (
                <div className="flex flex-col items-center justify-center h-72 bg-white rounded-xl shadow-sm border border-gray-100">
                    <Loader2 className="w-10 h-10 animate-spin text-cyan-600 mb-4" />
                    <p className="text-gray-500 font-medium animate-pulse">Running advanced political discourse pipeline...</p>
                </div>
            )}

            {!loading && error && (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            {!loading && data && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <StatCard
                            icon={Brain}
                            label="Documents Analyzed"
                            value={data.document_count?.toLocaleString?.() ?? data.document_count ?? 0}
                            tone="bg-cyan-50 border-cyan-100 text-cyan-800"
                        />
                        <StatCard
                            icon={Tags}
                            label="Topics Found"
                            value={topics.length}
                            tone="bg-indigo-50 border-indigo-100 text-indigo-800"
                        />
                        <StatCard
                            icon={Target}
                            label="Alignment Model"
                            value={alignmentTraining?.status || 'unknown'}
                            tone="bg-emerald-50 border-emerald-100 text-emerald-800"
                        />
                    </div>

                    {alignmentTraining?.reason && (
                        <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800">
                            {alignmentTraining.reason}
                        </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 space-y-6">
                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <Tags className="w-5 h-5 text-cyan-500" />
                                    BERTopic Themes
                                </h2>
                                <div className="space-y-4">
                                    {topics.length === 0 ? (
                                        <p className="text-sm text-gray-400">No advanced topics were extracted from the current batch.</p>
                                    ) : (
                                        topics.map((topic) => (
                                            <div key={topic.topic_id} className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                                                <div className="flex items-center justify-between gap-3">
                                                    <div>
                                                        <h3 className="font-semibold text-gray-900">{topic.topic_name}</h3>
                                                        <p className="text-xs text-gray-400 mt-1">
                                                            Topic ID {topic.topic_id} · {topic.document_count} documents
                                                        </p>
                                                    </div>
                                                    <span className="text-xs font-bold px-2 py-1 rounded bg-white border border-gray-200 text-gray-600">
                                                        {(topic.salience_score * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div className="flex flex-wrap gap-2 mt-3">
                                                    {topic.keywords.map((keyword) => (
                                                        <span
                                                            key={`${topic.topic_id}-${keyword}`}
                                                            className="px-2.5 py-1 text-xs font-medium bg-white text-gray-600 border border-gray-200 rounded-full"
                                                        >
                                                            {keyword}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-cyan-500" />
                                    Sample Document Inference
                                </h2>
                                <div className="space-y-3">
                                    {documents.length === 0 ? (
                                        <p className="text-sm text-gray-400">No document-level predictions available.</p>
                                    ) : (
                                        documents.map((doc, index) => (
                                            <div key={`${doc.post_id || index}`} className="rounded-xl border border-gray-100 p-4">
                                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                                    <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-100 uppercase">
                                                        {doc.platform}
                                                    </span>
                                                    {doc.party && (
                                                        <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-gray-50 text-gray-600 border border-gray-200 uppercase">
                                                            {doc.party}
                                                        </span>
                                                    )}
                                                    {doc.predicted_alignment && (
                                                        <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100">
                                                            {doc.predicted_alignment}
                                                        </span>
                                                    )}
                                                    {doc.sentiment_label && (
                                                        <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100 uppercase">
                                                            {doc.sentiment_label}
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-700 leading-relaxed">{doc.clean_text}</p>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Breakdown</h2>
                                <div className="space-y-3">
                                    {Object.keys(sentimentBreakdown).length === 0 ? (
                                        <p className="text-sm text-gray-400">No sentiment output available.</p>
                                    ) : (
                                        Object.entries(sentimentBreakdown).map(([label, count]) => (
                                            <div key={label} className="flex items-center justify-between text-sm">
                                                <span className="font-medium text-gray-600 capitalize">{label}</span>
                                                <span className="font-bold text-gray-900">{count}</span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4">Alignment Breakdown</h2>
                                <div className="space-y-3">
                                    {Object.keys(alignmentBreakdown).length === 0 ? (
                                        <p className="text-sm text-gray-400">No alignment output available.</p>
                                    ) : (
                                        Object.entries(alignmentBreakdown).map(([label, count]) => (
                                            <div key={label} className="flex items-center justify-between text-sm">
                                                <span className="font-medium text-gray-600">{label}</span>
                                                <span className="font-bold text-gray-900">{count}</span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default InsightsPage;
