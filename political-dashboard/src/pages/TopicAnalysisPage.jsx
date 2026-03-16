import React, { useState, useEffect } from 'react';
import { Loader2, RefreshCw, BarChart3, MessageSquareText } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../api/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const TopicAnalysisPage = () => {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ documentCount: 0, timeframe: 7, modelUsed: 'advanced' });
    const [usingSampleData, setUsingSampleData] = useState(false);
    const [fallbackReason, setFallbackReason] = useState('');

    const fetchTopics = async () => {
        setLoading(true);
        setUsingSampleData(false);
        setFallbackReason('');
        try {
            const { data } = await api.get('/nlp/topics?days=7&limit=6&model=advanced&document_limit=120');
            setTopics(data.topics || []);
            setStats({
                documentCount: data.document_count,
                timeframe: data.timeframe_days,
                modelUsed: data.model_used || 'advanced',
            });
        } catch (error) {
            console.error('Error fetching topics:', error);
            try {
                const fallback = await api.get('/nlp/topics?days=7&limit=6&model=basic');
                setTopics(fallback.data.topics || []);
                setStats({
                    documentCount: fallback.data.document_count,
                    timeframe: fallback.data.timeframe_days,
                    modelUsed: fallback.data.model_used || 'basic',
                });
                setFallbackReason(
                    `Advanced ML pipeline unavailable, showing basic NLP topics instead. ${
                        error.response?.data?.detail || ''
                    }`.trim()
                );
            } catch (fallbackError) {
                console.error('Error fetching fallback topics:', fallbackError);
                setUsingSampleData(true);
                setFallbackReason(
                    fallbackError.response?.data?.detail ||
                    error.response?.data?.detail ||
                    'Live topic extraction is currently unavailable.'
                );
                setTopics([
                    { topic_name: 'Budget-Economy', salience_score: 0.35, keywords: ['budget', 'economy', 'tax', 'finance', 'relief'] },
                    { topic_name: 'Election-Rallies', salience_score: 0.25, keywords: ['election', 'vote', 'rally', 'speech', 'crowd'] },
                    { topic_name: 'Infrastructure-Development', salience_score: 0.20, keywords: ['road', 'bridge', 'inauguration', 'development', 'highway'] },
                ]);
                setStats({ documentCount: 0, timeframe: 7, modelUsed: 'sample' });
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTopics();
    }, []);

    // Prepare data for the BarChart
    const chartData = topics.map(t => ({
        name: t.topic_name,
        salience: t.salience_score * 100 // Convert to percentage
    }));

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 border-l-4 border-indigo-500 pl-3">
                        Public Discourse Topics
                    </h1>
                    <p className="text-gray-500 text-sm mt-1 ml-4">
                        Advanced BERTopic + transformer pipeline with automatic fallback to the basic NLP model.
                    </p>
                </div>
                <button
                    onClick={fetchTopics}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh NLP Extraction
                </button>
            </div>

            {usingSampleData && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    Showing sample fallback topics. {fallbackReason}
                </div>
            )}

            {!usingSampleData && fallbackReason && (
                <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800">
                    {fallbackReason}
                </div>
            )}

            {loading ? (
                <div className="flex flex-col items-center justify-center h-64 bg-white rounded-xl shadow-sm border border-gray-100">
                    <Loader2 className="w-10 h-10 animate-spin text-indigo-600 mb-4" />
                    <p className="text-gray-500 font-medium animate-pulse">Running advanced ML topic extraction...</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column: Chart */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                            <h2 className="text-lg font-semibold text-gray-800 mb-6 flex items-center gap-2">
                                <BarChart3 className="w-5 h-5 text-indigo-500" />
                                Topic Salience (Last {stats.timeframe} Days)
                            </h2>
                            <div className="h-[350px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                        <XAxis type="number" tickFormatter={(v) => `${v}%`} />
                                        <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12, fill: '#4b5563' }} />
                                        <Tooltip
                                            formatter={(value) => [`${value.toFixed(1)}%`, 'Salience Weight']}
                                            cursor={{ fill: '#f3f4f6' }}
                                        />
                                        <Bar dataKey="salience" radius={[0, 4, 4, 0]}>
                                            {chartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Keyword Clouds */}
                    <div className="space-y-4">
                        <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl p-5 text-white shadow-md">
                            <h3 className="font-semibold text-lg opacity-90">Analysis Stats</h3>
                            <div className="mt-4 grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-indigo-100 text-xs uppercase tracking-wider">Documents Analyzed</p>
                                    <p className="text-2xl font-bold">{stats.documentCount.toLocaleString()}</p>
                                </div>
                                <div>
                                    <p className="text-indigo-100 text-xs uppercase tracking-wider">Topics Found</p>
                                    <p className="text-2xl font-bold">{topics.length}</p>
                                </div>
                            </div>
                            <div className="mt-4">
                                <p className="text-indigo-100 text-xs uppercase tracking-wider">Model</p>
                                <p className="text-lg font-bold capitalize">{stats.modelUsed}</p>
                            </div>
                        </div>

                        {topics.map((topic, i) => (
                            <div key={i} className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                                <div className="flex justify-between items-start mb-3">
                                    <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                                        <MessageSquareText className="w-4 h-4" style={{ color: COLORS[i % COLORS.length] }} />
                                        {topic.topic_name}
                                    </h3>
                                    <span className="text-xs font-bold px-2 py-1 rounded bg-gray-100 text-gray-600">
                                        {(topic.salience_score * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {topic.keywords.map((kw, idx) => (
                                        <span key={idx} className="px-2.5 py-1 text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200 rounded-full">
                                            {kw}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TopicAnalysisPage;
