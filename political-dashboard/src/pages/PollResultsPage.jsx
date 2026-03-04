import React, { useState, useEffect } from 'react';
import {
    ChevronLeft, Loader2, AlertCircle, BarChart2,
    Radio, CheckCircle2, Calendar, Users, Clock
} from 'lucide-react';
import api from '../api/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const isExpired = (poll) => {
    if (poll.is_active === 0 || poll.is_active === false) return true;
    if (poll.ends_at) return new Date() > new Date(poll.ends_at);
    return false;
};

const fmtDate = (str) => {
    if (!str) return '—';
    return new Date(str).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};

// ─── Animated result bar ──────────────────────────────────────────────────────
// Uses /polls/{id}/results shape: { option_id, text, votes, percentage }

const ResultBar = ({ result, isLeader, animate }) => {
    const pct = Number(result.percentage ?? 0);
    const votes = Number(result.votes ?? 0);
    const [width, setWidth] = useState(0);

    useEffect(() => {
        const t = setTimeout(() => setWidth(animate ? pct : 0), 80);
        return () => clearTimeout(t);
    }, [animate, pct]);

    useEffect(() => {
        if (animate) setWidth(pct);
    }, [pct]);

    return (
        <div className={`rounded-xl p-4 border transition-all duration-200
            ${isLeader ? 'border-blue-300 bg-blue-50 shadow-md shadow-blue-100' : 'border-gray-100 bg-white'}`}
        >
            <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                    <span className={`text-sm font-semibold ${isLeader ? 'text-blue-700' : 'text-gray-700'}`}>
                        {result.text}
                    </span>
                    {isLeader && (
                        <span className="text-[10px] font-bold uppercase tracking-wide bg-blue-500 text-white px-2 py-0.5 rounded-full">
                            Leading
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="font-mono font-semibold text-gray-700">{pct.toFixed(1)}%</span>
                    <span>{votes.toLocaleString()} votes</span>
                </div>
            </div>
            <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${isLeader ? 'bg-blue-500' : 'bg-gray-300'}`}
                    style={{ width: `${width}%` }}
                />
            </div>
        </div>
    );
};

// ─── Detailed results view ────────────────────────────────────────────────────

const PollDetail = ({ poll: initialPoll, onBack }) => {
    // Fetches from /polls/{id}/results: { poll_id, title, total_votes, results[] }
    const [resultsData, setResultsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [animate, setAnimate] = useState(false);
    const closed = isExpired(initialPoll);

    const fetchResults = async () => {
        try {
            const { data } = await api.get(`/polls/${initialPoll.id}/results`);
            setResultsData(data);
        } catch (_) { }
    };

    // Initial load
    useEffect(() => {
        const load = async () => {
            setLoading(true);
            await fetchResults();
            setLoading(false);
            setTimeout(() => setAnimate(true), 50);
        };
        load();
    }, [initialPoll.id]);

    // Auto-refresh every 15s for active polls
    useEffect(() => {
        if (closed) return;
        const interval = setInterval(fetchResults, 15000);
        return () => clearInterval(interval);
    }, [closed, initialPoll.id]);

    const results = resultsData?.results ?? [];
    const totalVotesCount = Number(resultsData?.total_votes ?? 0);
    const leadingId = results.length > 0 && totalVotesCount > 0
        ? results.reduce((a, b) => Number(a.votes ?? 0) >= Number(b.votes ?? 0) ? a : b).option_id
        : null;

    return (
        <div className="space-y-5">
            <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors font-medium">
                <ChevronLeft className="w-4 h-4" /> Back to Polls
            </button>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* Status banner */}
                {!closed && (
                    <div className="flex items-center gap-2 bg-green-500 text-white text-xs font-semibold px-5 py-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
                        </span>
                        Live Counting... Results update every 15 seconds
                    </div>
                )}
                {closed && (
                    <div className="flex items-center gap-2 bg-red-50 border-b border-red-100 text-red-600 text-xs font-semibold px-5 py-2">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Results Out! — Voting is closed
                    </div>
                )}

                <div className="p-6">
                    <div className="flex items-start justify-between gap-4 flex-wrap mb-4">
                        <div>
                            <h2 className="text-xl font-bold text-gray-900">{initialPoll.title}</h2>
                            {initialPoll.description && (
                                <p className="text-sm text-gray-500 mt-1 max-w-2xl">{initialPoll.description}</p>
                            )}
                        </div>
                        <div className="flex flex-col items-end gap-1">
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                            ) : (
                                <>
                                    <div className="text-3xl font-bold text-blue-600">{totalVotesCount.toLocaleString()}</div>
                                    <div className="text-xs text-gray-400 uppercase tracking-wider">Total Votes</div>
                                </>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-4 mb-6 text-xs text-gray-400 flex-wrap">
                        {initialPoll.created_at && (
                            <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Created {fmtDate(initialPoll.created_at)}</span>
                        )}
                        {initialPoll.ends_at && (
                            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {closed ? 'Ended' : 'Ends'} {fmtDate(initialPoll.ends_at)}</span>
                        )}
                    </div>

                    {loading ? (
                        <div className="flex items-center gap-2 py-8 justify-center text-blue-500 text-sm">
                            <Loader2 className="w-5 h-5 animate-spin" /> Loading results...
                        </div>
                    ) : results.length === 0 ? (
                        <p className="text-sm text-gray-400 text-center py-8">No results available yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {results
                                .slice()
                                .sort((a, b) => Number(b.votes ?? 0) - Number(a.votes ?? 0))
                                .map(r => (
                                    <ResultBar
                                        key={r.option_id}
                                        result={r}
                                        isLeader={r.option_id === leadingId && totalVotesCount > 0}
                                        animate={animate}
                                    />
                                ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// ─── Poll card ────────────────────────────────────────────────────────────────

const PollCard = ({ poll, onSelect }) => {
    const closed = isExpired(poll);
    const total = Number(poll.vote_count ?? 0);
    const isSimulation = poll.poll_type === 'simulation';

    return (
        <button onClick={() => onSelect(poll)}
            className="w-full text-left bg-white rounded-2xl border border-gray-100 p-5 hover:border-blue-200 hover:shadow-md hover:shadow-blue-50 transition-all duration-200 group"
        >
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full
                            ${isSimulation ? 'bg-purple-100 text-purple-600' : 'bg-blue-50 text-blue-500'}`}>
                            {isSimulation ? '⚡ Simulation' : poll.poll_type ?? 'Poll'}
                        </span>
                        {closed ? (
                            <span className="text-[10px] font-bold uppercase bg-red-50 border border-red-100 text-red-500 px-2 py-0.5 rounded-full">Results Out!</span>
                        ) : (
                            <span className="flex items-center gap-1 text-[10px] font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                                <Radio className="w-2.5 h-2.5" /> Live Counting
                            </span>
                        )}
                    </div>
                    <h3 className="font-semibold text-gray-900 text-sm group-hover:text-blue-700 transition-colors truncate">{poll.title}</h3>
                    {poll.description && (
                        <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{poll.description}</p>
                    )}
                </div>
                <ChevronLeft className="w-4 h-4 text-gray-300 group-hover:text-blue-400 rotate-180 flex-shrink-0 mt-1 transition-colors" />
            </div>

            <div className="flex items-center gap-4 mt-3 text-xs text-gray-400 flex-wrap">
                <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {total.toLocaleString()} votes</span>
                {poll.created_at && <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {fmtDate(poll.created_at)}</span>}
                {poll.ends_at && <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {closed ? 'Ended' : 'Ends'} {fmtDate(poll.ends_at)}</span>}
            </div>
        </button>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PollResultsPage = () => {
    const [polls, setPolls] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selected, setSelected] = useState(null);

    useEffect(() => {
        const fetchPolls = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get('/polls');
                const list = Array.isArray(data) ? data : data.polls ?? [];
                setPolls([
                    ...list.filter(p => p.poll_type === 'simulation'),
                    ...list.filter(p => p.poll_type !== 'simulation'),
                ]);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load polls.');
            } finally {
                setLoading(false);
            }
        };
        fetchPolls();
    }, []);

    if (selected) {
        return <PollDetail poll={selected} onBack={() => setSelected(null)} />;
    }

    const simPolls = polls.filter(p => p.poll_type === 'simulation');
    const otherPolls = polls.filter(p => p.poll_type !== 'simulation');

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Poll Results</h1>
                <p className="text-sm text-gray-400 mt-1">Select a poll to view detailed results.</p>
            </div>

            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-blue-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Loading polls...</span>
                </div>
            )}

            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {!loading && !error && polls.length === 0 && (
                <div className="text-center py-20">
                    <BarChart2 className="w-10 h-10 text-gray-200 mx-auto mb-3" />
                    <p className="text-sm text-gray-400">No poll results available.</p>
                </div>
            )}

            {!loading && simPolls.length > 0 && (
                <section>
                    <h2 className="text-xs font-bold uppercase tracking-widest text-purple-500 mb-3">⚡ Simulation Polls</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {simPolls.map(p => <PollCard key={p.id} poll={p} onSelect={setSelected} />)}
                    </div>
                </section>
            )}

            {!loading && otherPolls.length > 0 && (
                <section>
                    <h2 className="text-xs font-bold uppercase tracking-widest text-blue-500 mb-3">General &amp; Opinion Polls</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {otherPolls.map(p => <PollCard key={p.id} poll={p} onSelect={setSelected} />)}
                    </div>
                </section>
            )}
        </div>
    );
};

export default PollResultsPage;
