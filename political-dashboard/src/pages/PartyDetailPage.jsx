import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ChevronLeft, Loader2, AlertCircle, ExternalLink,
    Users, MapPin, BarChart2, Award, Twitter, Heart, Repeat2, MessageCircle
} from 'lucide-react';
import api from '../api/api';

const API_BASE = 'http://127.0.0.1:8000';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SectionHeading = ({ title }) => (
    <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-100">{title}</h2>
);

const ProseText = ({ text }) => {
    if (!text) return null;
    return (
        <div className="text-sm text-gray-700 leading-relaxed space-y-3">
            {text.split('\n').filter(Boolean).map((para, i) => (
                <p key={i}>{para}</p>
            ))}
        </div>
    );
};

const StatCard = ({ icon: Icon, label, value, accent }) => (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: `${accent}18` }}>
            <Icon className="w-4 h-4" style={{ color: accent }} />
        </div>
        <div>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
            <p className="text-base font-bold text-gray-900">{value ?? '—'}</p>
        </div>
    </div>
);

// ─── Leaders Grid ─────────────────────────────────────────────────────────────

const LeaderCard = ({ leader, accent }) => {
    const [imgError, setImgError] = useState(false);
    const photoSrc = leader.photo_url ? `${API_BASE}${leader.photo_url}` : null;

    return (
        <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow">
            {photoSrc && !imgError ? (
                <img
                    src={photoSrc}
                    alt={leader.name}
                    className="w-14 h-14 rounded-full object-cover flex-shrink-0 border border-gray-100"
                    onError={() => setImgError(true)}
                />
            ) : (
                <div className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-base flex-shrink-0"
                    style={{ backgroundColor: accent }}>
                    {(leader.name ?? '?')[0].toUpperCase()}
                </div>
            )}
            <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{leader.name}</p>
                {leader.position && (
                    <p className="text-xs text-gray-400 truncate">{leader.position}</p>
                )}
                {leader.twitter && (
                    <a href={`https://twitter.com/${leader.twitter.replace('@', '')}`}
                        target="_blank" rel="noopener noreferrer"
                        className="text-[10px] text-blue-500 hover:underline">
                        @{leader.twitter.replace('@', '')}
                    </a>
                )}
            </div>
        </div>
    );
};

// ─── Sentiment Badge ──────────────────────────────────────────────────────────

