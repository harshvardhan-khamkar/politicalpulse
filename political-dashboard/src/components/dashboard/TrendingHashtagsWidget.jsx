import React, { useEffect, useState, useCallback } from 'react';
import { Hash, TrendingUp, RefreshCw, Flame } from 'lucide-react';
import api from '../../api/api';

// ─── Party color map ──────────────────────────────────────────────────────────

const PARTY_COLORS = {
    BJP: 'bg-orange-100 text-orange-700 border-orange-200',
    INC: 'bg-blue-100 text-blue-700 border-blue-200',
    AAP: 'bg-cyan-100 text-cyan-700 border-cyan-200',
    SP: 'bg-red-100 text-red-700 border-red-200',
    TMC: 'bg-green-100 text-green-700 border-green-200',
    BSP: 'bg-sky-100 text-sky-700 border-sky-200',
    CPIM: 'bg-rose-100 text-rose-700 border-rose-200',
};

const BAR_COLORS = {
    BJP: 'bg-orange-400', INC: 'bg-blue-400', AAP: 'bg-cyan-400',
    SP: 'bg-red-400', TMC: 'bg-green-400', BSP: 'bg-sky-400',
    CPIM: 'bg-rose-400',
};

// ─── Day filter buttons ───────────────────────────────────────────────────────

const DAY_OPTIONS = [
    { label: '1D', value: 1 },
    { label: '7D', value: 7 },
    { label: '30D', value: 30 },
];

// ─── Single hashtag row ───────────────────────────────────────────────────────

const HashtagRow = ({ item, rank, maxCount, compact }) => {
    const pct = maxCount > 0 ? Math.round((item.count / maxCount) * 100) : 0;
    const barColor = BAR_COLORS[item.top_party] || 'bg-gray-400';
    const partyBadge = item.top_party ? (PARTY_COLORS[item.top_party] || 'bg-gray-100 text-gray-600 border-gray-200') : null;

    return (
        <div className={`group flex items-center gap-3 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer ${compact ? 'py-1.5 px-2' : 'py-2.5 px-3'}`}>
            {/* Rank */}
            <span className={`text-[10px] font-bold w-4 text-center flex-shrink-0 ${rank <= 3 ? 'text-amber-500' : 'text-gray-300'}`}>
                {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
            </span>

            {/* Hashtag + bar */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <span className={`font-semibold text-gray-800 truncate ${compact ? 'text-xs' : 'text-sm'}`}>{item.hashtag}</span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                        {partyBadge && (
                            <span className={`text-[8px] font-extrabold px-1 py-0 rounded-full border ${partyBadge}`}>
                                {item.top_party}
                            </span>
                        )}
                        {!compact && <span className="text-xs text-gray-400 font-medium">{item.count.toLocaleString()}</span>}
                    </div>
                </div>
                {/* Progress bar - hide if compact */}
                {!compact && (
                    <div className="h-1 bg-gray-100 rounded-full overflow-hidden mt-1">
                        <div
                            className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                            style={{ width: `${pct}%` }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

// ─── Widget ───────────────────────────────────────────────────────────────────

const TrendingHashtagsWidget = ({ className = '', compact = false }) => {
    const [days, setDays] = useState(1);
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [error, setError] = useState(null);

    const fetch = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.get('/social/trending/hashtags', {
                params: { days, limit: compact ? 8 : 15 }
            });
            setData(res.data?.hashtags || []);
            setLastUpdated(new Date());
        } catch (e) {
            setError('Could not load trending hashtags.');
            setData([]);
        } finally {
            setLoading(false);
        }
    }, [days, compact]);

    // Auto-refresh every 5 minutes
    useEffect(() => {
        fetch();
        const interval = setInterval(fetch, 300_000);
        return () => clearInterval(interval);
    }, [fetch]);

    const maxCount = data.length > 0 ? data[0].count : 1;

    return (
        <div className={`${compact ? 'bg-transparent border-none shadow-none' : 'bg-white rounded-2xl border border-gray-100 shadow-sm'} flex flex-col ${className}`}>
            {/* Header */}
            <div className={`border-b border-gray-50 flex items-center justify-between ${compact ? 'px-2 py-2' : 'px-4 py-4'}`}>
                <div className="flex items-center gap-2">
                    <div className={`rounded-lg bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center flex-shrink-0 ${compact ? 'w-6 h-6' : 'w-8 h-8'}`}>
                        <Flame className={`${compact ? 'w-3 h-3' : 'w-4 h-4'} text-white`} />
                    </div>
                    <div>
                        <h3 className={`font-bold text-gray-900 ${compact ? 'text-xs' : 'text-sm'}`}>Trending</h3>
                        {!compact && <p className="text-[10px] text-gray-400">Latest political hashtags</p>}
                    </div>
                </div>

                <div className="flex items-center gap-1.5">
                    {/* Day filter - simpler in compact */}
                    {!compact ? (
                        <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
                            {DAY_OPTIONS.map(o => (
                                <button
                                    key={o.value}
                                    onClick={() => setDays(o.value)}
                                    className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all
                      ${days === o.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    {o.label}
                                </button>
                            ))}
                        </div>
                    ) : (
                        <select
                            value={days}
                            onChange={(e) => setDays(parseInt(e.target.value))}
                            className="bg-gray-100 border-none rounded text-[10px] font-bold text-gray-500 py-0.5 px-1 outline-none"
                        >
                            {DAY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                    )}
                    {/* Refresh */}
                    <button
                        onClick={fetch}
                        disabled={loading}
                        className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all disabled:opacity-50"
                    >
                        <RefreshCw className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className={`flex-1 ${compact ? 'px-1 py-1' : 'px-2 py-2'}`}>
                {loading && (
                    <div className="flex flex-col gap-1 py-1">
                        {[...Array(compact ? 5 : 8)].map((_, i) => (
                            <div key={i} className={`flex items-center gap-3 ${compact ? 'px-1 py-1.5' : 'px-3 py-2.5'}`}>
                                <div className="w-4 h-2.5 bg-gray-100 rounded animate-pulse" />
                                <div className="flex-1">
                                    <div className="h-2.5 bg-gray-100 rounded animate-pulse w-3/4" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {!loading && error && (
                    <div className="flex flex-col items-center justify-center py-4 text-center">
                        <p className="text-[10px] text-gray-400">{error}</p>
                    </div>
                )}

                {!loading && !error && data.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-6 text-center">
                        <p className="text-[10px] text-gray-400">No data yet.</p>
                    </div>
                )}

                {!loading && !error && data.length > 0 && (
                    <div>
                        {data.map((item, i) => (
                            <HashtagRow key={item.hashtag} item={item} rank={i + 1} maxCount={maxCount} compact={compact} />
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            {lastUpdated && !loading && !compact && (
                <div className="px-4 py-2.5 border-t border-gray-50 text-[10px] text-gray-300">
                    Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            )}
        </div>
    );
};

export default TrendingHashtagsWidget;
