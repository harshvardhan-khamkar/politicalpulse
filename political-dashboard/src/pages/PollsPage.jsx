import React, { useState, useEffect } from 'react';
import {
    ChevronDown, ChevronUp, Lock, CheckCircle2,
    Loader2, AlertCircle, Activity, BarChart2
} from 'lucide-react';

// NOTE: API returns options with fields: { id, text } and optionally vote_count per option.
// Poll-level vote_count is the total.
import api from '../api/api';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const isExpired = (poll) => {
    if (poll.is_active === 0 || poll.is_active === false) return true;
    if (poll.ends_at) return new Date() > new Date(poll.ends_at);
    return false;
};

// Sum vote_count per option if available, otherwise 0
const totalVotes = (options = []) =>
    options.reduce((s, o) => s + Number(o.vote_count ?? 0), 0);

// Get display text — API returns either `text` or `option_text`
const optionText = (o) => o.option_text ?? o.text ?? '';

const isLoggedIn = () => !!localStorage.getItem('access_token');

// ─── ResultBar — uses /polls/{id}/results shape: { text, votes, percentage } ──

const ResultsBar = ({ result, isLeader }) => {
    const pct = Number(result.percentage ?? 0);
    const votes = Number(result.votes ?? 0);
    return (
        <div className={`rounded-xl p-4 border transition-all ${isLeader
            ? 'bg-blue-50 border-blue-200 shadow-sm shadow-blue-100'
            : 'bg-gray-50 border-gray-100'}`}
        >
            <div className="flex justify-between items-center mb-2">
                <span className={`text-sm font-medium ${isLeader ? 'text-blue-700' : 'text-gray-700'}`}>
                    {result.text}
                    {isLeader && (
                        <span className="ml-2 text-[10px] font-bold bg-blue-500 text-white px-1.5 py-0.5 rounded-full">LEADING</span>
                    )}
                </span>
                <span className="text-xs text-gray-500 font-mono">{votes.toLocaleString()} votes</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-700 ${isLeader ? 'bg-blue-500' : 'bg-gray-400'}`}
                    style={{ width: `${pct.toFixed(1)}%` }}
                />
            </div>
            <div className="text-right text-xs text-gray-400 mt-1">{pct.toFixed(1)}%</div>
        </div>
    );
};

// ─── EVM vote option ──────────────────────────────────────────────────────────

const VoteOption = ({ option, selected, disabled, onVote }) => {
    const isChosen = selected === option.id || selected === String(option.id);
    return (
        <div className={`flex items-center justify-between gap-4 px-4 py-3 rounded-xl border transition-all
            ${isChosen
                ? 'bg-blue-50 border-blue-300'
                : disabled
                    ? 'bg-gray-50 border-gray-100 opacity-50'
                    : 'bg-white border-gray-100 hover:border-blue-200 hover:bg-blue-50/30'
            }`}
        >
            <span className={`text-sm font-medium ${isChosen ? 'text-blue-700' : 'text-gray-700'}`}>
                {optionText(option)}
            </span>
            <button
                onClick={() => !disabled && onVote(option.id)}
                disabled={disabled}
                className={`flex-shrink-0 w-9 h-9 rounded-full border-2 flex items-center justify-center transition-all duration-200
                    ${isChosen
                        ? 'border-blue-500 bg-blue-500 shadow-lg shadow-blue-300'
                        : disabled
                            ? 'border-gray-200 bg-gray-100 cursor-not-allowed'
                            : 'border-gray-300 bg-white hover:border-blue-400 hover:shadow-md hover:shadow-blue-200 cursor-pointer'
                    }`}
            >
                {isChosen && <CheckCircle2 className="w-5 h-5 text-white" />}
            </button>
        </div>
    );
};

// ─── EVM Panel per poll ───────────────────────────────────────────────────────

const EVMPanel = ({ poll: initialPoll }) => {
    const closed = isExpired(initialPoll);
    const [selected, setSelected] = useState(null);
    const [voted, setVoted] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [voteError, setVoteError] = useState('');
    const loggedIn = isLoggedIn();
    const options = initialPoll.options ?? [];

    // ── Closed poll: just point to Poll Results page ──
    if (closed) {
        return (
            <div className="flex items-center gap-3 py-4 px-4 rounded-xl bg-gray-50 border border-dashed border-gray-200">
                <BarChart2 className="w-5 h-5 text-gray-300 flex-shrink-0" />
                <p className="text-sm text-gray-400">
                    This poll has ended.{' '}
                    <a href="/poll-results" className="text-blue-600 hover:underline font-medium">
                        View detailed results →
                    </a>
                </p>
            </div>
        );
    }

    const handleVote = async (optionId) => {
        if (!loggedIn || voted) return;
        setSelected(optionId);
        setSubmitting(true);
        setVoteError('');
        try {
            await api.post(`/polls/${initialPoll.id}/vote`, { option_id: optionId });
            setVoted(true);
        } catch (e) {
            const status = e.response?.status;
            if (status === 401) setVoteError('Please login to vote.');
            else if (status === 400) { setVoteError('You have already voted on this poll.'); setVoted(true); }
            else setVoteError('Could not record vote. Please try again.');
            setSelected(null);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="relative">
            {!loggedIn && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-white/60 backdrop-blur-sm border border-gray-100">
                    <Lock className="w-7 h-7 text-gray-400 mb-2" />
                    <p className="text-sm font-semibold text-gray-600">Login required to participate.</p>
                    <a href="/login" className="mt-2 text-xs text-blue-600 hover:underline font-medium">Sign in →</a>
                </div>
            )}

            <div className={`space-y-2 max-h-80 overflow-y-auto pr-1 ${!loggedIn ? 'blur-sm pointer-events-none select-none' : ''}`}>
                {options.map(opt => (
                    <VoteOption
                        key={opt.id}
                        option={opt}
                        selected={selected}
                        disabled={submitting || voted || !!selected}
                        onVote={handleVote}
                    />
                ))}
            </div>

            {voted && (
                <div className="mt-3 flex items-center gap-2 text-green-600 text-xs font-semibold">
                    <CheckCircle2 className="w-4 h-4" /> Vote Recorded
                </div>
            )}
            {submitting && (
                <div className="mt-3 flex items-center gap-2 text-blue-500 text-xs">
                    <Loader2 className="w-4 h-4 animate-spin" /> Submitting...
                </div>
            )}
            {voteError && (
                <div className="mt-3 flex items-center gap-2 text-red-500 text-xs">
                    <AlertCircle className="w-4 h-4" /> {voteError}
                </div>
            )}
        </div>
    );
};


// ─── Accordion item ───────────────────────────────────────────────────────────

const PollAccordion = ({ poll, isOpen, onToggle }) => {
    const closed = isExpired(poll);
    const isSimulation = poll.poll_type === 'simulation';

    return (
        <div className={`rounded-2xl border transition-all duration-200 overflow-hidden
            ${isOpen ? 'border-blue-200 shadow-md shadow-blue-50' : 'border-gray-100 hover:border-gray-200'}`}
        >
            <button onClick={onToggle} className="w-full flex items-center justify-between px-5 py-4 bg-white text-left group">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className={`flex-shrink-0 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full
                        ${isSimulation ? 'bg-purple-100 text-purple-600' : 'bg-blue-50 text-blue-500'}`}>
                        {isSimulation ? '⚡ Simulation' : poll.poll_type ?? 'Poll'}
                    </span>
                    <span className="font-semibold text-gray-900 text-sm truncate group-hover:text-blue-700 transition-colors">
                        {poll.title}
                    </span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                    {closed ? (
                        <span className="text-[10px] font-bold uppercase bg-red-50 border border-red-100 text-red-500 px-2 py-0.5 rounded-full">Results Out!</span>
                    ) : (
                        <span className="flex items-center gap-1 text-[10px] font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                            <Activity className="w-3 h-3" /> Active
                        </span>
                    )}
                    <span className="text-gray-400">
                        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </span>
                </div>
            </button>

            <div className={`transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
                <div className="px-5 pb-5 pt-1 bg-gray-50/50 border-t border-gray-100">
                    {poll.description && (
                        <p className="text-sm text-gray-500 mb-4 leading-relaxed">{poll.description}</p>
                    )}
                    <EVMPanel poll={poll} />
                </div>
            </div>
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PollsPage = () => {
    const [polls, setPolls] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [openId, setOpenId] = useState(null);

    useEffect(() => {
        const fetchPolls = async () => {
            setLoading(true);
            setError('');
            try {
                const { data } = await api.get('/polls');
                const list = Array.isArray(data) ? data : data.polls ?? [];
                const sorted = [
                    ...list.filter(p => p.poll_type === 'simulation'),
                    ...list.filter(p => p.poll_type !== 'simulation'),
                ];
                setPolls(sorted);
                if (sorted.length > 0) setOpenId(sorted[0].id);
            } catch (e) {
                setError(e.response?.data?.detail || e.message || 'Failed to load polls.');
            } finally {
                setLoading(false);
            }
        };
        fetchPolls();
    }, []);

    const simPolls = polls.filter(p => p.poll_type === 'simulation');
    const otherPolls = polls.filter(p => p.poll_type !== 'simulation');
    const toggle = (id) => setOpenId(prev => prev === id ? null : id);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Polls</h1>
                    <p className="text-sm text-gray-400 mt-1">Cast your vote or view results.</p>
                </div>
                {!isLoggedIn() && (
                    <a href="/login" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
                        <Lock className="w-4 h-4" /> Login to Vote
                    </a>
                )}
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
                    <p className="text-sm text-gray-400">No polls available right now.</p>
                </div>
            )}

            {!loading && simPolls.length > 0 && (
                <section>
                    <h2 className="text-xs font-bold uppercase tracking-widest text-purple-500 mb-3">⚡ Simulation Polls</h2>
                    <div className="space-y-3">
                        {simPolls.map(poll => (
                            <PollAccordion key={poll.id} poll={poll} isOpen={openId === poll.id} onToggle={() => toggle(poll.id)} />
                        ))}
                    </div>
                </section>
            )}

            {!loading && otherPolls.length > 0 && (
                <section>
                    <h2 className="text-xs font-bold uppercase tracking-widest text-blue-500 mb-3">General &amp; Opinion Polls</h2>
                    <div className="space-y-3">
                        {otherPolls.map(poll => (
                            <PollAccordion key={poll.id} poll={poll} isOpen={openId === poll.id} onToggle={() => toggle(poll.id)} />
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
};

export default PollsPage;
