'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, AlertCircle, CheckCircle, XCircle, Clock, Activity } from 'lucide-react';

interface GlobalStats {
    total_workflows: number;
    successful_workflows: number;
    failed_workflows: number;
    active_sessions: number;
    success_rate: number;
    avg_duration_seconds: number;
}

interface RecentSession {
    id: string;
    exam_id: string;
    user_id: string;
    status: string;
    progress: number;
    created_at: string;
    completed_at: string | null;
    result_message: string | null;
}

export default function AnalyticsPage() {
    const [stats, setStats] = useState<GlobalStats | null>(null);
    const [sessions, setSessions] = useState<RecentSession[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [statsRes, sessionsRes] = await Promise.all([
                fetch('/api/analytics/global'),
                fetch('/api/analytics/recent-sessions?limit=20')
            ]);

            if (statsRes.ok) setStats(await statsRes.json());
            if (sessionsRes.ok) setSessions(await sessionsRes.json());
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const styles: Record<string, string> = {
            completed: 'badge-success',
            failed: 'badge-error',
            running: 'badge-info',
            waiting_input: 'badge-warning',
            pending: 'badge-info'
        };
        return styles[status] || 'badge-info';
    };

    const formatDuration = (seconds: number) => {
        if (seconds < 60) return `${Math.round(seconds)}s`;
        return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-dark-400">Loading analytics...</div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Analytics</h1>
                <p className="text-dark-400">Workflow performance and statistics</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatCard
                    icon={<Activity className="w-5 h-5" />}
                    label="Total Workflows"
                    value={stats?.total_workflows.toString() || '0'}
                    color="primary"
                />
                <StatCard
                    icon={<CheckCircle className="w-5 h-5" />}
                    label="Successful"
                    value={stats?.successful_workflows.toString() || '0'}
                    subtext={`${((stats?.success_rate || 0) * 100).toFixed(1)}% rate`}
                    color="success"
                />
                <StatCard
                    icon={<XCircle className="w-5 h-5" />}
                    label="Failed"
                    value={stats?.failed_workflows.toString() || '0'}
                    color="error"
                />
                <StatCard
                    icon={<Clock className="w-5 h-5" />}
                    label="Avg Duration"
                    value={formatDuration(stats?.avg_duration_seconds || 0)}
                    subtext={`${stats?.active_sessions || 0} active`}
                    color="warning"
                />
            </div>

            {/* Success Rate Bar */}
            <div className="card mb-8">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-semibold">Success Rate</h2>
                    <span className="text-2xl font-bold text-green-500">
                        {((stats?.success_rate || 0) * 100).toFixed(1)}%
                    </span>
                </div>
                <div className="h-4 bg-dark-700 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
                        style={{ width: `${(stats?.success_rate || 0) * 100}%` }}
                    />
                </div>
                <div className="flex justify-between text-sm text-dark-400 mt-2">
                    <span>{stats?.successful_workflows || 0} succeeded</span>
                    <span>{stats?.failed_workflows || 0} failed</span>
                </div>
            </div>

            {/* Recent Sessions */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">Recent Sessions</h2>
                    <button onClick={fetchData} className="text-primary-500 hover:text-primary-400 text-sm">
                        Refresh
                    </button>
                </div>

                {sessions.length === 0 ? (
                    <div className="text-center py-8 text-dark-400">No sessions yet</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-dark-700">
                                    <th className="pb-3 text-dark-400 font-medium text-sm">Status</th>
                                    <th className="pb-3 text-dark-400 font-medium text-sm">Session ID</th>
                                    <th className="pb-3 text-dark-400 font-medium text-sm">Progress</th>
                                    <th className="pb-3 text-dark-400 font-medium text-sm">Started</th>
                                    <th className="pb-3 text-dark-400 font-medium text-sm">Result</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sessions.map((session) => (
                                    <tr key={session.id} className="border-b border-dark-800 hover:bg-dark-800/50">
                                        <td className="py-3">
                                            <span className={`badge ${getStatusBadge(session.status)}`}>
                                                {session.status}
                                            </span>
                                        </td>
                                        <td className="py-3 font-mono text-sm text-dark-300">
                                            {session.id.slice(0, 8)}...
                                        </td>
                                        <td className="py-3">
                                            <div className="flex items-center gap-2">
                                                <div className="w-24 h-2 bg-dark-700 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-primary-500"
                                                        style={{ width: `${session.progress}%` }}
                                                    />
                                                </div>
                                                <span className="text-sm text-dark-400">{session.progress}%</span>
                                            </div>
                                        </td>
                                        <td className="py-3 text-sm text-dark-400">
                                            {session.created_at ? new Date(session.created_at).toLocaleString() : '-'}
                                        </td>
                                        <td className="py-3 text-sm text-dark-400 max-w-xs truncate">
                                            {session.result_message || '-'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({
    icon,
    label,
    value,
    subtext,
    color,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
    subtext?: string;
    color: 'primary' | 'success' | 'error' | 'warning';
}) {
    const colors = {
        primary: 'from-primary-500/20 to-primary-600/10 border-primary-500/30 text-primary-400',
        success: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
        error: 'from-red-500/20 to-red-600/10 border-red-500/30 text-red-400',
        warning: 'from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-400',
    };

    return (
        <div className={`rounded-xl p-4 bg-gradient-to-br ${colors[color]} border`}>
            <div className="flex items-center gap-2 mb-2">
                {icon}
                <span className="text-sm text-dark-400">{label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            {subtext && <div className="text-sm text-dark-500 mt-1">{subtext}</div>}
        </div>
    );
}
