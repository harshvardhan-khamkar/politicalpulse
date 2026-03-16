import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
    ChevronLeft, Loader2, AlertCircle, MapPin, Landmark, Twitter,
    Heart, Repeat2, MessageCircle, ExternalLink, TrendingUp, BarChart3
} from 'lucide-react';
import api from '../api/api';

const API_BASE = 'http://127.0.0.1:8000';

// ─── Sentiment badge ──────────────────────────────────────────────────────────

const SentimentDot = ({ label }) => {
    if (!label) return null;
    const map = {
        positive: { bg: 'bg-emerald-500', ring: 'ring-emerald-200' },
        negative: { bg: 'bg-red-500', ring: 'ring-red-200' },
        neutral:  { bg: 'bg-gray-400', ring: 'ring-gray-200' },
    };
    const s = map[label.toLowerCase()] ?? map.neutral;
    return (
        <span className={`inline-block w-2 h-2 rounded-full ${s.bg} ring-2 ${s.ring}`}
              title={label} />
    );
};

// ─── Tweet Row ────────────────────────────────────────────────────────────────

const TweetRow = ({ tweet }) => (
    <div className="flex gap-3 py-3 border-b border-gray-50 last:border-0 group">
        <SentimentDot label={tweet.sentiment_label} />
        <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-700 leading-relaxed line-clamp-2">{tweet.content}</p>
            <div className="flex items-center gap-4 mt-1.5 text-[11px] text-gray-400">
                <span className="flex items-center gap-1">
                    <Heart className="w-3 h-3 text-rose-300" />
                    {(tweet.likes || 0).toLocaleString()}
                </span>
                <span className="flex items-center gap-1">
                    <Repeat2 className="w-3 h-3 text-emerald-300" />
                    {(tweet.retweets || 0).toLocaleString()}
                </span>
                <span className="flex items-center gap-1">
                    <MessageCircle className="w-3 h-3 text-sky-300" />
                    {(tweet.replies || 0).toLocaleString()}
                </span>
                {tweet.url && (
                    <a href={tweet.url} target="_blank" rel="noopener noreferrer"
                       className="ml-auto text-gray-300 hover:text-sky-500 transition-colors">
                        <ExternalLink className="w-3 h-3" />
                    </a>
                )}
            </div>
        </div>
    </div>
);

// ─── Stat Pill ────────────────────────────────────────────────────────────────

const StatPill = ({ icon: Icon, label, value, color }) => (
    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50 border border-gray-100">
        <Icon className="w-4 h-4 flex-shrink-0" style={{ color }} />
        <div>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{label}</p>
            <p className="text-sm font-bold text-gray-800">{value ?? '—'}</p>
        </div>
    </div>
);

// ─── Main Page ────────────────────────────────────────────────────────────────

