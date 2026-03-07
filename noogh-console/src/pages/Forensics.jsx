import React, { useState, useEffect } from 'react';
import {
    ShieldAlert,
    RotateCw,
    Search,
    Filter,
    Activity,
    Download,
    Terminal
} from 'lucide-react';
import ForensicGraph from '../components/ForensicGraph';

const Forensics = () => {
    const [data, setData] = useState({ traces: [], total: 0 });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [autoRefresh, setAutoRefresh] = useState(true);

    const fetchData = async () => {
        try {
            setLoading(true);
            const token = localStorage.getItem('token');
            // The unified API is on port 8001
            const response = await fetch('/api/v1/dashboard/forensics?limit=200', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to fetch forensic data');

            const result = await response.json();
            setData(result);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();

        let interval;
        if (autoRefresh) {
            interval = setInterval(fetchData, 10000);
        }

        return () => clearInterval(interval);
    }, [autoRefresh]);

    const filteredTraces = data.traces.filter(t =>
        t.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.trace_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.event_type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <ShieldAlert size={20} className="text-red-500" />
                        <h1 className="text-2xl font-bold text-white tracking-tight">Forensic Audit</h1>
                    </div>
                    <p className="text-slate-400 text-sm">Real-time cognitive trace monitoring and reasoning analysis.</p>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setAutoRefresh(!autoRefresh)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${autoRefresh ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400'
                            }`}
                    >
                        <Activity size={16} className={autoRefresh ? 'animate-pulse' : ''} />
                        {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
                    </button>

                    <button
                        onClick={fetchData}
                        className="p-2 bg-slate-800 text-slate-300 hover:text-white rounded-xl transition-colors"
                        title="Manual Refresh"
                    >
                        <RotateCw size={20} className={loading && !autoRefresh ? 'animate-spin' : ''} />
                    </button>

                    <button
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-blue-500/20"
                    >
                        <Download size={16} />
                        Export Audit
                    </button>
                </div>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard
                    icon={<Terminal size={20} />}
                    label="Total Trace Records"
                    value={data.total}
                    color="blue"
                />
                <StatCard
                    icon={<Brain size={20} />}
                    label="Active Thought Flows"
                    value={new Set(data.traces.map(t => t.trace_id)).size}
                    color="purple"
                />
                <StatCard
                    icon={<ShieldAlert size={20} />}
                    label="Audit File Path"
                    value={data.file_path?.split('/').pop() || 'forensics_trace.jsonl'}
                    color="slate"
                    isSmallValue
                />
            </div>

            {/* Main Content & Sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* Sidebar: Filters & Search */}
                <div className="space-y-4">
                    <div className="bg-slate-800/50 p-6 rounded-3xl border border-slate-700/50">
                        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                            <Filter size={16} /> Filter Traces
                        </h2>

                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-slate-500 block mb-2">Search Content</label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-2.5 text-slate-500" size={16} />
                                    <input
                                        type="text"
                                        placeholder="Keywords, IDs..."
                                        className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs text-slate-500 block mb-2">Event Types</label>
                                <div className="flex flex-wrap gap-2">
                                    {['thought', 'tool_call', 'observation', 'memory'].map(type => (
                                        <span key={type} className="px-2 py-1 bg-slate-900 border border-slate-700 rounded-lg text-[10px] text-slate-400 hover:border-blue-500/50 cursor-pointer transition-colors">
                                            {type}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-red-500/5 to-purple-500/5 p-6 rounded-3xl border border-red-500/10">
                        <p className="text-xs text-slate-400 leading-relaxed italic">
                            "Forensic tracing ensures the agent's reasoning is auditable, explainable, and accountable to the user's sovereign intent."
                        </p>
                    </div>
                </div>

                {/* Main Graph View */}
                <div className="lg:col-span-3">
                    {error ? (
                        <div className="p-8 bg-red-500/10 border border-red-500/20 rounded-3xl text-red-400 flex items-center gap-3">
                            <ShieldAlert size={24} />
                            <div>
                                <p className="font-semibold">Connection Error</p>
                                <p className="text-sm opacity-80">{error}</p>
                            </div>
                        </div>
                    ) : (
                        <ForensicGraph traces={filteredTraces} />
                    )}
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon, label, value, color, isSmallValue }) => (
    <div className="bg-slate-800/40 p-6 rounded-3xl border border-slate-700/50 hover:border-slate-600 transition-all">
        <div className={`p-2 w-fit bg-${color}-500/10 text-${color}-400 rounded-xl mb-3`}>
            {icon}
        </div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        <p className={`${isSmallValue ? 'text-sm font-mono' : 'text-2xl font-bold'} text-white mt-1`}>{value}</p>
    </div>
);

const Brain = ({ size, className }) => <Activity size={size} className={className} />;

export default Forensics;
