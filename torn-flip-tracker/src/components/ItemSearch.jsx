import { useState } from 'react';

// A small curated list of popular flippable items.
// Users can also type any numeric item ID directly.
const POPULAR_ITEMS = [
  { id: 206, name: 'Xanax' },
  { id: 367, name: 'Eraser' },
  { id: 370, name: 'Notebook' },
  { id: 4, name: 'Empty Can' },
  { id: 618, name: 'Vial of Heroin' },
  { id: 180, name: 'Bottle of Beer' },
  { id: 267, name: 'Beer Can' },
  { id: 185, name: 'Pint of Blood' },
  { id: 529, name: 'Bottle of Vicodin' },
];

export default function ItemSearch({ onSearch, loading, disabled }) {
  const [query, setQuery] = useState('');
  const [itemId, setItemId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const id = parseInt(itemId || query, 10);
    if (isNaN(id)) return;
    onSearch(id, query || `Item #${id}`);
  };

  const handlePopular = (item) => {
    setItemId(String(item.id));
    setQuery(item.name);
    onSearch(item.id, item.name);
  };

  return (
    <div className="card p-4 animate-fade-in">
      <p className="section-title mb-3">Item Search</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="number"
          value={itemId}
          onChange={e => { setItemId(e.target.value); setQuery(''); }}
          placeholder="Item ID (e.g. 206)"
          className="input-field sm:w-40"
          min="1"
        />
        <button
          type="submit"
          disabled={!itemId || loading || disabled}
          className="btn-primary whitespace-nowrap"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <LoadSpinner size={12} /> Fetching…
            </span>
          ) : 'Search Market'}
        </button>
      </form>

      <div className="mt-3">
        <p className="text-text-secondary text-xs mb-2">Quick picks:</p>
        <div className="flex flex-wrap gap-1.5">
          {POPULAR_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => handlePopular(item)}
              disabled={disabled || loading}
              className="px-2.5 py-1 bg-torn-surface border border-torn-border rounded text-xs
                         text-text-secondary hover:border-neon-green/40 hover:text-neon-green
                         transition-all duration-150 disabled:opacity-40"
            >
              {item.name} <span className="text-torn-muted">#{item.id}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function LoadSpinner({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" className="animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" strokeOpacity=".25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  );
}
