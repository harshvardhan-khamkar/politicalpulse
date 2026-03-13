import React, { useState, useEffect, useCallback } from 'react';
import {
    Twitter, Heart, Repeat2, MessageCircle, ExternalLink,
    Loader2, Search, SlidersHorizontal, X
} from 'lucide-react';
import api from '../api/api';

// ─── Sentiment Badge ─────────────────────────────────────────────────────────

const SentimentBadge = ({ label }) => {
    if (!label) return null;
    const map = {
        positive: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
        negative:  { bg: 'bg-red-50',     text: 'text-red-700',     border: 'border-red-200',     dot: 'bg-red-500'     },
        neutral:   { bg: 'bg-gray-50',    text: 'text-gray-600',    border: 'border-gray-200',    dot: 'bg-gray-400'    },
    };
    const s = map[label.toLowerCase()] ?? map.neutral;
    return (
        <span className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${s.bg} ${s.text} ${s.border}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
            {label}
        </span>
    );
};

// ─── Score Bar ────────────────────────────────────────────────────────────────

const ScoreBar = ({ score, label }) => {
    if (score == null) return null;
    const pct = Math.min(Math.abs(score) * 100, 100);
    const isPos = label?.toLowerCase() === 'positive';
    const isNeg = label?.toLowerCase() === 'negative';
    const barColor = isPos ? 'bg-emerald-400' : isNeg ? 'bg-red-400' : 'bg-gray-300';
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-[11px] font-semibold text-gray-500 w-10 text-right">
                {Number(score).toFixed(2)}
            </span>
        </div>
    );
};

// ─── Tweet Card ──────────────────────────────────────────────────────────────

