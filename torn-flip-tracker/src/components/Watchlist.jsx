import { useEffect, useRef, useState, useCallback } from 'react';
import { analyzeFlip, formatMoney } from '../utils/calculations';

const REFRESH_INTERVAL = 60_000; // 60s

function WatchlistItem({ item, apiKey, onRemove, onSelectItem }) {
  const [data, setData] = useState(item.listings || null);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(item.lastUpdated || null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL / 1000);
  const timerRef = useRef(null);
  const countdownRef = useRef(null);

  const fetchData = useCallback(async () => {
    if (!apiKey || !item.id) return;
    setLoading(true);
    try {
      const res = await fetch(
        `https://api.torn.com/market/${item.id}?selections=itemmarket&key=${apiKey}`
      );
      const json = await res.json();
      if (!json.error) {
        const normalized = (json.itemmarket || []).map(l => ({
          id: l.ID, cost: l.cost, quantity: l.quantity,
        }));
        setData(normalized);
        setLastUpdated(Date.now());
        setCountdown(REFRESH_INTERVAL / 1000);
      }
    } catch {
      // silently ignore network errors in watchlist refresh
    } finally {
      setLoading(false);
    }
  }, [apiKey, item.id]);

  // Auto-refresh every 60s
  useEffect(() => {
    fetchData();
    timerRef.current = setInterval(fetchData, REFRESH_INTERVAL);
    countdownRef.current = setInterval(() => {
      setCountdown(c => (c <= 1 ? REFRESH_INTERVAL / 1000 : c - 1));
    }, 1000);

    return () => {
      clearInterval(timerRef.current);
      clearInterval(countdownRef.current);
    };
  }, [fetchData]);

  const analysis = data ? analyzeFlip(data) : null;
  const isGood = analysis?.marginPct !== null && analysis?.marginPct >= 5;
  const isMeh = analysis?.marginPct !== null && analysis?.marginPct >= 1 && analysis?.marginPct < 5;

  return (
    <div className="bg-torn-surface border border-torn-border rounded-lg p-3 hover:border-torn-muted transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => onSelectItem(item.id, item.name)}
              className="text-text-primary font-semibold text-sm hover:text-neon-green transition-colors truncate"
            >
              {item.name}
            </button>
            <span className="text-text-secondary text-xs">#{item.id}</span>
            {analysis && (
              <span className={`badge text-xs ${isGood ? 'badge-green' : isMeh ? 'badge-gold' : 'badge-red'}`}>
                {isGood ? '✓' : isMeh ? '~' : '✗'} {analysis.marginPct?.toFixed(1)}%
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={fetchData}
            disabled={loading}
            title="Refresh now"
            className="text-text-secondary hover:text-neon-green transition-colors text-xs disabled:opacity-40"
          >
            {loading ? <SpinIcon /> : '↻'}
          </button>
          <button onClick={() => onRemove(item.id)} className="btn-danger py-0.5 px-2">×</button>
        </div>
      </div>

      {analysis ? (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <p className="text-text-secondary">Buy</p>
            <p className="neon-text-green font-semibold">{formatMoney(analysis.lowestPrice)}</p>
          </div>
          <div>
            <p className="text-text-secondary">Sell@</p>
            <p className="text-neon-gold font-semibold">{analysis.secondPrice ? formatMoney(analysis.secondPrice) : '—'}</p>
          </div>
          <div>
            <p className="text-text-secondary">Profit/u</p>
            <p className={`font-semibold ${analysis.profitPerUnit > 0 ? 'text-neon-green' : 'text-neon-red'}`}>
              {formatMoney(analysis.profitPerUnit)}
            </p>
          </div>
        </div>
      ) : (
        <div className="text-text-secondary text-xs">Loading…</div>
      )}

      <div className="mt-2 flex items-center justify-between text-xs text-text-secondary">
        <span>
          {lastUpdated
            ? `Updated ${Math.floor((Date.now() - lastUpdated) / 1000)}s ago`
            : 'Never fetched'}
        </span>
        <span className="flex items-center gap-1">
          <span className="glow-dot bg-neon-green/50 text-neon-green animate-pulse-green w-1.5 h-1.5" />
          refresh in {countdown}s
        </span>
      </div>
    </div>
  );
}

export default function Watchlist({ watchlist, apiKey, onRemove, onSelectItem }) {
  if (watchlist.length === 0) {
    return (
      <div className="card p-6 text-center animate-fade-in">
        <p className="section-title mb-2">Watchlist</p>
        <p className="text-text-secondary text-sm">
          No items watched. Search for an item and click <span className="text-neon-gold">+ Watch</span> to track it.
        </p>
      </div>
    );
  }

  return (
    <div className="card p-4 animate-fade-in">
      <div className="flex items-center justify-between mb-3">
        <p className="section-title">Watchlist</p>
        <span className="badge-blue badge">{watchlist.length} item{watchlist.length !== 1 ? 's' : ''}</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {watchlist.map(item => (
          <WatchlistItem
            key={item.id}
            item={item}
            apiKey={apiKey}
            onRemove={onRemove}
            onSelectItem={onSelectItem}
          />
        ))}
      </div>
    </div>
  );
}

function SpinIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" className="animate-spin inline" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" strokeOpacity=".25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  );
}
