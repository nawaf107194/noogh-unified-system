import { useEffect, useState, useRef } from 'react';
import { API_BASE } from '../lib/config';

export default function Logs() {
    const [service, setService] = useState('gateway');
    const [level, setLevel] = useState('');
    const [lines, setLines] = useState([]);
    const [status, setStatus] = useState('connecting');
    const [source, setSource] = useState('loki'); // Indicate data source
    const logsRef = useRef(null);
    const eventSourceRef = useRef(null);

    useEffect(() => {
        // Close previous connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
        }

        setLines([{ type: 'info', text: 'Connecting to Loki log stream...', ts: Date.now() }]);
        setStatus('connecting');

        // Build SSE URL with filters
        let url = `${API_BASE}/system/logs/stream?service=${service}`;
        if (level) {
            url += `&level=${level}`;
        }

        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            setStatus('connected');
            setSource('loki');
            setLines([{ type: 'info', text: `Connected to Loki. Streaming ${service} logs...`, ts: Date.now() }]);
        };

        eventSource.addEventListener('log', (event) => {
            try {
                const data = JSON.parse(event.data);
                setLines((prev) => [
                    ...prev.slice(-500),
                    {
                        type: 'log',
                        service: data.service,
                        text: data.line,
                        ts: data.ts
                    }
                ]);
            } catch {
                // Plain text fallback
                setLines((prev) => [...prev.slice(-500), { type: 'log', text: event.data, ts: Date.now() }]);
            }
        });

        eventSource.onerror = () => {
            setStatus('error');
            setLines((prev) => [...prev, { type: 'error', text: '[Connection lost - attempting reconnect...]', ts: Date.now() }]);
        };

        return () => {
            eventSource.close();
        };
    }, [service, level]);

    useEffect(() => {
        if (logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    }, [lines]);

    const statusColors = {
        connecting: 'var(--accent-warning)',
        connected: 'var(--accent-success)',
        error: 'var(--accent-error)',
    };

    const getLineClass = (line) => {
        if (line.type === 'error') return 'log-error';
        if (line.type === 'info') return 'log-info';
        const text = line.text || '';
        if (text.includes('ERROR') || text.includes('"level": "ERROR"')) return 'log-error';
        if (text.includes('WARNING') || text.includes('"level": "WARNING"')) return 'log-warning';
        return '';
    };

    return (
        <div>
            <h1 className="page-header">📋 Live Logs (via Loki)</h1>

            <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Service:</label>
                    <select value={service} onChange={(e) => setService(e.target.value)}>
                        <option value="gateway">Gateway</option>
                        <option value="neural_engine">Neural Engine</option>
                    </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Level:</label>
                    <select value={level} onChange={(e) => setLevel(e.target.value)}>
                        <option value="">All</option>
                        <option value="INFO">INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                    </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span
                        style={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            background: statusColors[status],
                        }}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {status === 'connected' ? `Live from ${source}` : status === 'connecting' ? 'Connecting...' : 'Disconnected'}
                    </span>
                </div>

                <button onClick={() => setLines([])} style={{ marginLeft: 'auto' }}>
                    Clear
                </button>
            </div>

            <pre className="logs-console" ref={logsRef}>
                {lines.map((line, idx) => (
                    <div key={idx} className={getLineClass(line)}>
                        {line.text}
                    </div>
                ))}
            </pre>

            <style>{`
        .log-error { color: var(--accent-error); }
        .log-warning { color: var(--accent-warning); }
        .log-info { color: var(--accent-primary); opacity: 0.8; }
      `}</style>
        </div>
    );
}
