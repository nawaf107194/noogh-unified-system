import { useEffect, useState } from 'react';
import { API_BASE } from '../lib/config';

export default function Tools() {
    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [result, setResult] = useState(null);
    const [executing, setExecuting] = useState(null);
    const [confirmDialog, setConfirmDialog] = useState(null);

    useEffect(() => {
        fetchTools();
    }, []);

    const fetchTools = async () => {
        try {
            const res = await fetch(`${API_BASE}/system/tools`);
            const data = await res.json();
            setTools(data.tools || []);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            setResult({ status: 'error', message: 'Failed to fetch tools: ' + err.message });
        }
    };

    const requestTool = async (toolName, confirm = false) => {
        setExecuting(toolName);
        setResult(null);
        setConfirmDialog(null);

        try {
            const response = await fetch(`${API_BASE}/system/tools/${toolName}/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    reason: 'Console request',
                    confirm: confirm,
                }),
            });
            const data = await response.json();

            if (data.status === 'pending_confirmation') {
                // Show confirmation dialog
                setConfirmDialog({
                    tool: toolName,
                    message: data.message,
                    risk: data.risk,
                });
            } else {
                setResult(data);
            }
        } catch (err) {
            setResult({ status: 'error', message: err.message });
        } finally {
            setExecuting(null);
        }
    };

    const confirmExecution = () => {
        if (confirmDialog) {
            requestTool(confirmDialog.tool, true);
        }
    };

    const cancelConfirmation = () => {
        setConfirmDialog(null);
    };

    const getRiskClass = (risk) => {
        if (risk === 'high') return 'risk-high';
        if (risk === 'medium') return 'risk-medium';
        return 'risk-low';
    };

    const getRiskIcon = (risk) => {
        if (risk === 'high') return '🔴';
        if (risk === 'medium') return '🟡';
        return '🟢';
    };

    return (
        <div>
            <h1 className="page-header">🔧 Tools Registry</h1>

            {/* Confirmation Dialog */}
            {confirmDialog && (
                <div
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0,0,0,0.7)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                    }}
                >
                    <div
                        className="card"
                        style={{
                            maxWidth: 400,
                            borderColor: confirmDialog.risk === 'high' ? 'var(--accent-error)' : 'var(--accent-warning)',
                        }}
                    >
                        <h3 style={{ marginBottom: 12 }}>
                            {confirmDialog.risk === 'high' ? '⚠️ High Risk' : '⚡ Confirm Execution'}
                        </h3>
                        <p style={{ marginBottom: 16, color: 'var(--text-secondary)' }}>
                            {confirmDialog.message}
                        </p>
                        <p style={{ marginBottom: 16 }}>
                            <strong>Tool:</strong> {confirmDialog.tool}
                        </p>
                        <div style={{ display: 'flex', gap: 12 }}>
                            <button
                                onClick={confirmExecution}
                                style={{
                                    flex: 1,
                                    background:
                                        confirmDialog.risk === 'high'
                                            ? 'var(--accent-error)'
                                            : 'var(--accent-warning)',
                                    color: '#000',
                                    fontWeight: 600,
                                }}
                            >
                                ✓ Confirm
                            </button>
                            <button onClick={cancelConfirmation} style={{ flex: 1 }}>
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Result Banner */}
            {result && (
                <div
                    className="card"
                    style={{
                        marginBottom: 16,
                        borderColor:
                            result.status === 'queued'
                                ? 'var(--accent-success)'
                                : result.status === 'error'
                                    ? 'var(--accent-error)'
                                    : 'var(--accent-warning)',
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                        <strong>
                            {result.status === 'queued' ? '✓' : result.status === 'error' ? '✗' : '⚡'}
                        </strong>
                        <span>{result.status?.toUpperCase()}</span>
                        {result.execution_id && (
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                                ID: {result.execution_id}
                            </span>
                        )}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                        {result.message}
                    </div>
                </div>
            )}

            {/* Tools Table */}
            {loading ? (
                <div>Loading tools...</div>
            ) : (
                <div className="card">
                    <table className="tools-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Description</th>
                                <th>Risk</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tools.map((tool) => (
                                <tr key={tool.name}>
                                    <td style={{ fontWeight: 600, fontFamily: 'monospace' }}>{tool.name}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{tool.description || '—'}</td>
                                    <td className={getRiskClass(tool.risk)}>
                                        {getRiskIcon(tool.risk)} {tool.risk}
                                    </td>
                                    <td>{tool.enabled ? '✓ Enabled' : '✗ Disabled'}</td>
                                    <td>
                                        <button
                                            onClick={() => requestTool(tool.name)}
                                            disabled={!tool.enabled || executing === tool.name}
                                            style={
                                                tool.risk === 'high'
                                                    ? { borderColor: 'var(--accent-error)' }
                                                    : tool.risk === 'medium'
                                                        ? { borderColor: 'var(--accent-warning)' }
                                                        : {}
                                            }
                                        >
                                            {executing === tool.name ? '...' : 'Request'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Legend */}
            <div style={{ marginTop: 16, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <strong>Risk Levels:</strong> 🟢 Low (safe) | 🟡 Medium (confirm) | 🔴 High (explicit confirm
                required)
            </div>
        </div>
    );
}
