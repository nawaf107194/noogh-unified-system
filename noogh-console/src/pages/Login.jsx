import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, AlertCircle } from 'lucide-react';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const result = await login(username, password);

            if (result.success) {
                navigate('/');
            } else {
                setError(result.error || 'Login failed');
            }
        } catch (err) {
            setError(err.message || 'An error occurred during login');
        } finally {
            setIsLoading(false);
        }
    };

    const quickLogin = (user) => {
        setUsername(user.username);
        setPassword(user.password);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-noogh-900 to-slate-900">
            <div className="w-full max-w-md">
                {/* Login Card */}
                <div className="bg-noogh-800 rounded-2xl shadow-2xl border border-slate-700 overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-center">
                        <div className="flex items-center justify-center mb-2">
                            <LogIn className="w-10 h-10 text-white" />
                        </div>
                        <h1 className="text-2xl font-bold text-white">NOOGH Dashboard</h1>
                        <p className="text-blue-100 text-sm mt-1">Neural Operating System</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="p-8">
                        {/* Error Alert */}
                        {error && (
                            <div className="mb-6 bg-red-500/20 border border-red-500 text-red-400 p-4 rounded-lg flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <span className="text-sm">{error}</span>
                            </div>
                        )}

                        {/* Username */}
                        <div className="mb-5">
                            <label htmlFor="username" className="block text-slate-300 text-sm font-medium mb-2">
                                Username
                            </label>
                            <input
                                id="username"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                placeholder="Enter your username"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        {/* Password */}
                        <div className="mb-6">
                            <label htmlFor="password" className="block text-slate-300 text-sm font-medium mb-2">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                placeholder="Enter your password"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3 rounded-lg transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    <span>Logging in...</span>
                                </>
                            ) : (
                                <>
                                    <LogIn className="w-5 h-5" />
                                    <span>Login</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Quick Login (Demo) */}
                    <div className="px-8 pb-8">
                        <div className="border-t border-slate-700 pt-6">
                            <p className="text-slate-400 text-sm mb-3 text-center">Demo Accounts (Development Only)</p>
                            <div className="grid grid-cols-3 gap-2">
                                <button
                                    onClick={() => quickLogin({ username: 'admin', password: 'admin123' })}
                                    className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition-colors"
                                    type="button"
                                >
                                    Admin
                                </button>
                                <button
                                    onClick={() => quickLogin({ username: 'operator', password: 'operator123' })}
                                    className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition-colors"
                                    type="button"
                                >
                                    Operator
                                </button>
                                <button
                                    onClick={() => quickLogin({ username: 'viewer', password: 'viewer123' })}
                                    className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-lg transition-colors"
                                    type="button"
                                >
                                    Viewer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-500 text-sm mt-6">
                    NOOGH Dashboard v0.2.0 • Secure JWT Authentication
                </p>
            </div>
        </div>
    );
};

export default Login;
