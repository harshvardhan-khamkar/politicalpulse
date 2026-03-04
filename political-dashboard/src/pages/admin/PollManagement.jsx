import React, { useState, useEffect, useCallback } from 'react';
import {
    Plus, Pencil, Trash2, XCircle, BarChart2,
    Loader2, AlertCircle, X, CheckCircle2
} from 'lucide-react';
import api from '../../api/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtDate = (str) => str ? new Date(str).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
const isExpired = (poll) => !poll.is_active || (poll.ends_at && new Date(poll.ends_at) < new Date());

const EMPTY_FORM = {
    title: '',
    description: '',
    poll_type: 'opinion',
    ends_at: '',
    options: [{ text: '' }, { text: '' }],
};

// ─── Toast ────────────────────────────────────────────────────────────────────

const Toast = ({ msg, ok, onClose }) => (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium
        ${ok ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
        {ok ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
        {msg}
        <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100"><X className="w-3.5 h-3.5" /></button>
    </div>
);

// ─── Modal ────────────────────────────────────────────────────────────────────

const PollModal = ({ poll, onClose, onSaved }) => {
    const isEdit = !!poll?.id;
    const [form, setForm] = useState(() => poll?.id ? {
        title: poll.title ?? '',
        description: poll.description ?? '',
        poll_type: poll.poll_type ?? 'opinion',
        ends_at: poll.ends_at ? poll.ends_at.slice(0, 16) : '',
        options: Array.isArray(poll.options) && poll.options.length
            ? poll.options.map(o => ({ text: o.text ?? o.option_text ?? '' }))
            : [{ text: '' }, { text: '' }],
    } : { ...EMPTY_FORM, options: [{ text: '' }, { text: '' }] });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const setField = (k, v) => setForm(f => ({ ...f, [k]: v }));
    const setOption = (i, v) => setForm(f => {
        const opts = [...f.options];
        opts[i] = { text: v };
        return { ...f, options: opts };
    });
    const addOption = () => setForm(f => ({ ...f, options: [...f.options, { text: '' }] }));
    const removeOption = (i) => setForm(f => ({ ...f, options: f.options.filter((_, idx) => idx !== i) }));

    const submit = async (e) => {
        e.preventDefault();
        if (form.options.some(o => !o.text.trim())) { setError('All options must have text.'); return; }
        setSaving(true); setError('');
        try {
            const payload = { ...form, options: form.options.map((o, i) => ({ id: String(i + 1), text: o.text.trim() })) };
            if (isEdit) await api.put(`/polls/${poll.id}`, payload);
            else await api.post('/polls', payload);
            onSaved();
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Save failed.';
            setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        } finally { setSaving(false); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <h2 className="font-bold text-gray-900">{isEdit ? 'Edit Poll' : 'Create Poll'}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors"><X className="w-5 h-5" /></button>
                </div>

                <form onSubmit={submit} className="p-6 space-y-4">
                    {error && (
                        <div className="flex gap-2 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg px-3 py-2">
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {error}
                        </div>
                    )}

                    <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Title *</label>
                        <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={form.title} onChange={e => setField('title', e.target.value)} required />
                    </div>

                    <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Description</label>
                        <textarea rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                            value={form.description} onChange={e => setField('description', e.target.value)} />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Type *</label>
                            <select className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={form.poll_type} onChange={e => setField('poll_type', e.target.value)}>
                                <option value="opinion">Opinion</option>
                                <option value="simulation">Simulation</option>
                                <option value="general">General</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">Ends At</label>
                            <input type="datetime-local" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={form.ends_at} onChange={e => setField('ends_at', e.target.value)} />
                        </div>
                    </div>

                    {/* Options */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Options *</label>
                            <button type="button" onClick={addOption}
                                className="text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                <Plus className="w-3 h-3" /> Add option
                            </button>
                        </div>
                        <div className="space-y-2">
                            {form.options.map((opt, i) => (
                                <div key={i} className="flex gap-2">
                                    <input
                                        className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder={`Option ${i + 1}`}
                                        value={opt.text}
                                        onChange={e => setOption(i, e.target.value)}
                                        required
                                    />
                                    {form.options.length > 2 && (
                                        <button type="button" onClick={() => removeOption(i)}
                                            className="text-gray-300 hover:text-red-400 transition-colors">
                                            <X className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <button type="button" onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                            Cancel
                        </button>
                        <button type="submit" disabled={saving}
                            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60">
                            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                            {isEdit ? 'Save Changes' : 'Create Poll'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// ─── Delete Confirm ───────────────────────────────────────────────────────────

const DeleteConfirm = ({ poll, onClose, onDeleted }) => {
    const [loading, setLoading] = useState(false);
    const confirm = async () => {
        setLoading(true);
        try { await api.delete(`/polls/${poll.id}`); onDeleted(); }
        catch (e) { onClose(); }
    };
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm">
                <h3 className="font-bold text-gray-900 mb-2">Delete Poll?</h3>
                <p className="text-sm text-gray-500 mb-5">
                    <span className="font-medium text-gray-800">"{poll.title}"</span> will be permanently deleted.
                </p>
                <div className="flex justify-end gap-3">
                    <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900">Cancel</button>
                    <button onClick={confirm} disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60">
                        {loading && <Loader2 className="w-4 h-4 animate-spin" />} Delete
                    </button>
                </div>
            </div>
        </div>
    );
};

// ─── Status Badge ─────────────────────────────────────────────────────────────

const StatusBadge = ({ poll }) => {
    const closed = isExpired(poll);
    return (
        <span className={`inline-flex items-center text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full
            ${closed ? 'bg-gray-100 text-gray-500' : 'bg-green-100 text-green-700'}`}>
            {closed ? 'Closed' : 'Active'}
        </span>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PollManagement = () => {
    const [polls, setPolls] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modal, setModal] = useState(null);     // null | 'create' | poll-object (edit)
    const [delTarget, setDelTarget] = useState(null);
    const [toast, setToast] = useState(null);

    const showToast = (msg, ok = true) => {
        setToast({ msg, ok });
        setTimeout(() => setToast(null), 3500);
    };

    const load = useCallback(async () => {
        setLoading(true); setError('');
        try {
            const { data } = await api.get('/polls');
            setPolls(Array.isArray(data) ? data : data.polls ?? []);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || 'Failed to load polls.');
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const forceClose = async (poll) => {
        try {
            await api.put(`/polls/${poll.id}`, { ...poll, is_active: 0 });
            showToast('Poll closed successfully.');
            load();
        } catch (e) {
            showToast(e.response?.data?.detail || 'Force close failed.', false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Poll Management</h1>
                    <p className="text-sm text-gray-400 mt-1">{polls.length} poll{polls.length !== 1 ? 's' : ''} total</p>
                </div>
                <button onClick={() => setModal('create')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm shadow-blue-200">
                    <Plus className="w-4 h-4" /> Create Poll
                </button>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-blue-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Loading polls...</span>
                </div>
            )}

            {/* Error */}
            {!loading && error && (
                <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {/* Table */}
            {!loading && !error && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-100 bg-gray-50">
                                    <th className="text-left px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Title</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Type</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Ends At</th>
                                    <th className="text-right px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Votes</th>
                                    <th className="text-right px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {polls.length === 0 && (
                                    <tr><td colSpan={6} className="text-center py-12 text-sm text-gray-400">No polls found.</td></tr>
                                )}
                                {polls.map(poll => (
                                    <tr key={poll.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-5 py-3.5">
                                            <p className="font-medium text-gray-900 truncate max-w-[200px]">{poll.title}</p>
                                            {poll.description && <p className="text-xs text-gray-400 truncate max-w-[200px]">{poll.description}</p>}
                                        </td>
                                        <td className="px-4 py-3.5">
                                            <span className="text-xs font-medium capitalize text-gray-600 bg-gray-100 px-2 py-0.5 rounded-full">
                                                {poll.poll_type ?? '—'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3.5"><StatusBadge poll={poll} /></td>
                                        <td className="px-4 py-3.5 text-xs text-gray-500">{fmtDate(poll.ends_at)}</td>
                                        <td className="px-4 py-3.5 text-right font-semibold text-gray-700">
                                            {Number(poll.vote_count ?? 0).toLocaleString()}
                                        </td>
                                        <td className="px-5 py-3.5">
                                            <div className="flex items-center justify-end gap-1">
                                                {/* Edit */}
                                                <button onClick={() => setModal(poll)} title="Edit"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-all">
                                                    <Pencil className="w-4 h-4" />
                                                </button>
                                                {/* View Results */}
                                                <a href={`/poll-results`} title="View Results"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all">
                                                    <BarChart2 className="w-4 h-4" />
                                                </a>
                                                {/* Force Close */}
                                                {!isExpired(poll) && (
                                                    <button onClick={() => forceClose(poll)} title="Force Close"
                                                        className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-all">
                                                        <XCircle className="w-4 h-4" />
                                                    </button>
                                                )}
                                                {/* Delete */}
                                                <button onClick={() => setDelTarget(poll)} title="Delete"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-all">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Modals */}
            {modal && (
                <PollModal
                    poll={modal === 'create' ? null : modal}
                    onClose={() => setModal(null)}
                    onSaved={() => { setModal(null); showToast(modal === 'create' ? 'Poll created!' : 'Poll updated!'); load(); }}
                />
            )}
            {delTarget && (
                <DeleteConfirm
                    poll={delTarget}
                    onClose={() => setDelTarget(null)}
                    onDeleted={() => { setDelTarget(null); showToast('Poll deleted.'); load(); }}
                />
            )}

            {/* Toast */}
            {toast && <Toast msg={toast.msg} ok={toast.ok} onClose={() => setToast(null)} />}
        </div>
    );
};

export default PollManagement;
