'use client';

import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, User } from 'lucide-react';

interface UserData {
    id: string;
    profile: {
        full_name: string;
        email: string;
        phone: string;
        date_of_birth?: string;
        gender?: string;
        guardian_name?: string;
        guardian_phone?: string;
    };
    academic: {
        current_class?: string;
        school_name?: string;
        board?: string;
    };
    address: {
        city?: string;
        state?: string;
        pincode?: string;
    };
}

const defaultForm = {
    full_name: '', email: '', phone: '', date_of_birth: '', gender: '',
    guardian_name: '', guardian_phone: '', current_class: '', school_name: '',
    board: '', city: '', state: '', pincode: ''
};

export default function UsersPage() {
    const [users, setUsers] = useState<UserData[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingUser, setEditingUser] = useState<UserData | null>(null);
    const [form, setForm] = useState(defaultForm);

    useEffect(() => { fetchUsers(); }, []);

    const fetchUsers = async () => {
        try {
            const res = await fetch('/api/users');
            if (res.ok) setUsers(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const body = {
            profile: {
                full_name: form.full_name, email: form.email, phone: form.phone,
                date_of_birth: form.date_of_birth || null, gender: form.gender || null,
                guardian_name: form.guardian_name || null, guardian_phone: form.guardian_phone || null
            },
            academic: {
                current_class: form.current_class || null, school_name: form.school_name || null,
                board: form.board || null
            },
            address: {
                city: form.city || null, state: form.state || null, pincode: form.pincode || null
            }
        };

        try {
            const url = editingUser ? `/api/users/${editingUser.id}` : '/api/users';
            const method = editingUser ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
            });
            if (res.ok) {
                setShowForm(false);
                setEditingUser(null);
                setForm(defaultForm);
                fetchUsers();
            }
        } catch (e) { console.error(e); }
    };

    const handleEdit = (user: UserData) => {
        setEditingUser(user);
        setForm({
            full_name: user.profile.full_name, email: user.profile.email, phone: user.profile.phone,
            date_of_birth: user.profile.date_of_birth || '', gender: user.profile.gender || '',
            guardian_name: user.profile.guardian_name || '', guardian_phone: user.profile.guardian_phone || '',
            current_class: user.academic.current_class || '', school_name: user.academic.school_name || '',
            board: user.academic.board || '', city: user.address.city || '',
            state: user.address.state || '', pincode: user.address.pincode || ''
        });
        setShowForm(true);
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this user?')) return;
        await fetch(`/api/users/${id}`, { method: 'DELETE' });
        fetchUsers();
    };

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Users</h1>
                    <p className="text-dark-400">Manage user profiles for form filling</p>
                </div>
                <button onClick={() => { setEditingUser(null); setForm(defaultForm); setShowForm(true); }} className="btn btn-primary">
                    <Plus className="w-4 h-4" /> Add User
                </button>
            </div>

            {showForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
                    <div className="bg-dark-800 rounded-xl p-6 w-full max-w-2xl animate-fade-in my-8">
                        <h2 className="text-xl font-semibold mb-4">{editingUser ? 'Edit User' : 'Add New User'}</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <Input label="Full Name *" value={form.full_name} onChange={v => setForm({ ...form, full_name: v })} required />
                                <Input label="Email *" type="email" value={form.email} onChange={v => setForm({ ...form, email: v })} required />
                                <Input label="Phone *" value={form.phone} onChange={v => setForm({ ...form, phone: v })} required />
                                <Input label="Date of Birth" value={form.date_of_birth} onChange={v => setForm({ ...form, date_of_birth: v })} placeholder="DD/MM/YYYY" />
                                <Input label="Gender" value={form.gender} onChange={v => setForm({ ...form, gender: v })} />
                                <Input label="Guardian Name" value={form.guardian_name} onChange={v => setForm({ ...form, guardian_name: v })} />
                                <Input label="Guardian Phone" value={form.guardian_phone} onChange={v => setForm({ ...form, guardian_phone: v })} />
                                <Input label="Current Class" value={form.current_class} onChange={v => setForm({ ...form, current_class: v })} />
                                <Input label="School Name" value={form.school_name} onChange={v => setForm({ ...form, school_name: v })} />
                                <Input label="Board" value={form.board} onChange={v => setForm({ ...form, board: v })} />
                                <Input label="City" value={form.city} onChange={v => setForm({ ...form, city: v })} />
                                <Input label="State" value={form.state} onChange={v => setForm({ ...form, state: v })} />
                                <Input label="Pincode" value={form.pincode} onChange={v => setForm({ ...form, pincode: v })} />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="submit" className="btn btn-primary flex-1">{editingUser ? 'Save' : 'Create'}</button>
                                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {loading ? (
                <div className="text-center py-12 text-dark-400">Loading...</div>
            ) : users.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-dark-400 mb-4">No users yet</p>
                    <button onClick={() => setShowForm(true)} className="btn btn-primary"><Plus className="w-4 h-4" /> Add First User</button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {users.map(user => (
                        <div key={user.id} className="card">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
                                        <User className="w-5 h-5 text-primary-500" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-white">{user.profile.full_name}</h3>
                                        <p className="text-dark-400 text-sm">{user.profile.phone}</p>
                                        <p className="text-dark-500 text-xs">{user.profile.email}</p>
                                    </div>
                                </div>
                                <div className="flex gap-1">
                                    <button onClick={() => handleEdit(user)} className="p-2 text-dark-400 hover:text-white"><Pencil className="w-4 h-4" /></button>
                                    <button onClick={() => handleDelete(user.id)} className="p-2 text-dark-400 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                            {user.academic.current_class && (
                                <div className="mt-3 pt-3 border-t border-dark-700 text-sm text-dark-400">
                                    Class: {user.academic.current_class} {user.academic.school_name && `• ${user.academic.school_name}`}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function Input({ label, value, onChange, type = 'text', required = false, placeholder = '' }: {
    label: string; value: string; onChange: (v: string) => void; type?: string; required?: boolean; placeholder?: string;
}) {
    return (
        <div>
            <label className="block text-sm text-dark-400 mb-1">{label}</label>
            <input type={type} value={value} onChange={e => onChange(e.target.value)} className="input" required={required} placeholder={placeholder} />
        </div>
    );
}
