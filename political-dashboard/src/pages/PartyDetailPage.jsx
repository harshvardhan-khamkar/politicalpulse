import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ChevronLeft, Loader2, AlertCircle, ExternalLink,
    Users, MapPin, BarChart2, Award
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

            {/* ── Wordcloud ── */}
            <section>
                <SectionHeading title="Wordcloud" />
                {party.wordcloud_image_url ? (
                    <div className="rounded-2xl overflow-hidden border border-gray-100">
                        <img
                            src={`${API_BASE}${party.wordcloud_image_url}`}
                            alt={`${party.name} wordcloud`}
                            className="w-full rounded-lg border object-contain max-h-80"
                            onError={e => { e.target.parentElement.style.display = 'none'; }}
                        />
                    </div>
                ) : (
                    <p className="text-sm text-gray-400 italic">No discourse data available.</p>
                )}
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
