import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, Search, MapPin, Twitter, ChevronRight } from 'lucide-react';
import api from '../api/api';

const API_BASE = 'http://127.0.0.1:8000';

// ─── Leader Card ──────────────────────────────────────────────────────────────

const LeaderCard = ({ leader, onClick }) => {
    const accent = leader.party_color_hex ?? '#6366f1';
    const [imgError, setImgError] = useState(false);
    const photoSrc = leader.photo_url
        ? (leader.photo_url.startsWith('http') ? leader.photo_url : `${API_BASE}${leader.photo_url}`)
        : null;

    return (
        <button
            onClick={onClick}
            className="group relative w-full text-left bg-white rounded-2xl overflow-hidden
                       border border-gray-100 shadow-sm hover:shadow-xl
                       transition-all duration-300 hover:-translate-y-1"
        >
            {/* Photo / placeholder banner */}
            <div className="relative h-32 overflow-hidden"
                style={{ background: `linear-gradient(135deg, ${accent}22 0%, ${accent}44 100%)` }}>
                {photoSrc && !imgError ? (
                    <img
                        src={photoSrc}
                        alt={leader.name}
                        className="absolute inset-0 w-full h-full object-cover object-top
                                   group-hover:scale-105 transition-transform duration-500"
                        onError={() => setImgError(true)}
                    />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-5xl font-black opacity-20" style={{ color: accent }}>
                            {(leader.name ?? '?')[0].toUpperCase()}
                        </span>
                    </div>
                )}
                {/* Gradient overlay */}
                <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/50 to-transparent" />

                {/* Party pill */}
                {leader.party_short_name && (
                    <span className="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wider
                                     px-2.5 py-1 rounded-full text-white backdrop-blur-sm"
                        style={{ backgroundColor: `${accent}cc` }}>
                        {leader.party_short_name}
                    </span>
                )}
            </div>

            {/* Info */}
            <div className="p-4 pt-3">
                <h3 className="font-bold text-gray-900 text-sm leading-tight mb-0.5
                               group-hover:text-indigo-600 transition-colors">
                    {leader.name}
                </h3>
                {leader.position && (
                    <p className="text-xs text-gray-400 mb-2">{leader.position}</p>
                )}

                <div className="flex items-center gap-3 text-[11px] text-gray-400">
                    {leader.state && (
                        <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" /> {leader.state}
                        </span>
                    )}
                    {leader.twitter_handle && (
                        <span className="flex items-center gap-1 text-sky-500">
                            <Twitter className="w-3 h-3" />
                            @{leader.twitter_handle.replace('@', '')}
                        </span>
                    )}
                </div>

                {/* View arrow */}
                <div className="mt-3 pt-2.5 border-t border-gray-50 flex items-center justify-between text-xs text-gray-300
                                group-hover:text-indigo-500 transition-colors">
                    <span className="font-medium">{leader.party_name ?? 'Independent'}</span>
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </div>
            </div>
        </button>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const LeaderInfoPage = () => {
    const [leaders, setLeaders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [search, setSearch] = useState('');
    const [partyFilter, setPartyFilter] = useState('all');
    const navigate = useNavigate();

    useEffect(() => {
        const fetch = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get('/leaders');
                setLeaders(Array.isArray(data) ? data : []);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load leaders.');
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, []);

    // Derive unique parties for filter pills
    const parties = [...new Map(
        leaders
            .filter(l => l.party_short_name)
            .map(l => [l.party_short_name, { name: l.party_short_name, color: l.party_color_hex }])
    ).values()];

    const filtered = leaders.filter(l => {
        const matchSearch = !search || l.name.toLowerCase().includes(search.toLowerCase());
        const matchParty = partyFilter === 'all' || l.party_short_name === partyFilter;
        return matchSearch && matchParty;
    });

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Politicians & Leaders</h1>
                <p className="text-sm text-gray-400 mt-1">
                    Explore profiles, tweets, and public sentiment for key political figures
                </p>
            </div>

            {/* Search + filters */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
                    <input
                        type="text"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        placeholder="Search leaders..."
                        className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm
                                   focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50/50"
                    />
                </div>

                {parties.length > 0 && (
                    <div className="flex flex-wrap gap-2 items-center">
                        <button
                            onClick={() => setPartyFilter('all')}
                            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                                partyFilter === 'all'
                                    ? 'bg-gray-900 text-white border-gray-900'
                                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                            }`}>
                            All
                        </button>
                        {parties.map(p => (
                            <button
                                key={p.name}
                                onClick={() => setPartyFilter(p.name)}
                                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                                    partyFilter === p.name
                                        ? 'text-white border-transparent'
                                        : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
                                }`}
                                style={partyFilter === p.name ? { backgroundColor: p.color ?? '#6366f1' } : {}}>
                                {p.name}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* States */}
            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-indigo-500">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Loading leaders...</span>
                </div>
            )}

            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {!loading && !error && filtered.length === 0 && (
                <div className="text-center py-20">
                    <p className="text-sm text-gray-400">
                        {leaders.length === 0 ? 'No leaders found.' : 'No leaders match your filters.'}
                    </p>
                </div>
            )}

            {/* Grid */}
            {!loading && !error && filtered.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {filtered.map(l => (
                        <LeaderCard
                            key={l.id}
                            leader={l}
                            onClick={() => navigate(`/leader-info/${l.id}`)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default LeaderInfoPage;
