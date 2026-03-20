import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { 
    MessageCircle, TrendingUp, TrendingDown, Users, 
    AlertCircle, Search, RefreshCw, Loader2, ListFilter
} from 'lucide-react';
import api from '../api/api';

// ─── Stat Card ───────────────────────────────────────────────────────────────
const StatCard = ({ icon: Icon, label, value, tone }) => (
    <div className={`rounded-2xl border p-5 shadow-sm ${tone}`}>
        <div className="flex items-center gap-2 text-sm font-semibold mb-3">
            <Icon className="w-4 h-4" />
            {label}
        </div>
        <div className="text-3xl font-bold">{value}</div>
    </div>
);

// ─── Score Bar (Stacked) ─────────────────────────────────────────────────────
const StackedScoreBar = ({ positive, neutral, negative, total }) => {
    if (!total || total === 0) return null;
    const posPct = (positive / total) * 100;
    const neuPct = (neutral / total) * 100;
    const negPct = (negative / total) * 100;
    
    return (
        <div className="space-y-1.5 w-full">
            <div className="w-full h-2.5 bg-gray-100 rounded-full flex overflow-hidden">
                <div className="bg-emerald-500 h-full" style={{ width: `${posPct}%` }} />
                <div className="bg-gray-400 h-full" style={{ width: `${neuPct}%` }} />
                <div className="bg-red-500 h-full" style={{ width: `${negPct}%` }} />
            </div>
            <div className="flex justify-between text-[10px] font-bold tracking-wider uppercase text-gray-500">
                <span className="text-emerald-600">{posPct.toFixed(1)}% Pos</span>
                <span className="text-gray-500">{neuPct.toFixed(1)}% Neu</span>
                <span className="text-red-600">{negPct.toFixed(1)}% Neg</span>
            </div>
        </div>
    );
};

