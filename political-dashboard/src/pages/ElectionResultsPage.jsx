import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, Loader2, Trophy, User, AlertCircle, MapPin, Users, TrendingUp, BarChart2, Medal } from 'lucide-react';
import api from '../api/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const normalize = (val) => val?.toString().replace(/_/g, ' ').trim() ?? '';

const dedupWithRaw = (arr) => {
    const seen = new Set();
    const result = [];
    for (const item of arr) {
        const key = normalize(String(item)).toLowerCase();
        if (!seen.has(key)) {
            seen.add(key);
            result.push({ raw: String(item), display: normalize(String(item)) });
        }
    }
    return result.sort((a, b) => a.display.localeCompare(b.display));
};

// ─── Party Colors ─────────────────────────────────────────────────────────────
// Each entry: { from, to, bar, shadow }
const PARTY_COLORS = {
    BJP: { from: 'from-orange-500', to: 'to-orange-600', bar: 'bg-orange-300', shadow: 'shadow-orange-200' },
    INC: { from: 'from-blue-600', to: 'to-blue-700', bar: 'bg-blue-300', shadow: 'shadow-blue-200' },
    AAP: { from: 'from-sky-500', to: 'to-cyan-500', bar: 'bg-sky-300', shadow: 'shadow-sky-200' },
    BSP: { from: 'from-indigo-500', to: 'to-indigo-700', bar: 'bg-indigo-300', shadow: 'shadow-indigo-200' },
    SP: { from: 'from-red-500', to: 'to-red-600', bar: 'bg-red-300', shadow: 'shadow-red-200' },
    NCP: { from: 'from-blue-700', to: 'to-indigo-600', bar: 'bg-blue-300', shadow: 'shadow-blue-200' },
    TMC: { from: 'from-teal-500', to: 'to-green-500', bar: 'bg-teal-300', shadow: 'shadow-teal-200' },
    CPI: { from: 'from-red-600', to: 'to-red-800', bar: 'bg-red-300', shadow: 'shadow-red-200' },
    SHS: { from: 'from-amber-600', to: 'to-orange-700', bar: 'bg-amber-300', shadow: 'shadow-amber-200' },
    JDU: { from: 'from-green-600', to: 'to-emerald-600', bar: 'bg-green-300', shadow: 'shadow-green-200' },
    IND: { from: 'from-purple-500', to: 'to-violet-600', bar: 'bg-purple-300', shadow: 'shadow-purple-200' },
    NOTA: { from: 'from-gray-400', to: 'to-gray-500', bar: 'bg-gray-300', shadow: 'shadow-gray-200' },
    DEFAULT: { from: 'from-slate-500', to: 'to-slate-600', bar: 'bg-slate-300', shadow: 'shadow-slate-200' },
};

const getPartyColor = (party) => PARTY_COLORS[party?.toUpperCase()] ?? PARTY_COLORS.DEFAULT;

// ─── Dropdown ─────────────────────────────────────────────────────────────────