const LeaderDetailPage = () => {
    const { leaderId } = useParams();
    const navigate = useNavigate();
    const [leader, setLeader] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Tweets
    const [tweets, setTweets] = useState([]);
    const [tweetsLoading, setTweetsLoading] = useState(true);
    const [sentimentFilter, setSentimentFilter] = useState('all');

    useEffect(() => {
        if (!leaderId) return;
        const fetchProfile = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get(`/leaders/${leaderId}/wiki`);
                setLeader(data);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load leader.');
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [leaderId]);

    // Fetch tweets once we have the leader identity
    useEffect(() => {
        if (!leader) return;
        const queryHandle = leader.twitter_handle
            ? leader.twitter_handle.replace('@', '')
            : '';
        const fetchTweets = async () => {
            setTweetsLoading(true);
            try {
                const params = { platform: 'twitter', limit: 50, days: 365 };
                if (queryHandle) {
                    params.username = queryHandle;
                } else if (leader.name) {
                    params.leader_name = leader.name;
                }
                const { data } = await api.get('/social/posts', {
                    params
                });
                setTweets(Array.isArray(data) ? data : []);
            } catch {
                setTweets([]);
            } finally {
                setTweetsLoading(false);
            }
        };
        fetchTweets();
    }, [leader]);

    // Derived
    const displayedTweets = sentimentFilter === 'all'
        ? tweets
        : tweets.filter(t => t.sentiment_label?.toLowerCase() === sentimentFilter);

    const sentimentCounts = tweets.reduce((acc, t) => {
        const lbl = t.sentiment_label?.toLowerCase() || 'neutral';
        acc[lbl] = (acc[lbl] || 0) + 1;
        return acc;
    }, {});
    const totalTweets = tweets.length;
    const positiveRate = totalTweets ? ((sentimentCounts.positive || 0) / totalTweets * 100).toFixed(0) : 0;
    const negativeRate = totalTweets ? ((sentimentCounts.negative || 0) / totalTweets * 100).toFixed(0) : 0;

    // ──────────────────────────────────────────────────────────────────────────

    if (loading) {
        return (
            <div className="flex items-center justify-center py-24 gap-3 text-indigo-500">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="text-sm font-medium">Loading profile...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-4">
                <button onClick={() => navigate(-1)}
                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 font-medium">
                    <ChevronLeft className="w-4 h-4" /> Back
                </button>
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            </div>
        );
    }

    if (!leader) return null;

    const accent = leader.party_color_hex ?? '#6366f1';
    const photoSrc = leader.photo_url
        ? (leader.photo_url.startsWith('http') ? leader.photo_url : `${API_BASE}${leader.photo_url}`)
        : null;

    return (
        <div className="space-y-6 max-w-5xl">
            {/* Back */}
            <button onClick={() => navigate(-1)}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 transition-colors font-medium">
                <ChevronLeft className="w-4 h-4" /> Leaders
            </button>

            {/* ── Profile Header ── */}
            <div className="relative bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* Banner gradient */}
                <div className="h-28"
                    style={{ background: `linear-gradient(135deg, ${accent}66 0%, ${accent}22 50%, transparent 100%)` }} />

                <div className="px-6 pb-6 -mt-14 relative z-10">
                    <div className="flex flex-col sm:flex-row gap-5">
                        {/* Photo */}
                        <div className="flex-shrink-0">
                            {photoSrc ? (
                                <img src={photoSrc} alt={leader.name}
                                    className="w-24 h-24 rounded-2xl object-cover border-4 border-white shadow-lg"
                                    onError={e => { e.target.style.display = 'none'; }} />
                            ) : (
                                <div className="w-24 h-24 rounded-2xl flex items-center justify-center text-white text-3xl font-bold border-4 border-white shadow-lg"
                                    style={{ backgroundColor: accent }}>
                                    {(leader.name ?? '?')[0]}
                                </div>
                            )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 pt-2">
                            <div className="flex items-start gap-3 flex-wrap mb-1">
                                <h1 className="text-2xl font-bold text-gray-900">{leader.name}</h1>
                                {leader.party_short_name && (
                                    <span className="mt-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full text-white"
                                        style={{ backgroundColor: accent }}>
                                        {leader.party_short_name}
                                    </span>
                                )}
                            </div>
                            {leader.position && (
                                <p className="text-sm text-gray-500 mb-2">{leader.position}</p>
                            )}
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
                                {leader.constituency && (
                                    <span className="flex items-center gap-1">
                                        <Landmark className="w-3 h-3" /> {leader.constituency}
                                    </span>
                                )}
                                {leader.state && (
                                    <span className="flex items-center gap-1">
                                        <MapPin className="w-3 h-3" /> {leader.state}
                                    </span>
                                )}
                                {leader.twitter_handle && (
                                    <a href={`https://twitter.com/${leader.twitter_handle.replace('@', '')}`}
                                       target="_blank" rel="noopener noreferrer"
                                       className="flex items-center gap-1 text-sky-500 hover:underline">
                                        <Twitter className="w-3 h-3" />
                                        @{leader.twitter_handle.replace('@', '')}
                                    </a>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Two-Column Layout ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left: Bio + Election History */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Bio */}
                    {leader.bio && (
                        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                            <h2 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
                                <div className="w-1 h-5 rounded-full" style={{ backgroundColor: accent }} />
                                About
                            </h2>
                            <div className="text-sm text-gray-600 leading-relaxed space-y-2">
                                {leader.bio.split('\n').filter(Boolean).map((p, i) => (
                                    <p key={i}>{p}</p>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Election History */}
                    {leader.election_history && (
                        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                            <h2 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
                                <div className="w-1 h-5 rounded-full" style={{ backgroundColor: accent }} />
                                Election History
                            </h2>
                            <div className="text-sm text-gray-600 leading-relaxed space-y-2">
                                {leader.election_history.split('\n').filter(Boolean).map((p, i) => (
                                    <p key={i}>{p}</p>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Tweets */}
                    <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                            <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
                                <div className="w-1 h-5 rounded-full" style={{ backgroundColor: accent }} />
                                Recent Tweets
                                {!tweetsLoading && tweets.length > 0 && (
                                    <span className="text-xs text-gray-400 font-normal ml-1">
                                        ({tweets.length})
                                    </span>
                                )}
                            </h2>
                            {/* Sentiment pills */}
                            {!tweetsLoading && tweets.length > 0 && (
                                <div className="flex gap-1.5">
                                    {[
                                        { key: 'all',      label: 'All',      color: 'bg-gray-100 text-gray-600' },
                                        { key: 'positive', label: '👍',        color: 'bg-emerald-50 text-emerald-600' },
                                        { key: 'neutral',  label: '😐',        color: 'bg-gray-50 text-gray-500' },
                                        { key: 'negative', label: '👎',        color: 'bg-red-50 text-red-500' },
                                    ].map(f => (
                                        <button key={f.key} onClick={() => setSentimentFilter(f.key)}
                                            className={`px-2 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                                                sentimentFilter === f.key
                                                    ? f.color + ' border-current/20'
                                                    : 'bg-white text-gray-300 border-gray-100 hover:border-gray-300'
                                            }`}>
                                            {f.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="px-6 py-2 max-h-[500px] overflow-y-auto">
                            {tweetsLoading ? (
                                <div className="flex items-center justify-center py-8 text-indigo-400">
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                </div>
                            ) : displayedTweets.length === 0 ? (
                                <p className="text-sm text-gray-400 text-center py-8 italic">
                                    {tweets.length === 0 ? 'No tweets found for this leader.' : 'No tweets match this filter.'}
                                </p>
                            ) : (
                                displayedTweets.slice(0, 30).map((t, i) => (
                                    <TweetRow key={t.id ?? i} tweet={t} />
                                ))
                            )}
                        </div>
                    </section>
                </div>

                {/* Right sidebar */}
                <div className="space-y-6">

                    {/* Sentiment Stats */}
                    {!tweetsLoading && tweets.length > 0 && (
                        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
                            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                Public Sentiment
                            </h3>
                            <div className="space-y-2">
                                <StatPill icon={TrendingUp} label="Positive" value={`${positiveRate}%`} color="#10b981" />
                                <StatPill icon={BarChart3} label="Negative" value={`${negativeRate}%`} color="#ef4444" />
                                <StatPill icon={MessageCircle} label="Total Analyzed" value={totalTweets.toLocaleString()} color={accent} />
                            </div>
                            {/* Mini bar */}
                            <div className="flex rounded-full overflow-hidden h-2 bg-gray-100">
                                {sentimentCounts.positive > 0 && (
                                    <div className="bg-emerald-500 transition-all"
                                        style={{ width: `${positiveRate}%` }} />
                                )}
                                {sentimentCounts.neutral > 0 && (
                                    <div className="bg-gray-300 transition-all"
                                        style={{ width: `${100 - positiveRate - negativeRate}%` }} />
                                )}
                                {sentimentCounts.negative > 0 && (
                                    <div className="bg-red-400 transition-all"
                                        style={{ width: `${negativeRate}%` }} />
                                )}
                            </div>
                        </section>
                    )}

                    {/* Word Clouds */}
                    {leader.wordcloud_url_en && (
                        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                            <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50/50">
                                <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                                    English Word Cloud
                                </span>
                            </div>
                            <img
                                src={`${API_BASE}${leader.wordcloud_url_en}`}
                                alt="English word cloud"
                                className="w-full object-contain max-h-56"
                                onError={e => { e.target.parentElement.style.display = 'none'; }}
                            />
                        </section>
                    )}

                    {leader.wordcloud_url_hi && (
                        <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                            <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50/50">
                                <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                                    Hindi Word Cloud
                                </span>
                            </div>
                            <img
                                src={`${API_BASE}${leader.wordcloud_url_hi}`}
                                alt="Hindi word cloud"
                                className="w-full object-contain max-h-56"
                                onError={e => { e.target.parentElement.style.display = 'none'; }}
                            />
                        </section>
                    )}

                    {/* Party link */}
                    {leader.party_name && (
                        <Link to={`/party-information/${leader.party_id}`}
                            className="block bg-white rounded-2xl border border-gray-100 shadow-sm p-4
                                       hover:shadow-md hover:border-gray-200 transition-all group">
                            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
                                Party
                            </p>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full flex-shrink-0"
                                    style={{ backgroundColor: accent }} />
                                <span className="text-sm font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">
                                    {leader.party_name}
                                </span>
                                <ChevronLeft className="w-4 h-4 text-gray-300 rotate-180 ml-auto
                                              group-hover:translate-x-0.5 transition-transform" />
                            </div>
                        </Link>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LeaderDetailPage;