// ─── Sentiment Badge ─────────────────────────────────────────────────────────
const SentimentBadge = ({ label }) => {
    if (!label) return null;
    const map = {
        positive: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
        negative: { bg: 'bg-red-50',     text: 'text-red-700',     border: 'border-red-200',     dot: 'bg-red-500'     },
        neutral:  { bg: 'bg-gray-50',    text: 'text-gray-600',    border: 'border-gray-200',    dot: 'bg-gray-400'    },
    };
    const s = map[label.toLowerCase()] ?? map.neutral;
    return (
        <span className={`inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${s.bg} ${s.text} ${s.border}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
            {label}
        </span>
    );
};

const FILTER_PARTIES = ['All', 'BJP', 'INC', 'AAP', 'TMC', 'SP', 'BSP'];
const FILTER_DAYS = [7, 30, 90];
const CHART_PARTIES = ['BJP', 'INC', 'AAP', 'TMC'];
const FILTER_SENTIMENTS = ['All', 'Positive', 'Negative', 'Neutral'];

const PublicSentimentPage = () => {
    // Top-level filters
    const [partyFilter, setPartyFilter] = useState('All');
    const [daysFilter, setDaysFilter] = useState(30);
    
    // UI State
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    
    // Data State
    const [comparisonData, setComparisonData] = useState([]);
    
    // Chart State
    const [chartParty, setChartParty] = useState('BJP');
    const [timelineData, setTimelineData] = useState([]);
    const [chartLoading, setChartLoading] = useState(false);
    
    // Replies State
    const [replies, setReplies] = useState([]);
    const [replyPage, setReplyPage] = useState(1);
    const [hasMoreReplies, setHasMoreReplies] = useState(false);
    const [repliesLoading, setRepliesLoading] = useState(false);
    const [replySentimentFilter, setReplySentimentFilter] = useState('All');

    // ─── Data Fetching ───────────────────────────────────────────────────────
    
    const fetchComparison = async () => {
        const params = { days: daysFilter };
        if (partyFilter !== 'All') params.party = partyFilter;
        const res = await api.get('/social/sentiment/public-comparison', { params });
        return res.data;
    };

    const fetchTimeline = async (party) => {
        const res = await api.get('/social/sentiment/public-timeline', { 
            params: { party, days: daysFilter } 
        });
        return res.data;
    };

    const fetchReplies = async (page = 1, replace = false) => {
        setRepliesLoading(true);
        try {
            const params = { page, limit: 20 };
            if (partyFilter !== 'All') params.party = partyFilter;
            // Note: we fetch all sentiments from API and filter client-side 
            // per user request, but we could pass reply_sentiment_label here.
            
            const res = await api.get('/social/posts/replies', { params });
            const data = res.data;
            
            if (replace) {
                setReplies(data.items || []);
            } else {
                setReplies(prev => [...prev, ...(data.items || [])]);
            }
            setReplyPage(data.page);
            setHasMoreReplies(data.has_more);
        } catch (err) {
            console.error("Replies fetch error", err);
        } finally {
            setRepliesLoading(false);
        }
    };

    // Main universal fetch (on mount or party/days change)
    useEffect(() => {
        const loadAll = async () => {
            setLoading(true);
            setError(false);
            try {
                // Determine which timeline to fetch based on top level filter
                // If top level is 'All', keep using chartParty. If top level is a specific party,
                // force chartParty to be that party temporarily.
                const targetChartParty = (partyFilter !== 'All' && CHART_PARTIES.includes(partyFilter)) 
                    ? partyFilter : chartParty;
                    
                if (targetChartParty !== chartParty) setChartParty(targetChartParty);
                
                const [comp, time] = await Promise.all([
                    fetchComparison(),
                    fetchTimeline(targetChartParty),
                    fetchReplies(1, true)
                ]);
                
                setComparisonData(comp);
                setTimelineData(time);
            } catch (err) {
                if (err.response?.status === 404) {
                    setComparisonData([]);
                    setTimelineData([]);
                    setReplies([]);
                } else {
                    setError(true);
                }
            } finally {
                setLoading(false);
            }
        };
        loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [partyFilter, daysFilter]);

    // Independent Chart Fetch (when only chart party tab changes)
    useEffect(() => {
        if (loading) return; // Prevent double fetch during initial load
        const loadChart = async () => {
            setChartLoading(true);
            try {
                const data = await fetchTimeline(chartParty);
                setTimelineData(data);
            } catch (e) {
                setTimelineData([]);
            } finally {
                setChartLoading(false);
            }
        };
        loadChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [chartParty]);


    // ─── Derived State ───────────────────────────────────────────────────────
    
    // Client-side reply filtering
    const filteredReplies = useMemo(() => {
        if (replySentimentFilter === 'All') return replies;
        return replies.filter(r => 
            r.reply_sentiment_label?.toLowerCase() === replySentimentFilter.toLowerCase()
        );
    }, [replies, replySentimentFilter]);

    // Aggregate stats from comparison data
    const aggregates = useMemo(() => {
        let total = 0, pos = 0, neg = 0, neu = 0;
        let mostPolarised = { party: 'N/A', ratio: 0 };

        comparisonData.forEach(d => {
            const s = d.public_reaction_summary;
            total += Number(s.total || 0);
            pos += Number(s.positive || 0);
            neg += Number(s.negative || 0);
            neu += Number(s.neutral || 0);
            
            const pTotal = Number(s.total || 0);
            if (pTotal >= 10) {
                const ratio = Number(s.negative || 0) / pTotal;
                if (ratio > mostPolarised.ratio) {
                    mostPolarised = { party: d.party, ratio };
                }
            }
        });

        const posPct = total > 0 ? ((pos / total) * 100).toFixed(1) + '%' : '0%';
        const negPct = total > 0 ? ((neg / total) * 100).toFixed(1) + '%' : '0%';

        return {
            totalReplied: total.toLocaleString(),
            positiveRate: posPct,
            negativeRate: negPct,
            polarisedParty: mostPolarised.party !== 'N/A' ? `${mostPolarised.party} (${(mostPolarised.ratio * 100).toFixed(0)}% Neg)` : 'N/A'
        };
    }, [comparisonData]);

    // Are we completely devoid of data? (Has pipeline run?)
    const isCompletelyEmpty = !loading && !error && comparisonData.length === 0 && replies.length === 0;

    // ─── Render ──────────────────────────────────────────────────────────────
    
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-sky-600 gap-4">
                <Loader2 className="w-10 h-10 animate-spin" />
                <p className="font-semibold animate-pulse">Analyzing public reaction pipeline...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-red-700 flex items-center gap-3">
                <AlertCircle className="w-6 h-6" />
                <p className="font-bold">Could not load public sentiment data. Is the pipeline server running?</p>
            </div>
        );
    }

    if (isCompletelyEmpty) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-12 text-center text-gray-500 flex flex-col items-center gap-3 shadow-sm">
                <AlertCircle className="w-10 h-10 text-gray-400" />
                <h3 className="text-lg font-bold text-gray-700">Reply analysis is still running</h3>
                <p className="text-sm">We haven't populated enough verified tweet replies yet. Check back in a few minutes once the APScheduler background job completes its first batch.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* ── Header & Global Filters ── */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Users className="w-6 h-6 text-indigo-500" />
                        Public Reaction
                    </h1>
                    <p className="text-sm text-gray-400 mt-0.5">
                        MiniLM Sentiment Analysis derived directly from Public Tweet Replies
                    </p>
                </div>
                
                <div className="flex items-center gap-4">
                    <div className="flex bg-gray-50 p-1 rounded-xl border border-gray-200">
                        {FILTER_PARTIES.map(p => (
                            <button key={p} onClick={() => setPartyFilter(p)}
                                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${partyFilter === p ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-200'}`}>
                                {p}
                            </button>
                        ))}
                    </div>
                    <div className="flex bg-gray-50 p-1 rounded-xl border border-gray-200">
                        {FILTER_DAYS.map(d => (
                            <button key={d} onClick={() => setDaysFilter(d)}
                                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${daysFilter === d ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-500 hover:bg-gray-200'}`}>
                                {d}d
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Section 1: Stat Cards ── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard icon={MessageCircle} label="Replies Analyzed" value={aggregates.totalReplied} tone="bg-indigo-50 border-indigo-100 text-indigo-800" />
                <StatCard icon={TrendingUp} label="Positive Reaction" value={aggregates.positiveRate} tone="bg-emerald-50 border-emerald-100 text-emerald-800" />
                <StatCard icon={TrendingDown} label="Negative Reaction" value={aggregates.negativeRate} tone="bg-red-50 border-red-100 text-red-800" />
                <StatCard icon={AlertCircle} label="Most Polarised" value={aggregates.polarisedParty} tone="bg-orange-50 border-orange-100 text-orange-800" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* ── Section 2: Stacked Bar Comparison ── */}
                <div className="lg:col-span-1 bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                    <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <ListFilter className="w-5 h-5 text-indigo-500" />
                        Party Breakdown
                    </h2>
                    
                    {comparisonData.length === 0 ? (
                        <p className="text-sm text-gray-400 italic">No party breakdown data available for this timeframe.</p>
                    ) : (
                        <div className="space-y-5">
                            {comparisonData.map(d => (
                                <div key={d.party} className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="font-bold text-sm tracking-wide text-gray-800 uppercase">{d.party}</span>
                                        <span className="text-xs font-bold text-gray-400">{d.tweet_count} Tweets</span>
                                    </div>
                                    <StackedScoreBar 
                                        positive={Number(d.public_reaction_summary?.positive || 0)}
                                        neutral={Number(d.public_reaction_summary?.neutral || 0)}
                                        negative={Number(d.public_reaction_summary?.negative || 0)}
                                        total={Number(d.public_reaction_summary?.total || 0)}
                                    />
                                    <div className="text-[10px] font-semibold text-gray-400 text-right">
                                        Avg Score: <span className={d.avg_public_score > 0 ? 'text-emerald-500' : d.avg_public_score < 0 ? 'text-red-500' : 'text-gray-500'}>
                                            {d.avg_public_score > 0 ? '+' : ''}{d.avg_public_score.toFixed(2)}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Section 3: Time-Series Area Chart ── */}
                <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex flex-col">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-indigo-500" />
                            Public Sentiment Timeline
                        </h2>
                        <div className="flex bg-gray-50 p-1 rounded-xl border border-gray-200">
                            {CHART_PARTIES.map(p => (
                                <button key={p} onClick={() => setChartParty(p)} disabled={chartLoading}
                                    className={`px-3 py-1 text-xs font-bold rounded-lg transition-colors ${chartParty === p ? 'bg-white border border-gray-200 text-indigo-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}>
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>
                    
                    <div className="flex-1 min-h-[250px] relative">
                        {chartLoading && (
                            <div className="absolute inset-0 z-10 bg-white/60 flex items-center justify-center">
                                <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                            </div>
                        )}
                        {timelineData.length === 0 && !chartLoading ? (
                            <div className="absolute inset-0 flex items-center justify-center text-sm text-gray-400 italic">
                                No timeline data points available.
                            </div>
                        ) : (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="posGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                        </linearGradient>
                                        <linearGradient id="negGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                                    <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
                                    <Tooltip 
                                        contentStyle={{ borderRadius: '12px', border: '1px solid #f3f4f6', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                        labelStyle={{ fontWeight: 'bold', color: '#374151', marginBottom: '8px' }}
                                    />
                                    <Area type="monotone" dataKey="positive" name="Positive Replies" stroke="#10b981" fill="url(#posGrad)" strokeWidth={2} />
                                    <Area type="monotone" dataKey="negative" name="Negative Replies" stroke="#ef4444" fill="url(#negGrad)" strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Section 4: Reply Feed ── */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-4 border-b border-gray-50">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <MessageCircle className="w-5 h-5 text-indigo-500" />
                        Reply Feed Stream
                    </h2>
                    
                    <div className="flex gap-2">
                        {FILTER_SENTIMENTS.map(s => (
                            <button key={s} onClick={() => setReplySentimentFilter(s)}
                                className={`px-3 py-1.5 text-[10px] uppercase font-bold tracking-wider rounded-lg transition-colors border ${replySentimentFilter === s ? 'bg-gray-800 text-white border-gray-800' : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'}`}>
                                {s}
                            </button>
                        ))}
                    </div>
                </div>

                {filteredReplies.length === 0 ? (
                    <div className="py-12 text-center text-sm text-gray-400 italic">
                        No replies found for this filter combination.
                    </div>
                ) : (
                    <div className="space-y-3">
                        {filteredReplies.map((r, i) => (
                            <div key={r.reply_id || i} className="p-4 rounded-xl border border-gray-100 bg-gray-50 hover:bg-white transition-colors">
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2 text-xs">
                                        <span className="font-bold text-gray-900">@{r.reply_username || 'unknown'}</span>
                                        <span className="text-gray-400">replying to</span>
                                        {r.party && (
                                            <span className="font-bold px-1.5 py-0.5 rounded text-[10px] bg-white border border-gray-200 text-gray-600 uppercase">
                                                {r.party}
                                            </span>
                                        )}
                                    </div>
                                    <SentimentBadge label={r.reply_sentiment_label} />
                                </div>
                                <p className="text-sm text-gray-800 leading-relaxed mb-3">
                                    {r.reply_content}
                                </p>
                                <div className="flex items-center gap-3 text-[11px] font-bold text-gray-400">
                                    <span className={r.reply_likes > 0 ? 'text-rose-400' : ''}>
                                        ♥ {r.reply_likes.toLocaleString()}
                                    </span>
                                    {r.reply_sentiment_score != null && (
                                        <span>Model Score: {r.reply_sentiment_score.toFixed(2)}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {hasMoreReplies && (
                    <div className="mt-6 flex justify-center">
                        <button 
                            onClick={() => fetchReplies(replyPage + 1, false)}
                            disabled={repliesLoading}
                            className="flex items-center gap-2 px-6 py-2 bg-indigo-50 text-indigo-700 font-bold text-sm rounded-xl hover:bg-indigo-100 transition-colors disabled:opacity-50"
                        >
                            {repliesLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                            Load More Replies
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PublicSentimentPage;
