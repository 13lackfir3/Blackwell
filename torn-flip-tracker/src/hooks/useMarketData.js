import { useState, useCallback, useRef } from 'react';

const MARKET_URL = (itemId, key) =>
  `https://api.torn.com/market/${itemId}?selections=itemmarket&key=${key}`;

export function useMarketData(apiKey) {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastFetched, setLastFetched] = useState(null);
  const abortRef = useRef(null);

  const fetchListings = useCallback(async (itemId) => {
    if (!apiKey || !itemId) return null;

    // Abort any in-flight request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError('');

    try {
      const res = await fetch(MARKET_URL(itemId, apiKey), {
        signal: abortRef.current.signal,
      });
      const data = await res.json();

      if (data.error) {
        setError(`API error: ${data.error.error}`);
        setLoading(false);
        return null;
      }

      // The API returns { itemmarket: [ { ID, cost, quantity } ] }
      const raw = data.itemmarket || [];
      const normalized = raw.map(l => ({
        id: l.ID,
        cost: l.cost,
        quantity: l.quantity,
      }));

      setListings(normalized);
      setLastFetched(Date.now());
      setLoading(false);
      return normalized;
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError('Network error — check your connection.');
        setLoading(false);
      }
      return null;
    }
  }, [apiKey]);

  const clearListings = useCallback(() => {
    setListings([]);
    setError('');
    setLastFetched(null);
  }, []);

  return { listings, loading, error, lastFetched, fetchListings, clearListings };
}
