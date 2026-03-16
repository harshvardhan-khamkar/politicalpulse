import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Plus, Pencil, Trash2, Loader2, AlertCircle, X, CheckCircle2, ImageIcon
} from 'lucide-react';
import api from '../../api/api';

// ─── Toast ────────────────────────────────────────────────────────────────────

const Toast = ({ msg, ok, onClose }) => (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium
        ${ok ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
        {ok ? <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
        {msg}
        <button onClick={onClose} className="ml-2 opacity-60 hover:opacity-100"><X className="w-3.5 h-3.5" /></button>
    </div>
);

// ─── Input helpers ────────────────────────────────────────────────────────────

const Field = ({ label, required, children }) => (
    <div>
        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1 block">
            {label}{required && ' *'}
        </label>
        {children}
    </div>
);

const Input = (props) => (
    <input {...props}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
);

const TextArea = (props) => (
    <textarea {...props}
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y" />
);

// ─── Create / Edit Modal ──────────────────────────────────────────────────────

const EMPTY = {
    name: '', position: '', twitter_handle: '', bio: '',
    state: '', constituency: '', election_history: '', party_id: '', display_order: 0,
};

const LeaderModal = ({ leader, parties, onClose, onSaved }) => {
    const isEdit = !!leader?.id;
    const [form, setForm] = useState(() => isEdit ? {
        name: leader.name ?? '',
        position: leader.position ?? '',
        twitter_handle: leader.twitter_handle ?? '',
        bio: leader.bio ?? '',
        state: leader.state ?? '',
        constituency: leader.constituency ?? '',
        election_history: leader.election_history ?? '',
        party_id: leader.party_id ?? '',
        display_order: leader.display_order ?? 0,
    } : { ...EMPTY });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

    const submit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        try {
            const payload = {
                ...form,
                party_id: Number(form.party_id),
                display_order: Number(form.display_order) || 0,
            };
            if (isEdit) await api.put(`/leaders/${leader.id}`, payload);
            else await api.post('/leaders', payload);
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
                    <h2 className="font-bold text-gray-900">{isEdit ? 'Edit Leader' : 'Add Leader'}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                </div>
                <form onSubmit={submit} className="p-6 space-y-4">
                    {error && (
                        <div className="flex gap-2 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg px-3 py-2">
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {error}
                        </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Full Name" required>
                            <Input value={form.name} onChange={e => set('name', e.target.value)} required />
                        </Field>
                        <Field label="Party" required>
                            <select value={form.party_id} onChange={e => set('party_id', e.target.value)} required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                                <option value="">Select party</option>
                                {(parties ?? []).map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </Field>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Position">
                            <Input value={form.position} onChange={e => set('position', e.target.value)} placeholder="President" />
                        </Field>
                        <Field label="Twitter Handle">
                            <Input value={form.twitter_handle} onChange={e => set('twitter_handle', e.target.value)} placeholder="@handle" />
                        </Field>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="State">
                            <Input value={form.state} onChange={e => set('state', e.target.value)} placeholder="Maharashtra" />
                        </Field>
                        <Field label="Constituency">
                            <Input value={form.constituency} onChange={e => set('constituency', e.target.value)} placeholder="Varanasi" />
                        </Field>
                    </div>
                    <Field label="Bio / Summary">
                        <TextArea rows={3} value={form.bio} onChange={e => set('bio', e.target.value)} placeholder="Short summary of the leader..." />
                    </Field>
                    <Field label="Election History">
                        <TextArea rows={3} value={form.election_history} onChange={e => set('election_history', e.target.value)} placeholder="Key election records..." />
                    </Field>
                    <div className="flex justify-end gap-3 pt-2">
                        <button type="button" onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                            Cancel
                        </button>
                        <button type="submit" disabled={saving}
                            className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60">
                            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                            {isEdit ? 'Save Changes' : 'Add Leader'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// ─── Delete Confirm ───────────────────────────────────────────────────────────

const DeleteConfirm = ({ leader, onClose, onDeleted }) => {
    const [loading, setLoading] = useState(false);
    const confirm = async () => {
        setLoading(true);
        try { await api.delete(`/leaders/${leader.id}`); onDeleted(); }
        catch { onClose(); }
    };
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm">
                <h3 className="font-bold text-gray-900 mb-2">Delete Leader?</h3>
                <p className="text-sm text-gray-500 mb-5">
                    <span className="font-medium text-gray-800">"{leader.name}"</span> will be permanently deleted.
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

// ─── Photo Upload Button ──────────────────────────────────────────────────────

const PhotoUploadBtn = ({ leaderId, onDone }) => {
    const ref = useRef();
    const [uploading, setUploading] = useState(false);
    const handle = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploading(true);
        const fd = new FormData();
        fd.append('photo', file);
        try {
            await api.post(`/leaders/${leaderId}/photo`, fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            onDone(true);
        } catch { onDone(false); }
        finally { setUploading(false); e.target.value = ''; }
    };
    return (
        <>
            <input ref={ref} type="file" accept="image/*" className="hidden" onChange={handle} />
            <button onClick={() => ref.current?.click()} disabled={uploading} title="Upload Photo"
                className="p-1.5 rounded-lg text-gray-400 hover:text-violet-600 hover:bg-violet-50 transition-all disabled:opacity-50">
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImageIcon className="w-4 h-4" />}
            </button>
        </>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const LeaderManagement = () => {
    const [leaders, setLeaders] = useState([]);
    const [parties, setParties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modal, setModal] = useState(null);
    const [delTarget, setDelTarget] = useState(null);
    const [toast, setToast] = useState(null);

    const showToast = (msg, ok = true) => { setToast({ msg, ok }); setTimeout(() => setToast(null), 3500); };

    const load = useCallback(async () => {
        setLoading(true); setError('');
        try {
            const [lr, pr] = await Promise.all([api.get('/leaders'), api.get('/parties')]);
            setLeaders(Array.isArray(lr.data) ? lr.data : []);
            setParties(Array.isArray(pr.data) ? pr.data : pr.data.parties ?? []);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || 'Failed to load.');
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Leader Management</h1>
                    <p className="text-sm text-gray-400 mt-1">{leaders.length} leader{leaders.length !== 1 ? 's' : ''} registered</p>
                </div>
                <button onClick={() => setModal('create')}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm shadow-indigo-200">
                    <Plus className="w-4 h-4" /> Add Leader
                </button>
            </div>

            {/* Loading */}
            {loading && (
                <div className="flex items-center justify-center py-20 gap-3 text-indigo-600">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="text-sm font-medium">Loading leaders...</span>
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
                                    <th className="text-left px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Leader</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Party</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Position</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">State</th>
                                    <th className="text-right px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {leaders.length === 0 && (
                                    <tr><td colSpan={5} className="text-center py-12 text-sm text-gray-400">No leaders found.</td></tr>
                                )}
                                {leaders.map(l => (
                                    <tr key={l.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-5 py-3">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                                                    style={{ backgroundColor: l.party_color_hex ?? '#6366f1' }}>
                                                    {(l.name ?? '?')[0]}
                                                </div>
                                                <p className="font-medium text-gray-900 truncate max-w-[160px]">{l.name}</p>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            {l.party_short_name && (
                                                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                                                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: l.party_color_hex ?? '#94a3b8' }} />
                                                    {l.party_short_name}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-gray-600">{l.position ?? '—'}</td>
                                        <td className="px-4 py-3 text-gray-600">{l.state ?? '—'}</td>
                                        <td className="px-5 py-3">
                                            <div className="flex items-center justify-end gap-1">
                                                <button onClick={() => setModal(l)} title="Edit"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all">
                                                    <Pencil className="w-4 h-4" />
                                                </button>
                                                <PhotoUploadBtn leaderId={l.id}
                                                    onDone={ok => { showToast(ok ? 'Photo uploaded!' : 'Upload failed.', ok); load(); }} />
                                                <button onClick={() => setDelTarget(l)} title="Delete"
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
                <LeaderModal
                    leader={modal === 'create' ? null : modal}
                    parties={parties}
                    onClose={() => setModal(null)}
                    onSaved={() => { setModal(null); showToast(modal === 'create' ? 'Leader added!' : 'Leader updated!'); load(); }}
                />
            )}
            {delTarget && (
                <DeleteConfirm
                    leader={delTarget}
                    onClose={() => setDelTarget(null)}
                    onDeleted={() => { setDelTarget(null); showToast('Leader deleted.'); load(); }}
                />
            )}

            {/* Toast */}
            {toast && <Toast msg={toast.msg} ok={toast.ok} onClose={() => setToast(null)} />}
        </div>
    );
};

export default LeaderManagement;
