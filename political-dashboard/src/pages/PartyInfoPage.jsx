import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, Loader2, AlertCircle, Users, BarChart2 } from 'lucide-react';
import api from '../api/api';

// ─── Party Card ───────────────────────────────────────────────────────────────

const PartyCard = ({ party, onClick }) => {
    const accent = party.color_hex ?? '#94a3b8';
    const voteShare = Math.min(Number(party.vote_share_percentage ?? 0), 100);

    return (
        <button
            onClick={onClick}
            className="w-full text-left bg-white rounded-2xl border border-gray-100 shadow-sm
                       hover:shadow-lg hover:-translate-y-1 hover:border-gray-200
                       transition-all duration-200 overflow-hidden group"
        >
            {/* Left accent border */}
            <div className="flex h-full">
                <div className="w-1 flex-shrink-0" style={{ backgroundColor: accent }} />

                <div className="flex-1 p-5">
                    {/* Header: logo + name + badge */}
                    <div className="flex items-start gap-3 mb-3">
                        {party.logo_url ? (
                            <div className="w-12 h-12 flex-shrink-0 flex items-center justify-center">
                                <img
                                    src={party.logo_url}
                                    alt={party.name}
                                    className="w-12 h-12 object-contain"
                                    onError={e => { e.target.parentElement.style.display = 'none'; }}
                                />
                            </div>
                        ) : (
                            <div
                                className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-base font-bold flex-shrink-0"
                                style={{ backgroundColor: accent }}
                            >
                                {(party.short_name ?? party.name ?? '?')[0]}
                            </div>
                        )}

                        <div className="min-w-0 flex-1">
                            <h3 className="font-bold text-gray-900 text-sm leading-tight group-hover:text-blue-700 transition-colors truncate mb-1">
                                {party.name}
                            </h3>
                            {party.short_name && (
                                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                                    <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: accent }} />
                                    {party.short_name}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Ideology */}
                    {party.ideology && (
                        <p className="text-xs text-gray-400 mb-3 line-clamp-2 leading-relaxed">
                            {party.ideology}
                        </p>
                    )}

                    {/* Stats row */}
                    <div className="pt-3 border-t border-gray-50 space-y-2.5">
                        {party.total_mps != null && (
                            <div className="flex items-center gap-1.5 text-xs text-gray-500">
                                <Users className="w-3.5 h-3.5 text-gray-400" />
                                <span className="font-semibold text-gray-700">{Number(party.total_mps).toLocaleString()}</span>
                                <span>MPs</span>
                            </div>
                        )}
                        {party.vote_share_percentage != null && (
                            <div>
                                <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                                    <BarChart2 className="w-3.5 h-3.5 text-gray-400" />
                                    <span className="font-semibold text-gray-700">{party.vote_share_percentage}%</span>
                                    <span>vote share</span>
                                </div>
                                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{ width: `${voteShare}%`, backgroundColor: accent }}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </button>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PartyInfoPage = () => {
    const [parties, setParties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selected, setSelected] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchParties = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get('/parties');
                const list = Array.isArray(data) ? data : data.parties ?? [];
                setParties(list);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load parties.');
            } finally {
                setLoading(false);
            }
        };
        fetchParties();
    }, []);

    const handleDropdownChange = (e) => {
        const id = e.target.value;
        setSelected(id);
        if (id) navigate(`/party-information/${id}`);
    };

    const handleCardClick = (id) => {
        navigate(`/party-information/${id}`);
    };

    return (
        <div className="space-y-6">
            {/* Page header + dropdown */}
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Party Information</h1>
                    <p className="text-sm text-gray-400 mt-1">Explore major political parties</p>
                </div>

                {/* Quick-navigate dropdown */}
                {parties.length > 0 && (
                    <div className="relative min-w-[220px]">
                        <select
                            value={selected}
                            onChange={handleDropdownChange}
                            className="w-full appearance-none pl-3 pr-9 py-2.5 rounded-lg border border-gray-200 bg-white text-sm font-medium text-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 hover:border-blue-400 transition-all"
                        >
                            <option value="">Jump to party...</option>
                            {parties.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                            <ChevronDown className="w-4 h-4" />
                        </div>
                    </div>
                )}
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-blue-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Loading parties...</span>
                </div>
            )}

            {/* Error */}
            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {/* Empty */}
            {!loading && !error && parties.length === 0 && (
                <div className="text-center py-20">
                    <Users className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                    <p className="text-sm text-gray-400">No parties found.</p>
                </div>
            )}

            {/* Grid */}
            {!loading && !error && parties.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {parties.map(p => (
                        <PartyCard
                            key={p.id}
                            party={p}
                            onClick={() => handleCardClick(p.id)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default PartyInfoPage;