const TweetCard = ({ tweet }) => (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-col gap-3 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-9 h-9 rounded-full bg-sky-50 border border-sky-100 flex items-center justify-center flex-shrink-0">
                    <Twitter className="w-4 h-4 text-sky-500" />
                </div>
                <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                        {tweet.leader_name || tweet.username || 'Unknown'}
                    </p>
                    {tweet.username && (
                        <p className="text-[11px] text-gray-400 truncate">@{tweet.username}</p>
                    )}
                </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
                {tweet.party && (
                    <span className="text-[10px] font-bold text-gray-400 bg-gray-50 border border-gray-200 px-1.5 py-0.5 rounded-md uppercase">
                        {tweet.party}
                    </span>
                )}
                <SentimentBadge label={tweet.sentiment_label} />
                {tweet.url && (
                    <a href={tweet.url} target="_blank" rel="noopener noreferrer"
                        className="text-gray-300 hover:text-sky-400 transition-colors">
                        <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                )}
            </div>
        </div>

        {/* Content */}
        <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">{tweet.content}</p>

        {/* Score bar */}
        <ScoreBar score={tweet.sentiment_score} label={tweet.sentiment_label} />

        {/* Footer */}
        <div className="flex items-center gap-4 text-xs text-gray-400 pt-1 border-t border-gray-50">
            <span className="flex items-center gap-1">
                <Heart className="w-3.5 h-3.5 text-rose-400" />
                {(tweet.likes || 0).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
                <Repeat2 className="w-3.5 h-3.5 text-emerald-400" />
                {(tweet.retweets || 0).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
                <MessageCircle className="w-3.5 h-3.5 text-sky-400" />
                {(tweet.replies || 0).toLocaleString()}
            </span>
            {tweet.posted_at && (
                <span className="ml-auto text-gray-300">
                    {new Date(tweet.posted_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                </span>
            )}
        </div>
    </div>
);

// ─── Stat Pill ────────────────────────────────────────────────────────────────

const StatPill = ({ label, value, color }) => (
    <div className={`flex flex-col items-center px-5 py-3 rounded-xl border ${color}`}>
        <span className="text-xl font-bold">{value}</span>
        <span className="text-[11px] font-medium opacity-70 uppercase tracking-wider mt-0.5">{label}</span>
    </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────

const SENTIMENT_FILTERS = [
    { key: 'all',      label: 'All',      active: 'bg-gray-800 text-white border-gray-800' },
    { key: 'positive', label: '😊 Positive', active: 'bg-emerald-500 text-white border-emerald-500' },
    { key: 'neutral',  label: '😐 Neutral',  active: 'bg-gray-500 text-white border-gray-500' },
    { key: 'negative', label: '😠 Negative', active: 'bg-red-500 text-white border-red-500' },
];

const DAYS_OPTIONS = [
    { label: '7 days',  value: 7  },
    { label: '30 days', value: 30 },
    { label: '90 days', value: 90 },
];

const TopTweetsPage = () => {
    const [tweets, setTweets]         = useState([]);
    const [loading, setLoading]       = useState(true);
    const [sentiment, setSentiment]   = useState('all');
    const [source, setSource]         = useState('all');
    const [days, setDays]             = useState(30);
    const [partyFilter, setPartyFilter] = useState('');
    const [partyInput, setPartyInput]   = useState('');
    const [showFilters, setShowFilters] = useState(false);

    const fetchTweets = useCallback(async () => {
        setLoading(true);
        try {
            const params = { platform: 'twitter', limit: 100, days };
            if (source !== 'all') params.source_type = source;
            if (sentiment !== 'all') params.sentiment_label = sentiment;
            if (partyFilter.trim()) params.party = partyFilter.trim();
            const { data } = await api.get('/social/posts', { params });
            setTweets(Array.isArray(data) ? data : []);
        } catch {
            setTweets([]);
        } finally {
            setLoading(false);
        }
    }, [sentiment, source, days, partyFilter]);

    useEffect(() => { fetchTweets(); }, [fetchTweets]);

    // Counts
    const counts = tweets.reduce((acc, t) => {
        const l = t.sentiment_label?.toLowerCase() || 'neutral';
        acc[l] = (acc[l] || 0) + 1;
        return acc;
    }, {});

    const avgScore = tweets.length
        ? (tweets.reduce((s, t) => s + (Number(t.sentiment_score) || 0), 0) / tweets.length).toFixed(3)
        : '—';

    const handlePartySearch = (e) => {
        e.preventDefault();
        setPartyFilter(partyInput);
    };

    return (
        <div className="space-y-6">
            {/* ── Header ── */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                        <Twitter className="w-6 h-6 text-sky-500" />
                        Top Tweets
                    </h1>
                    <p className="text-sm text-gray-400 mt-0.5">
                        Political Twitter — sentiment analysis across parties
                    </p>
                </div>
                <button
                    onClick={() => setShowFilters(f => !f)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold border transition-colors ${showFilters ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'}`}>
                    <SlidersHorizontal className="w-4 h-4" />
                    Filters
                </button>
            </div>

            {/* ── Filter Panel ── */}
            {showFilters && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {/* Party search */}
                        <div>
                            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 block">Party</label>
                            <form onSubmit={handlePartySearch} className="flex gap-2">
                                <div className="relative flex-1">
                                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                                    <input
                                        value={partyInput}
                                        onChange={e => setPartyInput(e.target.value)}
                                        placeholder="e.g. BJP, INC…"
                                        className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                {partyFilter && (
                                    <button type="button" onClick={() => { setPartyFilter(''); setPartyInput(''); }}
                                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 border border-gray-200">
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                )}
                                <button type="submit" className="px-3 py-1.5 bg-blue-600 text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors">Go</button>
                            </form>
                        </div>

                        {/* Source */}
                        <div>
                            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 block">Source</label>
                            <div className="flex gap-1.5">
                                {['all', 'political', 'public'].map(s => (
                                    <button key={s} onClick={() => setSource(s)}
                                        className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${source === s ? 'bg-sky-600 text-white border-sky-600' : 'bg-white text-gray-500 border-gray-200 hover:border-sky-300'}`}>
                                        {s.charAt(0).toUpperCase() + s.slice(1)}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Days */}
                        <div>
                            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 block">Time Range</label>
                            <div className="flex gap-1.5">
                                {DAYS_OPTIONS.map(d => (
                                    <button key={d.value} onClick={() => setDays(d.value)}
                                        className={`flex-1 px-2 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${days === d.value ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-500 border-gray-200 hover:border-indigo-300'}`}>
                                        {d.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Stats Strip ── */}
            {!loading && tweets.length > 0 && (
                <div className="flex flex-wrap gap-3">
                    <StatPill label="Total Tweets" value={tweets.length} color="bg-sky-50 border-sky-100 text-sky-700" />
                    <StatPill label="Positive" value={counts.positive || 0} color="bg-emerald-50 border-emerald-100 text-emerald-700" />
                    <StatPill label="Neutral" value={counts.neutral || 0} color="bg-gray-50 border-gray-200 text-gray-600" />
                    <StatPill label="Negative" value={counts.negative || 0} color="bg-red-50 border-red-100 text-red-700" />
                    <StatPill label="Avg Score" value={avgScore} color="bg-violet-50 border-violet-100 text-violet-700" />
                </div>
            )}

            {/* ── Sentiment filter pills ── */}
            <div className="flex flex-wrap gap-2">
                {SENTIMENT_FILTERS.map(f => (
                    <button key={f.key} onClick={() => setSentiment(f.key)}
                        className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold border transition-all ${sentiment === f.key ? f.active : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'}`}>
                        {f.label}
                        {!loading && (
                            <span className="opacity-70 text-[10px]">
                                ({f.key === 'all' ? tweets.length : (counts[f.key] || 0)})
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* ── Content ── */}
            {loading ? (
                <div className="flex items-center justify-center py-20 gap-3 text-sky-500">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Fetching tweets...</span>
                </div>
            ) : tweets.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-200 p-12 text-center space-y-2">
                    <Twitter className="w-8 h-8 text-gray-200 mx-auto" />
                    <p className="text-sm text-gray-400 italic">No tweets found for the selected filters.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {tweets.map((t, i) => (
                        <TweetCard key={t.id ?? i} tweet={t} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default TopTweetsPage;
