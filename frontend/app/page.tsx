'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Play, Settings, BarChart3, Zap } from 'lucide-react';

interface Exam {
    id: string;
    name: string;
    slug: string;
    is_active: boolean;
}

interface Stats {
    totalExams: number;
    activeExams: number;
    totalRuns: number;
    successRate: number;
}

export default function Dashboard() {
    const [exams, setExams] = useState<Exam[]>([]);
    const [stats, setStats] = useState<Stats>({
        totalExams: 0,
        activeExams: 0,
        totalRuns: 0,
        successRate: 0,
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchExams();
    }, []);

    const fetchExams = async () => {
        try {
            const res = await fetch('/api/exams');
            if (res.ok) {
                const data = await res.json();
                setExams(data);
                setStats({
                    totalExams: data.length,
                    activeExams: data.filter((e: Exam) => e.is_active).length,
                    totalRuns: 0,
                    successRate: 0,
                });
            }
        } catch (error) {
            console.error('Failed to fetch exams:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                <p className="text-dark-400">Manage your exam automations</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <StatCard
                    icon={<Settings className="w-5 h-5" />}
                    label="Total Exams"
                    value={stats.totalExams.toString()}
                    color="primary"
                />
                <StatCard
                    icon={<Zap className="w-5 h-5" />}
                    label="Active"
                    value={stats.activeExams.toString()}
                    color="success"
                />
                <StatCard
                    icon={<Play className="w-5 h-5" />}
                    label="Total Runs"
                    value={stats.totalRuns.toString()}
                    color="warning"
                />
                <StatCard
                    icon={<BarChart3 className="w-5 h-5" />}
                    label="Success Rate"
                    value={`${stats.successRate}%`}
                    color="info"
                />
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <Link href="/workflow" className="card group cursor-pointer">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Play className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Start New Workflow</h3>
                            <p className="text-dark-400 text-sm">Run form automation for an exam</p>
                        </div>
                    </div>
                </Link>
                <Link href="/exams" className="card group cursor-pointer">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-dark-600 to-dark-700 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Settings className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Manage Exams</h3>
                            <p className="text-dark-400 text-sm">Add or edit exam configurations</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Recent Exams */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white">Recent Exams</h2>
                    <Link href="/exams" className="text-primary-500 hover:text-primary-400 text-sm">
                        View all →
                    </Link>
                </div>
                {loading ? (
                    <div className="text-center py-8 text-dark-400">Loading...</div>
                ) : exams.length === 0 ? (
                    <div className="text-center py-8">
                        <p className="text-dark-400 mb-4">No exams configured yet</p>
                        <Link href="/exams" className="btn btn-primary">
                            Add First Exam
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {exams.slice(0, 5).map((exam) => (
                            <div
                                key={exam.id}
                                className="flex items-center justify-between p-3 rounded-lg bg-dark-800 hover:bg-dark-700 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-2 h-2 rounded-full ${exam.is_active ? 'bg-green-500' : 'bg-dark-500'}`} />
                                    <span className="font-medium">{exam.name}</span>
                                    <span className="text-dark-500 text-sm">/{exam.slug}</span>
                                </div>
                                <Link
                                    href={`/workflow?examId=${exam.id}`}
                                    className="text-primary-500 hover:text-primary-400 text-sm"
                                >
                                    Run →
                                </Link>
                            </div>
                        ))}
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
    color,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
    color: 'primary' | 'success' | 'warning' | 'info';
}) {
    const colors = {
        primary: 'from-primary-500/20 to-primary-600/10 border-primary-500/30',
        success: 'from-green-500/20 to-green-600/10 border-green-500/30',
        warning: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
        info: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30',
    };

    return (
        <div className={`rounded-xl p-4 bg-gradient-to-br ${colors[color]} border`}>
            <div className="flex items-center gap-2 text-dark-400 mb-2">
                {icon}
                <span className="text-sm">{label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
        </div>
    );
}
