import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'Exam Automation Platform',
    description: 'AI-powered exam registration automation',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="min-h-screen bg-dark-950">
                <nav className="fixed top-0 left-0 right-0 z-50 bg-dark-900/80 backdrop-blur-sm border-b border-dark-700">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex items-center justify-between h-16">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
                                    <span className="text-white font-bold text-sm">EA</span>
                                </div>
                                <span className="font-semibold text-lg">Exam Automation</span>
                            </div>
                            <div className="flex items-center gap-4">
                                <a href="/" className="text-dark-300 hover:text-white transition-colors text-sm">Dashboard</a>
                                <a href="/exams" className="text-dark-300 hover:text-white transition-colors text-sm">Exams</a>
                                <a href="/users" className="text-dark-300 hover:text-white transition-colors text-sm">Users</a>
                                <a href="/workflow" className="text-dark-300 hover:text-white transition-colors text-sm">Workflow</a>
                                <a href="/batch" className="text-dark-300 hover:text-white transition-colors text-sm">Batch</a>
                                <a href="/analytics" className="text-dark-300 hover:text-white transition-colors text-sm">Analytics</a>
                            </div>
                        </div>
                    </div>
                </nav>
                <main className="pt-16">
                    {children}
                </main>
            </body>
        </html>
    );
}
