import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Plus, Pencil, Trash2, Upload, Users,
    Loader2, AlertCircle, X, CheckCircle2, ImageIcon, ChevronDown, ChevronUp
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

// ─── Input helper ─────────────────────────────────────────────────────────────

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
        className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
);

// ─── Create / Edit Modal ──────────────────────────────────────────────────────

const EMPTY = {
    name: '', short_name: '', ideology: '', founded_year: '',
    color_hex: '#3b82f6', website: '', total_mps: '', vote_share_percentage: '',
};

const PartyModal = ({ party, onClose, onSaved }) => {
    const isEdit = !!party?.id;
    const [form, setForm] = useState(() => party?.id ? {
        name: party.name ?? '',
        short_name: party.short_name ?? '',
        ideology: party.ideology ?? '',
        founded_year: party.founded_year ?? '',
        color_hex: party.color_hex ?? '#3b82f6',
        website: party.website ?? '',
        total_mps: party.total_mps ?? '',
        vote_share_percentage: party.vote_share_percentage ?? '',
    } : { ...EMPTY });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

    const submit = async (e) => {
        e.preventDefault();
        setSaving(true); setError('');
        try {
            const payload = {
                ...form,
                founded_year: form.founded_year ? Number(form.founded_year) : null,
                total_mps: form.total_mps !== '' ? Number(form.total_mps) : null,
                vote_share_percentage: form.vote_share_percentage !== '' ? Number(form.vote_share_percentage) : null,
            };
            if (isEdit) await api.put(`/admin/parties/${party.id}`, payload);
            else await api.post('/admin/parties', payload);
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
                    <h2 className="font-bold text-gray-900">{isEdit ? 'Edit Party' : 'Create Party'}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                </div>
                <form onSubmit={submit} className="p-6 space-y-4">
                    {error && (
                        <div className="flex gap-2 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg px-3 py-2">
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {error}
                        </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Party Name" required>
                            <Input value={form.name} onChange={e => set('name', e.target.value)} required />
                        </Field>
                        <Field label="Short Name">
                            <Input value={form.short_name} onChange={e => set('short_name', e.target.value)} placeholder="BJP" />
                        </Field>
                    </div>
                    <Field label="Ideology">
                        <Input value={form.ideology} onChange={e => set('ideology', e.target.value)} placeholder="Right-wing, Nationalist..." />
                    </Field>
                    <div className="grid grid-cols-3 gap-4">
                        <Field label="Founded Year">
                            <Input type="number" value={form.founded_year} onChange={e => set('founded_year', e.target.value)} placeholder="1984" min="1800" max="2100" />
                        </Field>
                        <Field label="Total MPs">
                            <Input type="number" value={form.total_mps} onChange={e => set('total_mps', e.target.value)} min="0" />
                        </Field>
                        <Field label="Vote Share %">
                            <Input type="number" value={form.vote_share_percentage} onChange={e => set('vote_share_percentage', e.target.value)} step="0.01" min="0" max="100" />
                        </Field>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <Field label="Website">
                            <Input type="url" value={form.website} onChange={e => set('website', e.target.value)} placeholder="https://party.org" />
                        </Field>
                        <Field label="Color">
                            <div className="flex gap-2">
                                <Input type="color" value={form.color_hex} onChange={e => set('color_hex', e.target.value)}
                                    className="w-12 h-9 p-1 cursor-pointer border border-gray-200 rounded-lg" />
                                <Input value={form.color_hex} onChange={e => set('color_hex', e.target.value)} placeholder="#3b82f6" />
                            </div>
                        </Field>
                    </div>
                    <div className="flex justify-end gap-3 pt-2">
                        <button type="button" onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                            Cancel
                        </button>
                        <button type="submit" disabled={saving}
                            className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60">
                            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                            {isEdit ? 'Save Changes' : 'Create Party'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// ─── Delete Confirm ───────────────────────────────────────────────────────────

const DeleteConfirm = ({ party, onClose, onDeleted }) => {
    const [loading, setLoading] = useState(false);
    const confirm = async () => {
        setLoading(true);
        try { await api.delete(`/admin/parties/${party.id}`); onDeleted(); }
        catch { onClose(); }
    };
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm">
                <h3 className="font-bold text-gray-900 mb-2">Delete Party?</h3>
                <p className="text-sm text-gray-500 mb-5">
                    <span className="font-medium text-gray-800">"{party.name}"</span> will be permanently deleted.
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

// ─── Upload Button ────────────────────────────────────────────────────────────

const UploadBtn = ({ partyId, field, label, icon: Icon, onDone }) => {
    const ref = useRef();
    const [uploading, setUploading] = useState(false);

    const handle = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploading(true);
        const fd = new FormData();
        fd.append(field, file);   // 'logo' or 'eci_chart'
        try {
            await api.post(`/parties/${partyId}/assets`, fd, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            onDone(true);
        } catch { onDone(false); }
        finally { setUploading(false); e.target.value = ''; }
    };

    return (
        <>
            <input ref={ref} type="file" accept="image/*" className="hidden" onChange={handle} />
            <button onClick={() => ref.current?.click()} disabled={uploading}
                title={label}
                className="p-1.5 rounded-lg text-gray-400 hover:text-violet-600 hover:bg-violet-50 transition-all disabled:opacity-50">
                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
            </button>
        </>
    );
};

// ─── Manage Leaders Modal ─────────────────────────────────────────────────────

const LeadersModal = ({ party, onClose }) => {
    const [leaders, setLeaders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newLeader, setNewLeader] = useState({ name: '', position: '', twitter: '' });
    const [saving, setSaving] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await api.get(`/admin/parties/${party.id}/leaders`);
            setLeaders(Array.isArray(data) ? data : data.leaders ?? []);
        } catch { setLeaders([]); }
        finally { setLoading(false); }
    }, [party.id]);

    useEffect(() => { load(); }, [load]);

    const addLeader = async (e) => {
        e.preventDefault();
        setSaving(true);
        try {
            await api.post(`/admin/parties/${party.id}/leaders`, newLeader);
            setNewLeader({ name: '', position: '', twitter: '' });
            load();
        } catch { /* swallow */ }
        finally { setSaving(false); }
    };

    const removeLeader = async (leaderId) => {
        try { await api.delete(`/admin/parties/${party.id}/leaders/${leaderId}`); load(); }
        catch { /* swallow */ }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-y-auto">
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <h2 className="font-bold text-gray-900">Leaders — {party.name}</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                </div>
                <div className="p-6 space-y-5">
                    {/* Current leaders */}
                    {loading ? (
                        <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-blue-500" /></div>
                    ) : leaders.length === 0 ? (
                        <p className="text-sm text-gray-400 text-center py-4">No leaders yet.</p>
                    ) : (
                        <div className="space-y-2">
                            {leaders.map((l, i) => (
                                <div key={l.id ?? i} className="flex items-center gap-3 bg-gray-50 rounded-xl px-3 py-2">
                                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                                        {(l.name ?? '?')[0].toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900 truncate">{l.name}</p>
                                        <p className="text-xs text-gray-400">{l.position}{l.twitter ? ` · @${l.twitter.replace('@', '')}` : ''}</p>
                                    </div>
                                    <button onClick={() => removeLeader(l.id)}
                                        className="text-gray-300 hover:text-red-400 transition-colors flex-shrink-0">
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Add leader form */}
                    <div className="border-t border-gray-100 pt-4">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Add Leader</p>
                        <form onSubmit={addLeader} className="space-y-3">
                            <Input placeholder="Full Name *" value={newLeader.name}
                                onChange={e => setNewLeader(f => ({ ...f, name: e.target.value }))} required />
                            <div className="grid grid-cols-2 gap-3">
                                <Input placeholder="Position" value={newLeader.position}
                                    onChange={e => setNewLeader(f => ({ ...f, position: e.target.value }))} />
                                <Input placeholder="@twitter" value={newLeader.twitter}
                                    onChange={e => setNewLeader(f => ({ ...f, twitter: e.target.value }))} />
                            </div>
                            <button type="submit" disabled={saving || !newLeader.name.trim()}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60">
                                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                                <Plus className="w-3.5 h-3.5" /> Add
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

const PartyManagement = () => {
    const [parties, setParties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [modal, setModal] = useState(null);       // null | 'create' | party (edit)
    const [delTarget, setDelTarget] = useState(null);
    const [leadersTarget, setLeadersTarget] = useState(null);
    const [toast, setToast] = useState(null);

    const showToast = (msg, ok = true) => { setToast({ msg, ok }); setTimeout(() => setToast(null), 3500); };

    const load = useCallback(async () => {
        setLoading(true); setError('');
        try {
            const { data } = await api.get('/parties');
            setParties(Array.isArray(data) ? data : data.parties ?? []);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || 'Failed to load parties.');
        } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Party Management</h1>
                    <p className="text-sm text-gray-400 mt-1">{parties.length} part{parties.length !== 1 ? 'ies' : 'y'} registered</p>
                </div>
                <button onClick={() => setModal('create')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm shadow-blue-200">
                    <Plus className="w-4 h-4" /> Add Party
                </button>
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

            {/* Table */}
            {!loading && !error && (
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-100 bg-gray-50">
                                    <th className="text-left px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Party</th>
                                    <th className="text-left px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Short</th>
                                    <th className="text-right px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">MPs</th>
                                    <th className="text-right px-4 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Vote Share</th>
                                    <th className="text-right px-5 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {parties.length === 0 && (
                                    <tr><td colSpan={5} className="text-center py-12 text-sm text-gray-400">No parties found.</td></tr>
                                )}
                                {parties.map(party => (
                                    <tr key={party.id} className="hover:bg-gray-50 transition-colors">
                                        {/* Logo + Name */}
                                        <td className="px-5 py-3">
                                            <div className="flex items-center gap-3">
                                                {party.logo_url ? (
                                                    <img src={party.logo_url} alt={party.name}
                                                        className="w-8 h-8 object-contain flex-shrink-0"
                                                        onError={e => { e.target.style.display = 'none'; }} />
                                                ) : (
                                                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                                                        style={{ backgroundColor: party.color_hex ?? '#94a3b8' }}>
                                                        {(party.short_name ?? party.name ?? '?')[0]}
                                                    </div>
                                                )}
                                                <div>
                                                    <p className="font-medium text-gray-900 truncate max-w-[180px]">{party.name}</p>
                                                    {party.ideology && <p className="text-xs text-gray-400 truncate max-w-[180px]">{party.ideology}</p>}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            {party.short_name && (
                                                <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                                                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: party.color_hex ?? '#94a3b8' }} />
                                                    {party.short_name}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right font-semibold text-gray-700">
                                            {party.total_mps != null ? Number(party.total_mps).toLocaleString() : '—'}
                                        </td>
                                        <td className="px-4 py-3 text-right text-gray-600">
                                            {party.vote_share_percentage != null ? `${party.vote_share_percentage}%` : '—'}
                                        </td>
                                        {/* Actions */}
                                        <td className="px-5 py-3">
                                            <div className="flex items-center justify-end gap-1">
                                                {/* Edit */}
                                                <button onClick={() => setModal(party)} title="Edit"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-all">
                                                    <Pencil className="w-4 h-4" />
                                                </button>
                                                {/* Upload Logo */}
                                                <UploadBtn partyId={party.id} field="logo" label="Upload Logo"
                                                    icon={ImageIcon}
                                                    onDone={ok => { showToast(ok ? 'Logo uploaded!' : 'Logo upload failed.', ok); load(); }} />
                                                {/* Upload ECI Chart */}
                                                <UploadBtn partyId={party.id} field="eci_chart" label="Upload ECI Chart"
                                                    icon={Upload}
                                                    onDone={ok => { showToast(ok ? 'ECI chart uploaded!' : 'Upload failed.', ok); load(); }} />
                                                {/* Manage Leaders */}
                                                <button onClick={() => setLeadersTarget(party)} title="Manage Leaders"
                                                    className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all">
                                                    <Users className="w-4 h-4" />
                                                </button>
                                                {/* Delete */}
                                                <button onClick={() => setDelTarget(party)} title="Delete"
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
                <PartyModal
                    party={modal === 'create' ? null : modal}
                    onClose={() => setModal(null)}
                    onSaved={() => { setModal(null); showToast(modal === 'create' ? 'Party created!' : 'Party updated!'); load(); }}
                />
            )}
            {delTarget && (
                <DeleteConfirm
                    party={delTarget}
                    onClose={() => setDelTarget(null)}
                    onDeleted={() => { setDelTarget(null); showToast('Party deleted.'); load(); }}
                />
            )}
            {leadersTarget && (
                <LeadersModal party={leadersTarget} onClose={() => setLeadersTarget(null)} />
            )}

            {/* Toast */}
            {toast && <Toast msg={toast.msg} ok={toast.ok} onClose={() => setToast(null)} />}
        </div>
    );
};

export default PartyManagement;
