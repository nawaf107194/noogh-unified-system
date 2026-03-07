import React from 'react';
import {
    Brain,
    Search,
    Wrench,
    Database,
    AlertCircle,
    ChevronRight,
    ChevronDown,
    Clock
} from 'lucide-react';

const ForensicGraph = ({ traces }) => {
    if (!traces || traces.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-500 border-2 border-dashed border-slate-800 rounded-3xl">
                <Brain size={48} className="mb-4 opacity-20" />
                <p>No cognitive traces found for this period.</p>
            </div>
        );
    }

    // Group traces by trace_id
    const grouped = traces.reduce((acc, trace) => {
        if (!acc[trace.trace_id]) {
            acc[trace.trace_id] = [];
        }
        acc[trace.trace_id].push(trace);
        return acc;
    }, {});

    return (
        <div className="space-y-8">
            {Object.entries(grouped).map(([traceId, items]) => (
                <TraceGroup key={traceId} traceId={traceId} items={items} />
            ))}
        </div>
    );
};

const TraceGroup = ({ traceId, items }) => {
    const [isExpanded, setIsExpanded] = React.useState(true);

    return (
        <div className="bg-slate-900/40 rounded-3xl border border-slate-800 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
            <div
                className="p-4 bg-slate-800/50 flex items-center justify-between cursor-pointer"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400">
                        <Brain size={18} />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-white">Thought Flow: {traceId}</h3>
                        <p className="text-xs text-slate-400">{items.length} steps recorded</p>
                    </div>
                </div>
                <button className="text-slate-500 hover:text-white transition-colors">
                    {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                </button>
            </div>

            {isExpanded && (
                <div className="p-6 relative">
                    {/* Vertical line connecting nodes */}
                    <div className="absolute left-10 top-8 bottom-8 w-0.5 bg-slate-800 z-0" />

                    <div className="space-y-6 relative z-10">
                        {items.map((item, idx) => (
                            <TraceNode key={idx} item={item} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const TraceNode = ({ item }) => {
    const [showDetail, setShowDetail] = React.useState(false);
    const data = item.data || {};

    const getIcon = (type) => {
        switch (type) {
            case 'thought': return <Brain size={16} />;
            case 'tool_call': return <Wrench size={16} />;
            case 'observation': return <Search size={16} />;
            case 'memory': return <Database size={16} />;
            default: return <ChevronRight size={16} />;
        }
    };

    const getColor = (type) => {
        switch (type) {
            case 'thought': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
            case 'tool_call': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'observation': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
            case 'memory': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    const formatTime = (ts) => {
        try {
            return new Date(ts).toLocaleTimeString();
        } catch (e) {
            return ts;
        }
    };

    return (
        <div className="flex gap-4 group">
            {/* Node Bullet */}
            <div className={`mt-1 w-8 h-8 rounded-full border flex items-center justify-center shrink-0 z-10 transition-transform group-hover:scale-110 ${getColor(item.event_type)}`}>
                {getIcon(item.event_type)}
            </div>

            {/* Node Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded uppercase tracking-wider">
                        {item.event_type}
                    </span>
                    <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock size={10} />
                        {formatTime(item.timestamp)}
                    </span>
                </div>

                <div
                    className="p-4 bg-slate-800/30 hover:bg-slate-800/50 rounded-2xl border border-slate-700/50 cursor-pointer transition-all"
                    onClick={() => setShowDetail(!showDetail)}
                >
                    <p className="text-sm text-slate-200 leading-relaxed">
                        {item.message}
                    </p>

                    {showDetail && (
                        <div className="mt-4 pt-4 border-t border-slate-700/50">
                            <pre className="text-[11px] font-mono text-blue-300 overflow-x-auto p-3 bg-slate-900/80 rounded-xl max-h-60">
                                {JSON.stringify(data, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ForensicGraph;