const SelectDropdown = ({ label, value, options, onChange, disabled, loading, placeholder }) => (
    <div className="flex flex-col gap-1.5 flex-1 min-w-[180px]">
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</label>
        <div className="relative">
            <select
                value={value}
                onChange={e => onChange(e.target.value)}
                disabled={disabled || loading}
                className={`w-full appearance-none pl-3 pr-9 py-2.5 rounded-lg border text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-blue-500
                    ${disabled || loading
                        ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
                        : 'bg-white border-gray-200 text-gray-800 cursor-pointer hover:border-blue-400'
                    }`}
            >
                <option value="">{loading ? 'Loading...' : placeholder}</option>
                {options.map(opt => (
                    <option key={opt.raw} value={opt.raw}>{opt.display}</option>
                ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronDown className="w-4 h-4" />}
            </div>
        </div>
    </div>
);

// ─── Animated Vote Bar ────────────────────────────────────────────────────────

const VoteBar = ({ pct, color = 'bg-blue-500', animate }) => {
    const [width, setWidth] = useState(0);
    useEffect(() => {
        const t = setTimeout(() => setWidth(animate ? Math.min(Number(pct) || 0, 100) : 0), 120);
        return () => clearTimeout(t);
    }, [animate, pct]);

    return (
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
                style={{ width: `${width}%` }}
            />
        </div>
    );
};

// ─── Summary Stats ────────────────────────────────────────────────────────────

const StatPill = ({ icon: Icon, label, value }) => (
    <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 px-4 py-3 shadow-sm flex-1 min-w-[130px]">
        <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
            <Icon className="w-4 h-4 text-blue-600" />
        </div>
        <div>
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
            <p className="text-sm font-bold text-gray-900 leading-tight">{value}</p>
        </div>
    </div>
);

// ─── Winner Card ──────────────────────────────────────────────────────────────

const WinnerCard = ({ candidate, animate }) => {
    const pc = getPartyColor(candidate.party);
    return (
        <div className={`relative bg-gradient-to-br ${pc.from} ${pc.to} rounded-2xl p-6 text-white shadow-lg ${pc.shadow} overflow-hidden`}>
            {/* Background decoration */}
            <div className="absolute -top-6 -right-6 w-28 h-28 rounded-full bg-white opacity-10" />
            <div className="absolute -bottom-8 -left-4 w-24 h-24 rounded-full bg-white opacity-10" />

            <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                    <span className="flex items-center gap-1.5 bg-white/20 backdrop-blur-sm text-white text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wide">
                        <Trophy className="w-3 h-3" /> Winner
                    </span>
                    <span className="text-white/60 text-[10px] font-semibold bg-white/10 px-2 py-0.5 rounded-full uppercase tracking-wider">
                        {candidate.party}
                    </span>
                </div>

                <div className="flex items-center gap-3 mb-4">
                    <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-xl font-bold flex-shrink-0">
                        {candidate.candidate_name?.charAt(0) ?? '?'}
                    </div>
                    <div>
                        <h3 className="font-bold text-lg leading-tight">{candidate.candidate_name}</h3>
                        <p className="text-white/80 text-sm font-medium">{candidate.gender ?? ''}</p>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-white/20 rounded-xl px-3 py-2">
                        <p className="text-white/70 text-[10px] uppercase tracking-wide">Votes</p>
                        <p className="font-bold text-base">{Number(candidate.votes_secured ?? 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-white/20 rounded-xl px-3 py-2">
                        <p className="text-white/70 text-[10px] uppercase tracking-wide">Vote Share</p>
                        <p className="font-bold text-base">{candidate.vote_share_percentage}%</p>
                    </div>
                </div>

                <div>
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-white/70 text-xs">Vote Share</span>
                        <span className="text-white text-xs font-semibold">{candidate.vote_share_percentage}%</span>
                    </div>
                    <VoteBar pct={candidate.vote_share_percentage} color={pc.bar} animate={animate} />
                </div>
            </div>
        </div>
    );
};

// ─── Runner-up Card (2nd / 3rd) ───────────────────────────────────────────────

const RunnerUpCard = ({ candidate, animate }) => {
    const medals = { 2: { icon: '🥈', color: 'text-slate-400', bg: 'bg-slate-100' }, 3: { icon: '🥉', color: 'text-amber-600', bg: 'bg-amber-50' } };
    const m = medals[candidate.position] ?? { icon: `#${candidate.position}`, color: 'text-gray-400', bg: 'bg-gray-50' };

    return (
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm hover:border-blue-100 hover:shadow-md transition-all">
            <div className="flex items-center justify-between mb-3">
                <span className={`text-sm ${m.color} font-bold`}>{m.icon}</span>
                <span className="text-xs text-gray-400">#{candidate.position}</span>
            </div>
            <div className="flex items-center gap-2 mb-3">
                <div className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${m.bg} ${m.color}`}>
                    {candidate.candidate_name?.charAt(0) ?? '?'}
                </div>
                <div className="min-w-0">
                    <p className="font-semibold text-gray-900 text-sm truncate">{candidate.candidate_name}</p>
                    <p className="text-xs text-gray-400">{candidate.party}</p>
                </div>
            </div>
            <div className="space-y-2">
                <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Votes</span>
                    <span className="font-semibold text-gray-800">{Number(candidate.votes_secured ?? 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-gray-400">Vote Share</span>
                    <span className="font-bold text-blue-600">{candidate.vote_share_percentage}%</span>
                </div>
                <VoteBar pct={candidate.vote_share_percentage} color="bg-blue-400" animate={animate} />
            </div>
        </div>
    );
};

// ─── Compact Candidate Row ────────────────────────────────────────────────────

const CandidateRow = ({ candidate, animate }) => (
    <div className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 px-4 py-3 hover:border-blue-100 transition-all">
        <span className="text-xs text-gray-300 font-bold w-5 text-center flex-shrink-0">#{candidate.position}</span>
        <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 flex-shrink-0">
            {candidate.candidate_name?.charAt(0) ?? '?'}
        </div>
        <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{candidate.candidate_name}</p>
            <p className="text-xs text-gray-400">{candidate.party}</p>
        </div>
        <div className="flex-1 min-w-0 hidden sm:block">
            <VoteBar pct={candidate.vote_share_percentage} color="bg-gray-300" animate={animate} />
        </div>
        <div className="text-right flex-shrink-0">
            <p className="text-xs font-bold text-gray-700">{candidate.vote_share_percentage}%</p>
            <p className="text-[10px] text-gray-400">{Number(candidate.votes_secured ?? 0).toLocaleString()}</p>
        </div>
    </div>
);

// ─── Summary Section ──────────────────────────────────────────────────────────

const SummarySection = ({ results }) => {
    const total = results.reduce((s, c) => s + Number(c.votes_secured ?? 0), 0);
    const winner = results[0];
    const runnerUp = results[1];
    const margin = winner && runnerUp
        ? Number(winner.votes_secured ?? 0) - Number(runnerUp.votes_secured ?? 0)
        : null;
    const turnout = winner?.turnout ?? null;

    return (
        <div className="flex flex-wrap gap-3 mb-6">
            <StatPill icon={Users} label="Candidates" value={results.length} />
            <StatPill icon={BarChart2} label="Total Votes" value={total.toLocaleString()} />
            {turnout !== null && <StatPill icon={TrendingUp} label="Turnout" value={`${turnout}%`} />}
            {margin !== null && <StatPill icon={Medal} label="Win Margin" value={margin.toLocaleString()} />}
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const ElectionResultsPage = () => {
    const [states, setStates] = useState([]);
    const [constituencies, setConstituencies] = useState([]);
    const [years, setYears] = useState([]);

    const [selectedState, setSelectedState] = useState('');
    const [selectedConstituency, setSelectedConstituency] = useState('');
    const [selectedYear, setSelectedYear] = useState('');

    const [loadingStates, setLoadingStates] = useState(false);
    const [loadingConstituencies, setLoadingConstituencies] = useState(false);
    const [loadingYears, setLoadingYears] = useState(false);
    const [loadingResults, setLoadingResults] = useState(false);

    const [results, setResults] = useState(null);
    const [error, setError] = useState('');
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        const fetchInit = async () => {
            setLoadingStates(true);
            setLoadingYears(true);
            try {
                const [statesRes, yearsRes] = await Promise.all([
                    api.get('/elections/states'),
                    api.get('/elections/years'),
                ]);
                const rawStates = Array.isArray(statesRes.data) ? statesRes.data : statesRes.data.states ?? [];
                setStates(dedupWithRaw(rawStates));
                const rawYears = Array.isArray(yearsRes.data) ? yearsRes.data : yearsRes.data.years ?? [];
                const uniqueYears = [...new Set(rawYears)].sort((a, b) => b - a);
                setYears(uniqueYears.map(y => ({ raw: String(y), display: String(y) })));
            } catch (e) {
                console.error('Init fetch failed', e);
            } finally {
                setLoadingStates(false);
                setLoadingYears(false);
            }
        };
        fetchInit();
    }, []);

    useEffect(() => {
        if (!selectedState) { setConstituencies([]); setSelectedConstituency(''); return; }
        const fetchConstituencies = async () => {
            setLoadingConstituencies(true);
            setSelectedConstituency('');
            try {
                const res = await api.get(`/elections/constituencies?state=${encodeURIComponent(selectedState)}`);
                const raw = Array.isArray(res.data) ? res.data : res.data.constituencies ?? [];
                setConstituencies(dedupWithRaw(raw));
            } catch (e) { console.error('Constituency fetch failed', e); }
            finally { setLoadingConstituencies(false); }
        };
        fetchConstituencies();
    }, [selectedState]);

    useEffect(() => {
        if (!selectedState || !selectedConstituency || !selectedYear) return;
        const fetchResults = async () => {
            setLoadingResults(true);
            setError('');
            setResults(null);
            setAnimate(false);
            try {
                const res = await api.get('/elections/results', {
                    params: { state: selectedState, constituency: selectedConstituency, year: selectedYear },
                });
                const list = Array.isArray(res.data) ? res.data : res.data.results ?? [];
                setResults(list.sort((a, b) => (a.position ?? 99) - (b.position ?? 99)));
                setTimeout(() => setAnimate(true), 100);
            } catch (e) {
                const msg = e.response?.data?.detail || e.message || 'Failed to fetch results.';
                setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
            } finally {
                setLoadingResults(false);
            }
        };
        fetchResults();
    }, [selectedState, selectedConstituency, selectedYear]);

    const winner = results?.[0];
    const podium = results?.slice(1, 3) ?? [];
    const rest = results?.slice(3) ?? [];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Election Results</h1>
                <p className="text-sm text-gray-400 mt-1">Search results by state, constituency and election year.</p>
            </div>

            {/* Filter bar */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-5">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                        <MapPin className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-gray-900">See your constituency result!</h2>
                        <p className="text-xs text-gray-400">Select state, constituency and year to view results.</p>
                    </div>
                </div>
                <div className="flex flex-wrap gap-4">
                    <SelectDropdown label="State" value={selectedState} options={states} onChange={setSelectedState} loading={loadingStates} placeholder="Select State" />
                    <SelectDropdown label="Constituency" value={selectedConstituency} options={constituencies} onChange={setSelectedConstituency} disabled={!selectedState} loading={loadingConstituencies} placeholder={selectedState ? 'Select Constituency' : 'Select state first'} />
                    <SelectDropdown label="Year" value={selectedYear} options={years} onChange={setSelectedYear} loading={loadingYears} placeholder="Select Year" />
                </div>
            </div>

            {/* Loading */}
            {loadingResults && (
                <div className="flex items-center justify-center py-16 gap-3 text-blue-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Fetching results...</span>
                </div>
            )}

            {/* Error */}
            {!loadingResults && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {/* Empty */}
            {!loadingResults && !error && results !== null && results.length === 0 && (
                <div className="text-center py-16">
                    <User className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                    <p className="text-sm text-gray-400">No results found for this selection.</p>
                </div>
            )}

            {/* Results */}
            {!loadingResults && !error && results && results.length > 0 && (
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex items-center justify-between flex-wrap gap-2">
                        <h3 className="font-semibold text-gray-800">
                            {results.length} candidates
                            <span className="ml-2 text-gray-400 font-normal text-sm">
                                · {normalize(selectedConstituency)}, {normalize(selectedState)} ({selectedYear})
                            </span>
                        </h3>
                    </div>

                    {/* Summary stats */}
                    <SummarySection results={results} />

                    {/* Winner */}
                    {winner && (
                        <div>
                            <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-3">🏆 Winner</p>
                            <WinnerCard candidate={winner} animate={animate} />
                        </div>
                    )}

                    {/* 2nd & 3rd */}
                    {podium.length > 0 && (
                        <div>
                            <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-3">Runners Up</p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {podium.map((c, i) => <RunnerUpCard key={c.id ?? i} candidate={c} animate={animate} />)}
                            </div>
                        </div>
                    )}

                    {/* Remaining */}
                    {rest.length > 0 && (
                        <div>
                            <p className="text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-3">All Candidates</p>
                            <div className="space-y-2">
                                {rest.map((c, i) => <CandidateRow key={c.id ?? i} candidate={c} animate={animate} />)}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ElectionResultsPage;
