import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, Filter, Search, ChevronRight } from 'lucide-react';
import dashboardAPI from '../services/api';

const Tasks = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all'); // all, completed, failed, blocked
    const [searchTerm, setSearchTerm] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const fetchTasks = async () => {
        try {
            setLoading(true);
            const params = {
                page,
                page_size: 20,
                ...(filter !== 'all' && { status: filter })
            };

            const data = await dashboardAPI.listTasks(params);
            setTasks(data.tasks || []);
            setTotalPages(Math.ceil((data.total || 0) / 20));
            setError(null);
        } catch (err) {
            console.error("Failed to fetch tasks:", err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, [page, filter]);

    // Filter tasks by search term
    const filteredTasks = tasks.filter(task =>
        task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.task_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.agent_role.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading && tasks.length === 0) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-slate-400">Loading tasks...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white mb-2">Task Execution History</h1>
                <p className="text-slate-400">Monitor and track all task executions across the platform</p>
            </div>

            {/* Controls Bar */}
            <div className="bg-noogh-800 border border-slate-700 rounded-xl p-4">
                <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
                    {/* Search */}
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search tasks by ID, title, or agent..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none"
                        />
                    </div>

                    {/* Filters */}
                    <div className="flex items-center gap-2">
                        <Filter size={18} className="text-slate-400" />
                        <select
                            value={filter}
                            onChange={(e) => {
                                setFilter(e.target.value);
                                setPage(1);
                            }}
                            className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:border-blue-500 focus:outline-none"
                        >
                            <option value="all">All Tasks</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                            <option value="blocked">Blocked</option>
                            <option value="running">Running</option>
                        </select>
                    </div>

                    {/* Refresh */}
                    <button
                        onClick={fetchTasks}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        <Clock size={18} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Error State */}
            {error && (
                <div className="bg-red-500/10 border border-red-500 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                        <AlertCircle className="text-red-400" size={24} />
                        <div>
                            <h3 className="text-red-400 font-semibold">Failed to load tasks</h3>
                            <p className="text-slate-300 text-sm">{error}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Tasks Table */}
            <div className="bg-noogh-800 border border-slate-700 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-700/50 border-b border-slate-700">
                            <tr>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Task ID</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Title</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Agent</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Risk</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Isolation</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Status</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Duration</th>
                                <th className="text-left px-6 py-4 text-slate-300 font-semibold text-sm">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTasks.length === 0 ? (
                                <tr>
                                    <td colSpan="8" className="text-center py-12 text-slate-400">
                                        No tasks found
                                    </td>
                                </tr>
                            ) : (
                                filteredTasks.map((task) => (
                                    <TaskRow key={task.task_id} task={task} />
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="border-t border-slate-700 px-6 py-4 flex items-center justify-between">
                        <div className="text-sm text-slate-400">
                            Page {page} of {totalPages}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// Task Row Component
const TaskRow = ({ task }) => {
    const statusConfig = {
        completed: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
        failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
        blocked: { icon: AlertCircle, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
        running: { icon: Clock, color: 'text-blue-400', bg: 'bg-blue-500/20' },
        pending: { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/20' },
    };

    const config = statusConfig[task.status] || statusConfig.pending;
    const StatusIcon = config.icon;

    const riskColors = {
        SAFE: 'text-green-400 bg-green-500/20',
        RESTRICTED: 'text-yellow-400 bg-yellow-500/20',
        DANGEROUS: 'text-red-400 bg-red-500/20',
    };

    const isolationColors = {
        none: 'text-slate-400 bg-slate-500/20',
        sandbox: 'text-blue-400 bg-blue-500/20',
        lab_container: 'text-purple-400 bg-purple-500/20',
    };

    return (
        <tr className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
            <td className="px-6 py-4">
                <code className="text-xs text-blue-400 font-mono">{task.task_id.slice(0, 8)}...</code>
            </td>
            <td className="px-6 py-4">
                <div className="text-white font-medium">{task.title}</div>
                {task.capability && (
                    <div className="text-xs text-slate-500 mt-1">{task.capability}</div>
                )}
            </td>
            <td className="px-6 py-4">
                <span className="text-slate-300">{task.agent_role}</span>
            </td>
            <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${riskColors[task.risk_level] || 'text-slate-400'}`}>
                    {task.risk_level}
                </span>
            </td>
            <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${isolationColors[task.isolation] || 'text-slate-400'}`}>
                    {task.isolation}
                </span>
            </td>
            <td className="px-6 py-4">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full w-fit ${config.bg}`}>
                    <StatusIcon size={14} className={config.color} />
                    <span className={`text-xs font-medium ${config.color} capitalize`}>
                        {task.status}
                    </span>
                </div>
            </td>
            <td className="px-6 py-4">
                <span className="text-slate-300 text-sm">
                    {task.duration_ms ? `${(task.duration_ms / 1000).toFixed(2)}s` : '-'}
                </span>
            </td>
            <td className="px-6 py-4">
                <button className="p-2 hover:bg-slate-600 rounded-lg transition-colors text-slate-400 hover:text-white">
                    <ChevronRight size={18} />
                </button>
            </td>
        </tr>
    );
};

export default Tasks;