const SentimentBadge = ({ label }) => {
    if (!label) return null;
    const map = {
        positive:  { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
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

// ─── Tweet Card ───────────────────────────────────────────────────────────────

const TweetCard = ({ tweet }) => (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-col gap-3 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
                <div className="w-8 h-8 rounded-full bg-sky-100 flex items-center justify-center flex-shrink-0">
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
                <SentimentBadge label={tweet.sentiment_label} />
                {tweet.url && (
                    <a href={tweet.url} target="_blank" rel="noopener noreferrer"
                        className="text-gray-300 hover:text-sky-500 transition-colors">
                        <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                )}
            </div>
        </div>

        {/* Content */}
        <p className="text-sm text-gray-700 leading-relaxed line-clamp-4">{tweet.content}</p>

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
            {tweet.sentiment_score != null && (
                <span className="ml-auto font-medium text-gray-500">
                    Score: {Number(tweet.sentiment_score).toFixed(2)}
                </span>
            )}
        </div>
    </div>
);

// ─── Top Tweets Section ───────────────────────────────────────────────────────

const TopTweets = ({ partyName, partyShortName }) => {
    const [tweets, setTweets]         = useState([]);
    const [loading, setLoading]       = useState(true);
    const [filter, setFilter]         = useState('all'); // all | positive | negative | neutral
    const [sourceFilter, setSource]   = useState('all'); // all | political | public

    useEffect(() => {
        if (!partyName) return;
        const fetchTweets = async () => {
            setLoading(true);
            try {
                // Try short_name first for data richness, fallback to full name
                const key = partyShortName || partyName;
                const params = { platform: 'twitter', party: key, limit: 50, days: 90 };
                if (sourceFilter !== 'all') params.source_type = sourceFilter;
                const { data } = await api.get('/social/posts', { params });
                setTweets(Array.isArray(data) ? data : []);
            } catch {
                setTweets([]);
            } finally {
                setLoading(false);
            }
        };
        fetchTweets();
    }, [partyName, partyShortName, sourceFilter]);

    const displayed = filter === 'all'
        ? tweets
        : tweets.filter(t => t.sentiment_label?.toLowerCase() === filter);

    // Sentiment counts
    const counts = tweets.reduce((acc, t) => {
        const lbl = t.sentiment_label?.toLowerCase() || 'neutral';
        acc[lbl] = (acc[lbl] || 0) + 1;
        return acc;
    }, {});

    const FILTERS = [
        { key: 'all',      label: 'All',      color: 'bg-gray-100 text-gray-700 border-gray-200' },
        { key: 'positive', label: 'Positive', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
        { key: 'neutral',  label: 'Neutral',  color: 'bg-gray-50 text-gray-600 border-gray-200' },
        { key: 'negative', label: 'Negative', color: 'bg-red-50 text-red-700 border-red-200' },
    ];

    return (
        <section>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 pb-2 border-b border-gray-100">
                <h2 className="text-xl font-semibold text-gray-900">
                    Top Tweets
                    {!loading && tweets.length > 0 && (
                        <span className="ml-2 text-sm font-normal text-gray-400">{tweets.length} tweets</span>
                    )}
                </h2>
                {/* Source toggle */}
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 font-medium">Source:</span>
                    {['all', 'political', 'public'].map(s => (
                        <button key={s} onClick={() => setSource(s)}
                            className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-colors ${
                                sourceFilter === s
                                    ? 'bg-sky-600 text-white border-sky-600'
                                    : 'bg-white text-gray-500 border-gray-200 hover:border-sky-300'
                            }`}>
                            {s.charAt(0).toUpperCase() + s.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Sentiment filter pills */}
            {!loading && tweets.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                    {FILTERS.map(f => (
                        <button key={f.key} onClick={() => setFilter(f.key)}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                                filter === f.key
                                    ? f.color + ' shadow-sm'
                                    : 'bg-white text-gray-400 border-gray-200 hover:border-gray-300'
                            }`}>
                            {f.label}
                            <span className="opacity-60">
                                ({f.key === 'all' ? tweets.length : (counts[f.key] || 0)})
                            </span>
                        </button>
                    ))}
                </div>
            )}

            {loading ? (
                <div className="flex items-center justify-center py-10 gap-3 text-sky-500">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="text-sm font-medium">Loading tweets...</span>
                </div>
            ) : displayed.length === 0 ? (
                <div className="rounded-xl border border-dashed border-gray-200 p-8 text-center text-sm text-gray-400 italic">
                    {tweets.length === 0 ? 'No tweets found for this party.' : 'No tweets match the selected filter.'}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {displayed.slice(0, 20).map((t, i) => (
                        <TweetCard key={t.id ?? i} tweet={t} />
                    ))}
                </div>
            )}
        </section>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PartyDetailPage = () => {
    const { partyId } = useParams();
    const navigate = useNavigate();
    const [party, setParty] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!partyId) return;
        const fetchParty = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get(`/parties/${partyId}/wiki`);
                setParty(data);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load party details.');
            } finally {
                setLoading(false);
            }
        };
        fetchParty();
    }, [partyId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-24 gap-3 text-blue-600">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="text-sm font-medium">Loading party details...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-4">
                <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors font-medium">
                    <ChevronLeft className="w-4 h-4" /> Back
                </button>
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            </div>
        );
    }

    if (!party) return null;

    const accent = party.color_hex ?? '#3b82f6';
    const leaders = Array.isArray(party.leaders) ? party.leaders : [];

    return (
        <div className="space-y-8 max-w-4xl">
            {/* Back */}
            <button onClick={() => navigate(-1)}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors font-medium">
                <ChevronLeft className="w-4 h-4" /> Party Information
            </button>

            {/* ── Header Card ── */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* Top accent strip */}
                <div className="h-1.5 w-full" style={{ backgroundColor: accent }} />

                <div className="p-6 flex flex-col sm:flex-row gap-5">
                    {/* Logo */}
                    <div className="flex-shrink-0">
                        {party.logo_url ? (
                            <img
                                src={`${API_BASE}${party.logo_url}`}
                                alt={party.name}
                                className="w-20 h-20 object-contain rounded border border-gray-100 mr-4"
                                onError={e => { e.target.style.display = 'none'; }}
                            />
                        ) : (
                            <div className="w-20 h-20 rounded-xl flex items-center justify-center text-white text-2xl font-bold"
                                style={{ backgroundColor: accent }}>
                                {(party.short_name ?? party.name ?? '?')[0]}
                            </div>
                        )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-3 flex-wrap mb-2">
                            <h1 className="text-2xl font-bold text-gray-900 leading-tight">{party.name}</h1>
                            {party.short_name && (
                                <span className="mt-1 text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full text-white flex-shrink-0"
                                    style={{ backgroundColor: accent }}>
                                    {party.short_name}
                                </span>
                            )}
                        </div>

                        <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-gray-500">
                            {party.founded_year && (
                                <span><span className="text-gray-400 text-xs uppercase tracking-wide mr-1">Founded</span>{party.founded_year}</span>
                            )}
                            {party.ideology && (
                                <span className="text-gray-600">{party.ideology}</span>
                            )}
                        </div>

                        {party.website && (
                            <a href={party.website} target="_blank" rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 mt-3 text-xs font-medium text-blue-600 hover:underline">
                                <ExternalLink className="w-3 h-3" /> {party.website}
                            </a>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Stats Strip ── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={MapPin} label="States Won" value={party.states_won} accent={accent} />
                <StatCard icon={Users} label="Total MPs" value={party.total_mps} accent={accent} />
                <StatCard icon={Award} label="Total MLAs" value={party.total_mlas} accent={accent} />
                <StatCard icon={BarChart2} label="Vote Share" value={party.vote_share_percentage != null ? `${party.vote_share_percentage}%` : null} accent={accent} />
            </div>

            {/* ── Overview ── */}
            {party.overview && (
                <section>
                    <SectionHeading title="Overview" />
                    <ProseText text={party.overview} />
                </section>
            )}

            {/* ── History ── */}
            {party.history && (
                <section>
                    <SectionHeading title="History" />
                    <ProseText text={party.history} />
                </section>
            )}

            {/* ── Policies ── */}
            {party.policies && (
                <section>
                    <SectionHeading title="Policies" />
                    <ProseText text={party.policies} />
                </section>
            )}

            {/* ── Leaders ── */}
            {leaders.length > 0 && (
                <section>
                    <SectionHeading title={`Leaders (${leaders.length})`} />
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {leaders.map((l, i) => (
                            <LeaderCard key={l.id ?? i} leader={l} accent={accent} />
                        ))}
                    </div>
                </section>
            )}

            {/* ── Top Tweets ── */}
            <TopTweets partyName={party.name} partyShortName={party.short_name} />

            {/* ── Wordclouds ── */}
            <section>
                <SectionHeading title="Wordclouds" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* English Wordcloud */}
                    {party.wordcloud_image_url_en ? (
                        <div className="rounded-2xl overflow-hidden border border-gray-100 flex flex-col bg-white">
                            <div className="bg-gray-50 px-4 py-2 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                English Discourse
                            </div>
                            <img
                                src={`${API_BASE}${party.wordcloud_image_url_en}`}
                                alt={`${party.name} English wordcloud`}
                                className="w-full object-contain max-h-80"
                                onError={e => { e.target.parentElement.style.display = 'none'; }}
                            />
                        </div>
                    ) : (
                        <div className="rounded-2xl border border-dashed border-gray-200 p-6 flex items-center justify-center text-sm text-gray-400 italic">
                            No English data available.
                        </div>
                    )}

                    {/* Hindi Wordcloud */}
                    {party.wordcloud_image_url_hi ? (
                        <div className="rounded-2xl overflow-hidden border border-gray-100 flex flex-col bg-white">
                            <div className="bg-gray-50 px-4 py-2 border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                Hindi Discourse
                            </div>
                            <img
                                src={`${API_BASE}${party.wordcloud_image_url_hi}`}
                                alt={`${party.name} Hindi wordcloud`}
                                className="w-full object-contain max-h-80"
                                onError={e => { e.target.parentElement.style.display = 'none'; }}
                            />
                        </div>
                    ) : (
                        <div className="rounded-2xl border border-dashed border-gray-200 p-6 flex items-center justify-center text-sm text-gray-400 italic">
                            No Hindi data available.
                        </div>
                    )}
                </div>
            </section>

            {/* ── ECI Chart ── */}
            <section>
                <SectionHeading title="ECI Chart" />
                {party.eci_chart_image_url ? (
                    <div className="rounded-2xl overflow-hidden border border-gray-100">
                        <img
                            src={`${API_BASE}${party.eci_chart_image_url}`}
                            alt={`${party.name} ECI chart`}
                            className="w-full rounded-lg border object-contain max-h-96"
                            onError={e => { e.target.parentElement.style.display = 'none'; }}
                        />
                    </div>
                ) : (
                    <p className="text-sm text-gray-400 italic">ECI performance chart not available.</p>
                )}
            </section>
        </div>
    );
};

export default PartyDetailPage;
