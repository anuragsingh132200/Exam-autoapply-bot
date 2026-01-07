'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Play, Pause, RefreshCw, MessageSquare, Lock, Keyboard, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface Exam { id: string; name: string; slug: string; }
interface User { id: string; profile: { full_name: string; email: string; phone: string; }; }
interface LogEntry { message: string; level: string; timestamp: string; }

function WorkflowContent() {
    const searchParams = useSearchParams();
    const preselectedExamId = searchParams.get('examId');

    const [exams, setExams] = useState<Exam[]>([]);
    const [users, setUsers] = useState<User[]>([]);
    const [selectedExam, setSelectedExam] = useState('');
    const [selectedUser, setSelectedUser] = useState('');

    const [sessionId, setSessionId] = useState<string | null>(null);
    const [status, setStatus] = useState<'idle' | 'running' | 'waiting' | 'success' | 'failed'>('idle');
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [screenshot, setScreenshot] = useState<string | null>(null);

    // Intervention modals
    const [showOtpModal, setShowOtpModal] = useState(false);
    const [showCaptchaModal, setShowCaptchaModal] = useState(false);
    const [showCustomModal, setShowCustomModal] = useState(false);
    const [captchaImage, setCaptchaImage] = useState('');
    const [customField, setCustomField] = useState({ id: '', label: '', type: 'text' });
    const [inputValue, setInputValue] = useState('');

    const wsRef = useRef<WebSocket | null>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchExams();
        fetchUsers();
    }, []);

    useEffect(() => {
        if (preselectedExamId) setSelectedExam(preselectedExamId);
    }, [preselectedExamId]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const fetchExams = async () => {
        try {
            const res = await fetch('/api/exams');
            if (res.ok) setExams(await res.json());
        } catch (e) { console.error(e); }
    };

    const fetchUsers = async () => {
        try {
            const res = await fetch('/api/users');
            if (res.ok) setUsers(await res.json());
        } catch (e) { console.error(e); }
    };

    const startWorkflow = () => {
        if (!selectedExam || !selectedUser) return;

        const ws = new WebSocket(`ws://localhost:8000/ws/workflow`);
        wsRef.current = ws;

        ws.onopen = () => {
            ws.send(JSON.stringify({
                type: 'START_WORKFLOW',
                payload: { examId: selectedExam, userId: selectedUser }
            }));
            setStatus('running');
            setLogs([]);
            setProgress(0);
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            handleMessage(msg);
        };

        ws.onclose = () => {
            if (status === 'running') setStatus('failed');
        };
    };

    const handleMessage = (msg: any) => {
        const payload = msg.payload || {};

        switch (msg.type) {
            case 'SESSION_CREATED':
                setSessionId(payload.sessionId);
                break;
            case 'LOG':
                setLogs(prev => [...prev, {
                    message: payload.message,
                    level: payload.level,
                    timestamp: new Date().toLocaleTimeString()
                }]);
                break;
            case 'STATUS':
                setCurrentStep(payload.step);
                setProgress(payload.progress || 0);
                break;
            case 'SCREENSHOT':
                setScreenshot(payload.imageBase64);
                break;
            case 'REQUEST_OTP':
                setStatus('waiting');
                setShowOtpModal(true);
                break;
            case 'REQUEST_CAPTCHA':
                setStatus('waiting');
                setCaptchaImage(payload.imageBase64);
                setShowCaptchaModal(true);
                break;
            case 'REQUEST_CUSTOM_INPUT':
                setStatus('waiting');
                setCustomField({ id: payload.fieldId, label: payload.label, type: payload.type });
                setShowCustomModal(true);
                break;
            case 'RESULT':
                setStatus(payload.success ? 'success' : 'failed');
                wsRef.current?.close();
                break;
        }
    };

    const submitOtp = () => {
        if (!inputValue.trim()) return;
        wsRef.current?.send(JSON.stringify({ type: 'OTP_SUBMIT', payload: { otp: inputValue } }));
        setShowOtpModal(false);
        setInputValue('');
        setStatus('running');
    };

    const submitCaptcha = () => {
        if (!inputValue.trim()) return;
        wsRef.current?.send(JSON.stringify({ type: 'CAPTCHA_SUBMIT', payload: { solution: inputValue } }));
        setShowCaptchaModal(false);
        setInputValue('');
        setStatus('running');
    };

    const submitCustom = () => {
        if (!inputValue.trim()) return;
        wsRef.current?.send(JSON.stringify({
            type: 'CUSTOM_INPUT_SUBMIT',
            payload: { fieldId: customField.id, value: inputValue }
        }));
        setShowCustomModal(false);
        setInputValue('');
        setStatus('running');
    };

    const getStatusColor = () => {
        switch (status) {
            case 'running': return 'text-primary-500';
            case 'waiting': return 'text-amber-500';
            case 'success': return 'text-green-500';
            case 'failed': return 'text-red-500';
            default: return 'text-dark-400';
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">Workflow</h1>
                <p className="text-dark-400">Run exam registration automation</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Controls & Logs */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Control Panel */}
                    <div className="card">
                        <h2 className="text-lg font-semibold mb-4">Configuration</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                                <label className="block text-sm text-dark-400 mb-1">Exam</label>
                                <select
                                    value={selectedExam}
                                    onChange={(e) => setSelectedExam(e.target.value)}
                                    className="input"
                                    disabled={status === 'running'}
                                >
                                    <option value="">Select exam...</option>
                                    {exams.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-dark-400 mb-1">User</label>
                                <select
                                    value={selectedUser}
                                    onChange={(e) => setSelectedUser(e.target.value)}
                                    className="input"
                                    disabled={status === 'running'}
                                >
                                    <option value="">Select user...</option>
                                    {users.map(u => (
                                        <option key={u.id} value={u.id}>{u.profile.full_name} ({u.profile.phone})</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <button
                                onClick={startWorkflow}
                                disabled={!selectedExam || !selectedUser || status === 'running'}
                                className="btn btn-primary"
                            >
                                <Play className="w-4 h-4" />
                                Start Workflow
                            </button>
                            <div className={`flex items-center gap-2 ${getStatusColor()}`}>
                                {status === 'running' && <RefreshCw className="w-4 h-4 animate-spin" />}
                                {status === 'waiting' && <AlertCircle className="w-4 h-4" />}
                                {status === 'success' && <CheckCircle className="w-4 h-4" />}
                                {status === 'failed' && <XCircle className="w-4 h-4" />}
                                <span className="capitalize font-medium">{status}</span>
                            </div>
                        </div>

                        {/* Progress */}
                        {status !== 'idle' && (
                            <div className="mt-4">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-dark-400">{currentStep}</span>
                                    <span className="text-dark-400">{progress}%</span>
                                </div>
                                <div className="progress-bar">
                                    <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Logs */}
                    <div className="card">
                        <h2 className="text-lg font-semibold mb-4">Logs</h2>
                        <div className="h-64 overflow-y-auto bg-dark-900 rounded-lg p-3 font-mono text-sm">
                            {logs.length === 0 ? (
                                <p className="text-dark-500">No logs yet. Start a workflow to see activity.</p>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={i} className={`mb-1 ${log.level === 'error' ? 'text-red-400' :
                                            log.level === 'warning' ? 'text-amber-400' :
                                                log.level === 'success' ? 'text-green-400' : 'text-dark-300'
                                        }`}>
                                        <span className="text-dark-500">[{log.timestamp}]</span> {log.message}
                                    </div>
                                ))
                            )}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>

                {/* Right: Screenshot */}
                <div className="card h-fit">
                    <h2 className="text-lg font-semibold mb-4">Live View</h2>
                    <div className="aspect-[4/3] bg-dark-900 rounded-lg overflow-hidden flex items-center justify-center">
                        {screenshot ? (
                            <img
                                src={`data:image/png;base64,${screenshot}`}
                                alt="Browser screenshot"
                                className="w-full h-full object-contain"
                            />
                        ) : (
                            <p className="text-dark-500 text-sm">No screenshot available</p>
                        )}
                    </div>
                </div>
            </div>

            {/* OTP Modal */}
            {showOtpModal && (
                <Modal title="Enter OTP" icon={<MessageSquare className="w-6 h-6 text-primary-500" />}>
                    <p className="text-dark-400 mb-4">Please enter the OTP sent to your phone</p>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Enter 6-digit OTP"
                        className="input mb-4"
                        maxLength={6}
                        autoFocus
                    />
                    <button onClick={submitOtp} className="btn btn-primary w-full">Submit OTP</button>
                </Modal>
            )}

            {/* Captcha Modal */}
            {showCaptchaModal && (
                <Modal title="Solve Captcha" icon={<Lock className="w-6 h-6 text-amber-500" />}>
                    {captchaImage && (
                        <img src={`data:image/png;base64,${captchaImage}`} alt="Captcha" className="w-full rounded-lg mb-4" />
                    )}
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Enter captcha text"
                        className="input mb-4"
                        autoFocus
                    />
                    <button onClick={submitCaptcha} className="btn btn-primary w-full">Submit</button>
                </Modal>
            )}

            {/* Custom Input Modal */}
            {showCustomModal && (
                <Modal title={customField.label} icon={<Keyboard className="w-6 h-6 text-cyan-500" />}>
                    <p className="text-dark-400 mb-4">Please provide the following information</p>
                    <input
                        type={customField.type}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={`Enter ${customField.label.toLowerCase()}`}
                        className="input mb-4"
                        autoFocus
                    />
                    <button onClick={submitCustom} className="btn btn-primary w-full">Submit</button>
                </Modal>
            )}
        </div>
    );
}

function Modal({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-dark-800 rounded-xl p-6 w-full max-w-sm animate-fade-in">
                <div className="flex items-center gap-3 mb-4">
                    {icon}
                    <h2 className="text-xl font-semibold">{title}</h2>
                </div>
                {children}
            </div>
        </div>
    );
}

export default function WorkflowPage() {
    return (
        <Suspense fallback={<div className="p-8 text-center text-dark-400">Loading...</div>}>
            <WorkflowContent />
        </Suspense>
    );
}
