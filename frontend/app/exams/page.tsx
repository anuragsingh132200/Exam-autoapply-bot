'use client';

import { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';

interface Exam {
    id: string;
    name: string;
    slug: string;
    url: string;
    is_active: boolean;
    created_at: string;
}

export default function ExamsPage() {
    const [exams, setExams] = useState<Exam[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingExam, setEditingExam] = useState<Exam | null>(null);
    const [formData, setFormData] = useState({ name: '', slug: '', url: '' });

    useEffect(() => {
        fetchExams();
    }, []);

    const fetchExams = async () => {
        try {
            const res = await fetch('/api/exams');
            if (res.ok) {
                setExams(await res.json());
            }
        } catch (error) {
            console.error('Failed to fetch exams:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const url = editingExam ? `/api/exams/${editingExam.id}` : '/api/exams';
            const method = editingExam ? 'PUT' : 'POST';

            const res = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (res.ok) {
                setShowForm(false);
                setEditingExam(null);
                setFormData({ name: '', slug: '', url: '' });
                fetchExams();
            }
        } catch (error) {
            console.error('Failed to save exam:', error);
        }
    };

    const handleEdit = (exam: Exam) => {
        setEditingExam(exam);
        setFormData({ name: exam.name, slug: exam.slug, url: exam.url });
        setShowForm(true);
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this exam?')) return;
        try {
            await fetch(`/api/exams/${id}`, { method: 'DELETE' });
            fetchExams();
        } catch (error) {
            console.error('Failed to delete exam:', error);
        }
    };

    const handleToggle = async (id: string) => {
        try {
            await fetch(`/api/exams/${id}/toggle`, { method: 'POST' });
            fetchExams();
        } catch (error) {
            console.error('Failed to toggle exam:', error);
        }
    };

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Exams</h1>
                    <p className="text-dark-400">Configure exam registrations</p>
                </div>
                <button
                    onClick={() => {
                        setEditingExam(null);
                        setFormData({ name: '', slug: '', url: '' });
                        setShowForm(true);
                    }}
                    className="btn btn-primary"
                >
                    <Plus className="w-4 h-4" />
                    Add Exam
                </button>
            </div>

            {/* Form Modal */}
            {showForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-800 rounded-xl p-6 w-full max-w-md animate-fade-in">
                        <h2 className="text-xl font-semibold mb-4">
                            {editingExam ? 'Edit Exam' : 'Add New Exam'}
                        </h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm text-dark-400 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="PW NSAT"
                                    className="input"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-dark-400 mb-1">Slug</label>
                                <input
                                    type="text"
                                    value={formData.slug}
                                    onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
                                    placeholder="pwnsat"
                                    className="input"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-dark-400 mb-1">Registration URL</label>
                                <input
                                    type="url"
                                    value={formData.url}
                                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                                    placeholder="https://example.com/register"
                                    className="input"
                                    required
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="submit" className="btn btn-primary flex-1">
                                    {editingExam ? 'Save Changes' : 'Create Exam'}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowForm(false)}
                                    className="btn btn-secondary"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Exams List */}
            {loading ? (
                <div className="text-center py-12 text-dark-400">Loading...</div>
            ) : exams.length === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-dark-400 mb-4">No exams configured</p>
                    <button onClick={() => setShowForm(true)} className="btn btn-primary">
                        <Plus className="w-4 h-4" />
                        Add Your First Exam
                    </button>
                </div>
            ) : (
                <div className="space-y-4">
                    {exams.map((exam) => (
                        <div key={exam.id} className="card flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <button onClick={() => handleToggle(exam.id)} className="text-dark-400 hover:text-white">
                                    {exam.is_active ? (
                                        <ToggleRight className="w-8 h-8 text-green-500" />
                                    ) : (
                                        <ToggleLeft className="w-8 h-8" />
                                    )}
                                </button>
                                <div>
                                    <h3 className="font-semibold text-white">{exam.name}</h3>
                                    <p className="text-dark-500 text-sm truncate max-w-md">{exam.url}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className={`badge ${exam.is_active ? 'badge-success' : 'badge-error'}`}>
                                    {exam.is_active ? 'Active' : 'Inactive'}
                                </span>
                                <button onClick={() => handleEdit(exam)} className="p-2 text-dark-400 hover:text-white">
                                    <Pencil className="w-4 h-4" />
                                </button>
                                <button onClick={() => handleDelete(exam.id)} className="p-2 text-dark-400 hover:text-red-500">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
