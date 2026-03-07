import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, ScrollText, Wrench, LogOut, User, ShieldAlert } from 'lucide-react';

// Auth
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Overview from './pages/Overview';
import Chat from './pages/Chat';
import Logs from './pages/Logs';
import Tools from './pages/Tools';
import Tasks from './pages/Tasks';
import Forensics from './pages/Forensics';

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    {/* Public Route - Login */}
                    <Route path="/login" element={<Login />} />

                    {/* Protected Routes - Dashboard */}
                    <Route path="/*" element={
                        <ProtectedRoute>
                            <DashboardLayout />
                        </ProtectedRoute>
                    } />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

// Dashboard Layout (Protected)
function DashboardLayout() {
    const { user, logout } = useAuth();

    return (
        <div className="flex h-screen bg-noogh-900 text-slate-200 font-sans">
            {/* === Sidebar === */}
            <aside className="w-64 bg-noogh-800 border-r border-slate-700 flex flex-col shadow-2xl">
                {/* Logo Area */}
                <div className="p-6 flex items-center gap-3 border-b border-slate-700">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <span className="font-bold text-white">N</span>
                    </div>
                    <div>
                        <h1 className="font-bold text-lg tracking-wider text-white">NOOGH</h1>
                        <p className="text-xs text-slate-400">Unified System v2.0</p>
                    </div>
                </div>

                {/* Navigation Links */}
                <nav className="flex-1 p-4 space-y-2 mt-4">
                    <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Overview" />
                    <NavItem to="/forensics" icon={<ShieldAlert size={20} className="text-red-400" />} label="Forensic Audit" />
                    <NavItem to="/tasks" icon={<ScrollText size={20} />} label="Tasks" />
                    <NavItem to="/chat" icon={<MessageSquare size={20} />} label="Neural Chat" />
                    <NavItem to="/logs" icon={<ScrollText size={20} />} label="System Logs" />
                    <NavItem to="/tools" icon={<Wrench size={20} />} label="Dev Tools" />
                </nav>

                {/* User Info & Logout */}
                <div className="p-4 bg-slate-900/50 border-t border-slate-700 space-y-3">
                    {/* User Info */}
                    {user && (
                        <div className="flex items-center gap-3 px-3 py-2 bg-slate-800 rounded-lg">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center">
                                <User size={16} className="text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">{user.username}</p>
                                <p className="text-xs text-slate-400 capitalize">{user.role}</p>
                            </div>
                        </div>
                    )}

                    {/* Logout Button */}
                    <button
                        onClick={logout}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                        <LogOut size={16} />
                        <span>Logout</span>
                    </button>
                </div>
            </aside>

            {/* === Main Content Area === */}
            <main className="flex-1 flex flex-col overflow-hidden bg-slate-900">
                {/* Top Header */}
                <header className="h-16 bg-noogh-800/80 backdrop-blur-md border-b border-slate-700 flex items-center justify-between px-6 z-10">
                    <h2 className="text-sm font-medium text-slate-300">Console Dashboard</h2>
                    <div className="flex items-center gap-4">
                        {user && (
                            <span className="text-xs text-slate-400">
                                Welcome, <span className="text-blue-400 font-medium">{user.full_name}</span>
                            </span>
                        )}
                    </div>
                </header>

                {/* Page Content (Scrollable) */}
                <div className="flex-1 overflow-auto p-6">
                    <Routes>
                        <Route path="/" element={<Overview />} />
                        <Route path="/forensics" element={<Forensics />} />
                        <Route path="/tasks" element={<Tasks />} />
                        <Route path="/chat" element={<Chat />} />
                        <Route path="/logs" element={<Logs />} />
                        <Route path="/tools" element={<Tools />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}

// Navigation Item Component
function NavItem({ to, icon, label }) {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                    ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20'
                    : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-100'
                }`
            }
        >
            <span className="group-hover:scale-110 transition-transform">{icon}</span>
            <span className="font-medium text-sm">{label}</span>
        </NavLink>
    );
}

export default App;
