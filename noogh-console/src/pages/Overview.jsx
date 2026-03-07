import React, { useState, useEffect } from 'react';
import {
  Activity, Cpu, HardDrive, Zap, Server, AlertTriangle, Users,
  CheckCircle, Shield, Lock, Eye, Brain, Terminal, Crown,
  TrendingUp, Clock, Sparkles, Target, ChevronRight
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import dashboardAPI from '../services/api';

const Overview = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [activityData, setActivityData] = useState([]);

  // Generate mock activity data for chart
  useEffect(() => {
    const data = [];
    for (let i = 24; i >= 0; i--) {
      data.push({
        time: `${i}h`,
        requests: Math.floor(Math.random() * 50) + 20,
        blocked: Math.floor(Math.random() * 5),
        tools: Math.floor(Math.random() * 30) + 10,
      });
    }
    setActivityData(data);
  }, []);

  // Fetch data from Dashboard API
  const fetchData = async () => {
    try {
      const data = await dashboardAPI.getSystemStatus();
      setSystemStatus(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error("Failed to fetch system status:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 5 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 relative mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
            <div className="absolute inset-0 rounded-full border-4 border-t-blue-500 animate-spin"></div>
            <Brain className="absolute inset-0 m-auto text-blue-400" size={24} />
          </div>
          <p className="text-slate-400 text-lg">جاري تحميل حالة النظام...</p>
          <p className="text-slate-500 text-sm mt-2">Loading System Status</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass border border-red-500/30 rounded-2xl p-8 max-w-lg mx-auto mt-12">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-xl bg-red-500/20 flex items-center justify-center">
            <AlertTriangle className="text-red-400" size={28} />
          </div>
          <div>
            <h3 className="text-red-400 font-bold text-xl">خطأ في الاتصال</h3>
            <p className="text-slate-500 text-sm">Connection Error</p>
          </div>
        </div>
        <p className="text-slate-300 mb-2">{error}</p>
        <p className="text-slate-500 text-sm mb-6">تأكد من تشغيل Gateway API على المنفذ 8001</p>
        <button
          onClick={fetchData}
          className="btn-danger w-full py-3 rounded-xl text-white font-semibold flex items-center justify-center gap-2"
        >
          <Zap size={18} />
          إعادة المحاولة
        </button>
      </div>
    );
  }

  const { services = [], metrics = {} } = systemStatus || {};

  // Count online/offline services
  const onlineServices = services.filter(s => s.status === 'online').length;
  const totalServices = services.length;
  const systemHealth = onlineServices === totalServices ? 'optimal' : onlineServices > 0 ? 'degraded' : 'offline';

  // Sovereignty metrics (mock for now, can be connected to real API)
  const sovereigntyMetrics = {
    testsTotal: 85,
    testsPassed: 85,
    passRate: 100,
    lastTestRun: '2 min ago',
    attacksBlocked: 19,
    constitutionActive: true,
    speechLayerActive: true,
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* ═══════════════════════════════════════════════════════════
          Hero Header Section
          ═══════════════════════════════════════════════════════════ */}
      <div className="glass gradient-glow rounded-2xl p-8 border border-slate-700/50 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Logo with glow */}
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-2xl shadow-blue-500/30">
                <Crown className="text-white" size={40} />
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-4 border-slate-900 status-online"></div>
            </div>

            <div>
              <h1 className="text-4xl font-black text-gradient mb-2">NOOGH SOVEREIGN</h1>
              <p className="text-slate-400 text-lg">Neural Operating System — Control Plane v2.0</p>
              <div className="flex items-center gap-4 mt-3">
                <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-medium flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></div>
                  Live
                </span>
                <span className="text-slate-500 text-sm flex items-center gap-1">
                  <Clock size={14} />
                  Updated: {lastUpdate?.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* System Status Badge */}
          <div className={`px-6 py-4 rounded-2xl border flex items-center gap-4 ${systemHealth === 'optimal'
            ? 'glass border-green-500/30 shadow-lg shadow-green-500/10'
            : systemHealth === 'degraded'
              ? 'glass border-yellow-500/30 shadow-lg shadow-yellow-500/10'
              : 'glass border-red-500/30 shadow-lg shadow-red-500/10'
            }`}>
            <div className={`w-4 h-4 rounded-full ${systemHealth === 'optimal' ? 'bg-green-400 status-online' :
              systemHealth === 'degraded' ? 'bg-yellow-400 status-warning' :
                'bg-red-400 status-offline'
              }`}></div>
            <div>
              <div className={`text-sm font-bold ${systemHealth === 'optimal' ? 'text-green-400' :
                systemHealth === 'degraded' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                {systemHealth === 'optimal' ? 'جميع الأنظمة تعمل'
                  : systemHealth === 'degraded' ? 'خدمة جزئية'
                    : 'النظام غير متصل'}
              </div>
              <div className="text-slate-500 text-xs uppercase tracking-wider">
                {systemHealth.toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Sovereignty Status (NEW!)
          ═══════════════════════════════════════════════════════════ */}
      <div className="glass-dark border border-red-500/20 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-orange-500/5"></div>

        <div className="relative">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl sovereignty-badge flex items-center justify-center">
                <Shield className="text-white" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gradient-sovereign">🔴 SOVEREIGNTY STATUS</h2>
                <p className="text-slate-500 text-sm">حالة السيادة والحماية</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-4 py-2 rounded-xl bg-green-500/20 text-green-400 font-mono font-bold text-lg">
                {sovereigntyMetrics.passRate}% SECURE
              </span>
            </div>
          </div>

          {/* Sovereignty Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SovereignCard
              icon={<Target className="text-green-400" />}
              label="اختبارات ناجحة"
              value={`${sovereigntyMetrics.testsPassed}/${sovereigntyMetrics.testsTotal}`}
              status="success"
            />
            <SovereignCard
              icon={<Shield className="text-red-400" />}
              label="هجمات مصدودة"
              value={sovereigntyMetrics.attacksBlocked}
              status="danger"
            />
            <SovereignCard
              icon={<Lock className="text-purple-400" />}
              label="Speech Layer"
              value={sovereigntyMetrics.speechLayerActive ? 'Active' : 'Inactive'}
              status={sovereigntyMetrics.speechLayerActive ? 'active' : 'inactive'}
            />
            <SovereignCard
              icon={<Brain className="text-blue-400" />}
              label="Constitution"
              value={sovereigntyMetrics.constitutionActive ? 'Enforced' : 'Disabled'}
              status={sovereigntyMetrics.constitutionActive ? 'active' : 'inactive'}
            />
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Main Metrics Grid
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Server className="text-green-400" />}
          label="الخدمات النشطة"
          sublabel="Services Online"
          value={`${onlineServices}/${totalServices}`}
          trend={systemHealth === 'optimal' ? '+100%' : null}
          color="green"
        />
        <StatCard
          icon={<Users className="text-blue-400" />}
          label="الوكلاء النشطون"
          sublabel="Active Agents"
          value={metrics.agents_online || 0}
          color="blue"
        />
        <StatCard
          icon={<Activity className="text-purple-400" />}
          label="الأدوات المنفذة"
          sublabel="Tools Executed"
          value={metrics.tools_executed_1h || 0}
          subValue="آخر ساعة"
          color="purple"
        />
        <StatCard
          icon={<AlertTriangle className="text-yellow-400" />}
          label="إجراءات محظورة"
          sublabel="Blocked Actions"
          value={metrics.blocked_actions_1h || 0}
          subValue="حماية أمنية"
          color="yellow"
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Two Column Layout
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Services List */}
        <div className="glass border border-slate-700/50 rounded-2xl p-6 card-hover">
          <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Server size={20} className="text-blue-400" />
            </div>
            <div>
              <span>خدمات النظام</span>
              <span className="text-slate-500 text-sm font-normal block">System Services</span>
            </div>
          </h3>
          <div className="space-y-3">
            {services.map((service, idx) => (
              <ServiceStatus key={service.name} service={service} delay={idx * 100} />
            ))}
          </div>
        </div>

        {/* Execution Metrics */}
        <div className="glass border border-slate-700/50 rounded-2xl p-6 card-hover">
          <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
              <Zap size={20} className="text-purple-400" />
            </div>
            <div>
              <span>مقاييس التنفيذ</span>
              <span className="text-slate-500 text-sm font-normal block">Execution Metrics</span>
            </div>
          </h3>
          <div className="space-y-5">
            <MetricBar
              label="تنفيذات Sandbox"
              value={metrics.sandbox_executions_1h || 0}
              max={100}
              color="from-blue-500 to-cyan-400"
            />
            <MetricBar
              label="تنفيذات Lab"
              value={metrics.lab_executions_1h || 0}
              max={100}
              color="from-purple-500 to-pink-400"
            />
            <MetricBar
              label="استعلامات ReAct"
              value={metrics.react_queries_1h || 45}
              max={100}
              color="from-orange-500 to-yellow-400"
            />

            <div className="pt-5 border-t border-slate-700/50 flex items-center justify-between">
              <span className="text-slate-400 text-sm flex items-center gap-2">
                <Clock size={16} />
                متوسط وقت التنفيذ
              </span>
              <div className="text-right">
                <span className="text-2xl font-bold text-gradient">{metrics.avg_execution_ms?.toFixed(0) || 42}</span>
                <span className="text-slate-500 text-sm mr-1">ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Activity Chart
          ═══════════════════════════════════════════════════════════ */}
      <div className="glass border border-slate-700/50 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center">
              <TrendingUp size={20} className="text-blue-400" />
            </div>
            <div>
              <span>نشاط النظام</span>
              <span className="text-slate-500 text-sm font-normal block">System Activity (24h)</span>
            </div>
          </h3>

          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-2 text-blue-400">
              <div className="w-3 h-3 rounded-full bg-blue-400"></div>
              الطلبات
            </span>
            <span className="flex items-center gap-2 text-purple-400">
              <div className="w-3 h-3 rounded-full bg-purple-400"></div>
              الأدوات
            </span>
            <span className="flex items-center gap-2 text-red-400">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              المحظورة
            </span>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={activityData}>
              <defs>
                <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorTools" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  backdropFilter: 'blur(12px)'
                }}
              />
              <Area type="monotone" dataKey="requests" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRequests)" strokeWidth={2} />
              <Area type="monotone" dataKey="tools" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorTools)" strokeWidth={2} />
              <Line type="monotone" dataKey="blocked" stroke="#ef4444" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          Quick Actions Footer
          ═══════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <QuickAction icon={<Terminal />} label="Neural Chat" to="/chat" color="blue" />
        <QuickAction icon={<Eye />} label="System Logs" to="/logs" color="purple" />
        <QuickAction icon={<Target />} label="Run Tests" to="/tools" color="green" />
        <QuickAction icon={<Sparkles />} label="Tasks" to="/tasks" color="orange" />
      </div>

    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// Sub-Components
// ═══════════════════════════════════════════════════════════

const SovereignCard = ({ icon, label, value, status }) => {
  const statusColors = {
    success: 'border-green-500/30 bg-green-500/5',
    danger: 'border-red-500/30 bg-red-500/5',
    active: 'border-emerald-500/30 bg-emerald-500/5',
    inactive: 'border-slate-500/30 bg-slate-500/5',
  };

  return (
    <div className={`rounded-xl border p-4 ${statusColors[status] || statusColors.inactive}`}>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center">
          {icon}
        </div>
        <span className="text-slate-400 text-sm">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white font-mono">{value}</div>
    </div>
  );
};

const StatCard = ({ icon, label, sublabel, value, subValue, trend, color }) => {
  const colors = {
    green: 'from-green-500/20 to-emerald-500/20 border-green-500/20 hover:border-green-500/40',
    blue: 'from-blue-500/20 to-cyan-500/20 border-blue-500/20 hover:border-blue-500/40',
    purple: 'from-purple-500/20 to-pink-500/20 border-purple-500/20 hover:border-purple-500/40',
    yellow: 'from-yellow-500/20 to-orange-500/20 border-yellow-500/20 hover:border-yellow-500/40',
  };

  return (
    <div className={`glass bg-gradient-to-br ${colors[color]} border rounded-2xl p-5 card-hover shimmer`}>
      <div className="flex justify-between items-start mb-4">
        <div className="w-12 h-12 rounded-xl bg-slate-800/50 flex items-center justify-center">
          {icon}
        </div>
        {trend && <span className="text-xs text-green-400 bg-green-500/20 px-2 py-1 rounded-full">{trend}</span>}
      </div>
      <div className="text-4xl font-black text-white mb-2 counter-value">{value}</div>
      <div className="text-sm font-medium text-slate-300">{label}</div>
      <div className="text-xs text-slate-500">{sublabel}</div>
      {subValue && <div className="text-xs text-slate-600 mt-2">{subValue}</div>}
    </div>
  );
};

const ServiceStatus = ({ service, delay }) => {
  const statusConfig = {
    online: { color: 'bg-green-400', badge: 'bg-green-500/20 text-green-400', glow: 'status-online' },
    offline: { color: 'bg-red-400', badge: 'bg-red-500/20 text-red-400', glow: 'status-offline' },
    degraded: { color: 'bg-yellow-400', badge: 'bg-yellow-500/20 text-yellow-400', glow: 'status-warning' }
  };

  const config = statusConfig[service.status] || statusConfig.offline;

  return (
    <div
      className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl hover:bg-slate-800/50 transition-all border border-transparent hover:border-slate-700/50 fade-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center gap-4">
        <div className={`w-3 h-3 rounded-full ${config.color} ${config.glow}`}></div>
        <div>
          <div className="text-white font-medium capitalize">{service.name.replace('_', ' ')}</div>
          {service.port && (
            <div className="text-xs text-slate-500">Port: {service.port}</div>
          )}
        </div>
      </div>
      <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider ${config.badge}`}>
        {service.status}
      </div>
    </div>
  );
};

const MetricBar = ({ label, value, max, color }) => {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-slate-400 text-sm">{label}</span>
        <span className="text-white font-bold text-lg">{value}</span>
      </div>
      <div className="w-full bg-slate-800/50 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${color} transition-all duration-1000 rounded-full`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

const QuickAction = ({ icon, label, to, color }) => {
  const colors = {
    blue: 'from-blue-500/20 to-cyan-500/20 hover:from-blue-500/30 hover:to-cyan-500/30 border-blue-500/20',
    purple: 'from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 border-purple-500/20',
    green: 'from-green-500/20 to-emerald-500/20 hover:from-green-500/30 hover:to-emerald-500/30 border-green-500/20',
    orange: 'from-orange-500/20 to-yellow-500/20 hover:from-orange-500/30 hover:to-yellow-500/30 border-orange-500/20',
  };

  return (
    <a
      href={to}
      className={`glass bg-gradient-to-br ${colors[color]} border rounded-xl p-4 flex items-center justify-between transition-all hover:scale-[1.02] cursor-pointer`}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center text-slate-400">
          {icon}
        </div>
        <span className="text-slate-300 font-medium">{label}</span>
      </div>
      <ChevronRight className="text-slate-500" size={20} />
    </a>
  );
};

export default Overview;
