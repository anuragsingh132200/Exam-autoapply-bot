'use client';

import { useState, useEffect } from 'react';
import { Plus, Play, Pause, Trash2, Users, Clock, CheckCircle, XCircle } from 'lucide-react';

interface Exam { id: string; name: string; }
interface User { id: string; profile: { full_name: string; phone: string; }; }
interface BatchJob {
    id: string;
    status: string;
    total: number;
    completed: number;
    successful: number;
    failed: number;
    created_at: string;
}

export default function BatchPage() {
    const [exams, setExams] = useState<Exam[]>([]);
    const [users, setUsers] = useState<User[]>([]);
    const [batches, setBatches] = useState<BatchJob[]>([]);
    const [loading, setLoading] = useState(true);

    const [showForm, setShowForm] = useState(false);
    const [selectedExam, setSelectedExam] = useState('');
    const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
    const [delay, setDelay] = useState(30);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [examsRes, usersRes, batchesRes] = await Promise.all([
                fetch('/api/exams'),
                fetch('/api/users'),
                fetch('/api/batch')
            ]);
            if (examsRes.ok) setExams(await examsRes.json());
            if (usersRes.ok) setUsers(await usersRes.json());
            if (batchesRes.ok) setBatches(await batchesRes.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleCreate = async () => {
        if (!selectedExam || selectedUsers.length === 0) return;

        try {
            const res = await fetch('/api/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exam_id: selectedExam,
                    user_ids: selectedUsers,
                    delay_between_runs_seconds: delay
                })
            });

            if (res.ok) {
                setShowForm(false);
                setSelectedExam('');
                setSelectedUsers([]);
                fetchData();
            }
        } catch (e) { console.error(e); }
    };

    const handleCancel = async (batchId: string) => {
        await fetch(`/api/batch/${batchId}/cancel`, { method: 'POST' });
        fetchData();
    };

    const toggleUser = (userId: string) => {
        setSelectedUsers(prev =>
            prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
        );
    };

    const selectAll = () => setSelectedUsers(users.map(u => u.id));
    const deselectAll = () => setSelectedUsers([]);

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Batch Processing</h1>
                    <p className="text-dark-400">Run workflows for multiple users at once</p>
                </div>
                <button onClick={() => setShowForm(true)} className="btn btn-primary">
                    <Plus className="w-4 h-4" /> New Batch
                </button>
            </div>

            {/* Create Modal */}
            {showForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-800 rounded-xl p-6 w-full max-w-xl animate-fade-in">
                        <h2 className="text-xl font-semibold mb-4">Create Batch Job</h2>

                        <div className="mb-4">
                            <label className="block text-sm text-dark-400 mb-1">Exam</label>
                            <select
                                value={selectedExam}
                                onChange={(e) => setSelectedExam(e.target.value)}
                                className="input"
                            >
                                <option value="">Select exam...</option>
                                {exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                            </select>
                        </div>

                        <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                                <label className="text-sm text-dark-400">Users ({selectedUsers.length} selected)</label>
                                <div className="flex gap-2">
                                    <button onClick={selectAll} className="text-xs text-primary-500">Select All</button>
                                    <button onClick={deselectAll} className="text-xs text-dark-500">Clear</button>
                                </div>
                            </div>
                            <div className="max-h-48 overflow-y-auto bg-dark-900 rounded-lg p-2 space-y-1">
                                {users.map(user => (
                                    <label
                                        key={user.id}
                                        className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${selectedUsers.includes(user.id) ? 'bg-primary-500/20' : 'hover:bg-dark-800'
                                            }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedUsers.includes(user.id)}
                                            onChange={() => toggleUser(user.id)}
                                            className="rounded"
                                        />
                                        <span className="text-sm">{user.profile.full_name}</span>
                                        <span className="text-xs text-dark-500">{user.profile.phone}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="mb-4">
                            <label className="block text-sm text-dark-400 mb-1">Delay between runs (seconds)</label>
                            <input
                                type="number"
                                value={delay}
                                onChange={(e) => setDelay(parseInt(e.target.value) || 30)}
                                min={10}
                                className="input w-32"
                            />
                        </div>

                        <div className="flex gap-3">
                            <button onClick={handleCreate} className="btn btn-primary flex-1">
                                <Play className="w-4 h-4" /> Start Batch
                            </button>
                            <button onClick={() => setShowForm(false)} className="btn btn-secondary">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Batches List */}
            {loading ? (
                <div className="text-center py-12 text-dark-400">Loading...</div>
            ) : batches.length === 0 ? (
                <div className="card text-center py-12">
                    <Users className="w-12 h-12 text-dark-600 mx-auto mb-4" />
                    <p className="text-dark-400 mb-4">No batch jobs yet</p>
                    <button onClick={() => setShowForm(true)} className="btn btn-primary">
                        Create First Batch
                    </button>
                </div>
            ) : (
                <div className="space-y-4">
                    {batches.map((batch) => (
                        <div key={batch.id} className="card">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <BatchStatusIcon status={batch.status} />
                                    <div>
                                        <p className="font-semibold">Batch {batch.id.slice(0, 8)}</p>
                                        <p className="text-sm text-dark-500">
                                            Created {new Date(batch.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`badge ${batch.status === 'completed' ? 'badge-success' :
                                            batch.status === 'running' ? 'badge-info' :
                                                batch.status === 'failed' ? 'badge-error' : 'badge-warning'
                                        }`}>{batch.status}</span>
                                    {batch.status === 'running' && (
                                        <button onClick={() => handleCancel(batch.id)} className="btn btn-secondary text-sm py-1">
                                            <Pause className="w-3 h-3" /> Cancel
                                        </button>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-4 gap-4 mb-4 text-center">
                                <div>
                                    <div className="text-2xl font-bold text-white">{batch.total}</div>
                                    <div className="text-xs text-dark-500">Total</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-primary-400">{batch.completed}</div>
                                    <div className="text-xs text-dark-500">Completed</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-green-400">{batch.successful}</div>
                                    <div className="text-xs text-dark-500">Successful</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-red-400">{batch.failed}</div>
                                    <div className="text-xs text-dark-500">Failed</div>
                                </div>
                            </div>

                            <div className="progress-bar">
                                <div
                                    className="progress-bar-fill"
                                    style={{ width: `${(batch.completed / batch.total) * 100}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function BatchStatusIcon({ status }: { status: string }) {
    switch (status) {
        case 'running':
            return <Clock className="w-8 h-8 text-primary-500 animate-pulse" />;
        case 'completed':
            return <CheckCircle className="w-8 h-8 text-green-500" />;
        case 'failed':
            return <XCircle className="w-8 h-8 text-red-500" />;
        default:
            return <Clock className="w-8 h-8 text-amber-500" />;
    }
}
