import { useState, useCallback } from 'react';

const STORAGE_KEY = 'torn_flip_watchlist';

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function persist(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function useWatchlist() {
  const [watchlist, setWatchlist] = useState(load);

  const addItem = useCallback((item) => {
    setWatchlist(prev => {
      if (prev.some(i => i.id === item.id)) return prev;
      const next = [...prev, { ...item, addedAt: Date.now() }];
      persist(next);
      return next;
    });
  }, []);

  const removeItem = useCallback((itemId) => {
    setWatchlist(prev => {
      const next = prev.filter(i => i.id !== itemId);
      persist(next);
      return next;
    });
  }, []);

  const updateItemData = useCallback((itemId, data) => {
    setWatchlist(prev => {
      const next = prev.map(i =>
        i.id === itemId ? { ...i, ...data, lastUpdated: Date.now() } : i
      );
      persist(next);
      return next;
    });
  }, []);

  const isWatched = useCallback(
    (itemId) => watchlist.some(i => i.id === itemId),
    [watchlist]
  );

  return { watchlist, addItem, removeItem, updateItemData, isWatched };
}
