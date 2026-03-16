import React, { useEffect, useState, useCallback } from 'react';
import { RefreshCw, Flame } from 'lucide-react';
import api from '../../api/api';

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
    BJP: 'bg-orange-400',
    INC: 'bg-blue-400',
    AAP: 'bg-cyan-400',
    SP: 'bg-red-400',
    TMC: 'bg-green-400',
    BSP: 'bg-sky-400',
    CPIM: 'bg-rose-400',
};

const HashtagRow = ({ item, rank, maxScore, compact }) => {
    const score = item.score ?? item.count ?? 0;
    const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
    const barColor = BAR_COLORS[item.top_party] || 'bg-gray-400';
    const partyBadge = item.top_party
        ? (PARTY_COLORS[item.top_party] || 'bg-gray-100 text-gray-600 border-gray-200')
        : null;
    const metricLabel = item.volume_label || (item.count ? item.count.toLocaleString() : null);

    const content = (
        <>
            <span className={`text-[10px] font-bold w-4 text-center flex-shrink-0 ${rank <= 3 ? 'text-amber-500' : 'text-gray-300'}`}>
                {rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank}
            </span>

            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <span className={`font-semibold text-gray-800 truncate ${compact ? 'text-xs' : 'text-sm'}`}>
                        {item.hashtag}
                    </span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                        {partyBadge && (
                            <span className={`text-[8px] font-extrabold px-1 py-0 rounded-full border ${partyBadge}`}>
                                {item.top_party}
                            </span>
                        )}
                        {!compact && metricLabel && (
                            <span className="text-xs text-gray-400 font-medium">{metricLabel}</span>
                        )}
                    </div>
                </div>
                {!compact && (
                    <div className="h-1 bg-gray-100 rounded-full overflow-hidden mt-1">
                        <div
                            className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                            style={{ width: `${pct}%` }}
                        />
                    </div>
                )}
            </div>
        </>
    );

    if (item.url) {
        return (
            <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`group flex items-center gap-3 rounded-xl hover:bg-gray-50 transition-colors ${compact ? 'py-1.5 px-2' : 'py-2.5 px-3'}`}
            >
                {content}
            </a>
        );
    }

    return (
        <div className={`group flex items-center gap-3 rounded-xl hover:bg-gray-50 transition-colors ${compact ? 'py-1.5 px-2' : 'py-2.5 px-3'}`}>
            {content}
        </div>
    );
};

const TrendingHashtagsWidget = ({ className = '', compact = false }) => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [error, setError] = useState(null);
    const [sourceMeta, setSourceMeta] = useState({
        source: null,
        isLive: false,
        location: 'India',
        fallbackReason: null,
    });

    const fetch = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.get('/social/trending/hashtags', {
                params: {
                    live: true,
                    limit: compact ? 8 : 15,
                    country_code: 'IN',
                    hashtags_only: true,
                    days: 1,
                },
            });
            setData(res.data?.hashtags || []);
            setSourceMeta({
                source: res.data?.source || null,
                isLive: Boolean(res.data?.is_live),
                location: res.data?.location || 'India',
                fallbackReason: res.data?.fallback_reason || null,
            });
            setLastUpdated(new Date());
        } catch (e) {
            setError('Could not load Twitter trending hashtags.');
            setData([]);
            setSourceMeta({
                source: null,
                isLive: false,
                location: 'India',
                fallbackReason: null,
            });
        } finally {
            setLoading(false);
        }
    }, [compact]);

    useEffect(() => {
        fetch();
        const interval = setInterval(fetch, 300_000);
        return () => clearInterval(interval);
    }, [fetch]);

    const maxScore = data.length > 0
        ? Math.max(...data.map((item) => item.score ?? item.count ?? 0), 1)
        : 1;

    const sourceLabel = sourceMeta.isLive
        ? `Live on Twitter/X${sourceMeta.location ? ` · ${sourceMeta.location}` : ''}`
        : 'Fallback from stored tweets';

    return (
        <div className={`${compact ? 'bg-transparent border-none shadow-none' : 'bg-white rounded-2xl border border-gray-100 shadow-sm'} flex flex-col ${className}`}>
            <div className={`border-b border-gray-50 flex items-center justify-between ${compact ? 'px-2 py-2' : 'px-4 py-4'}`}>
                <div className="flex items-center gap-2">
                    <div className={`rounded-lg bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center flex-shrink-0 ${compact ? 'w-6 h-6' : 'w-8 h-8'}`}>
                        <Flame className={`${compact ? 'w-3 h-3' : 'w-4 h-4'} text-white`} />
                    </div>
                    <div>
                        <h3 className={`font-bold text-gray-900 ${compact ? 'text-xs' : 'text-sm'}`}>Trending</h3>
                        {!compact && <p className="text-[10px] text-gray-400">{sourceLabel}</p>}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {!compact && (
                        <span
                            className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide ${
                                sourceMeta.isLive
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                        >
                            {sourceMeta.isLive ? 'Live' : 'Fallback'}
                        </span>
                    )}
                    <button
                        onClick={fetch}
                        disabled={loading}
                        className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all disabled:opacity-50"
                    >
                        <RefreshCw className={`${compact ? 'w-3 h-3' : 'w-3.5 h-3.5'} ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>

            {!compact && sourceMeta.fallbackReason && (
                <div className="px-4 py-2 text-[10px] text-amber-700 bg-amber-50 border-b border-amber-100">
                    Live Twitter trends were unavailable, so this list is using stored tweets right now.
                </div>
            )}

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
                        <p className="text-[10px] text-gray-400">No trending hashtags available right now.</p>
                    </div>
                )}

                {!loading && !error && data.length > 0 && (
                    <div>
                        {data.map((item, i) => (
                            <HashtagRow
                                key={`${item.hashtag}-${i}`}
                                item={item}
                                rank={i + 1}
                                maxScore={maxScore}
                                compact={compact}
                            />
                        ))}
                    </div>
                )}
            </div>

            {lastUpdated && !loading && !compact && (
                <div className="px-4 py-2.5 border-t border-gray-50 text-[10px] text-gray-300">
                    Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            )}
        </div>
    );
};

export default TrendingHashtagsWidget;
