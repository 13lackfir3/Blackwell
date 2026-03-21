import { useState } from 'react';

export default function ApiKeyInput({ apiKey, playerInfo, validating, validationError, onValidate, onClear }) {
  const [inputVal, setInputVal] = useState(apiKey || '');
  const [show, setShow] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onValidate(inputVal.trim());
  };

  if (apiKey && playerInfo) {
    return (
      <div className="card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-fade-in">
        <div className="flex items-center gap-3">
          <span className="glow-dot bg-neon-green text-neon-green" />
          <div>
            <p className="text-xs text-text-secondary uppercase tracking-widest">Connected as</p>
            <p className="neon-text-green font-semibold text-base">{playerInfo.name}</p>
          </div>
          <div className="hidden sm:block border-l border-torn-border pl-3">
            <p className="text-xs text-text-secondary uppercase tracking-widest">Level</p>
            <p className="text-text-primary font-semibold">{playerInfo.level}</p>
          </div>
          <div className="hidden sm:block border-l border-torn-border pl-3">
            <p className="text-xs text-text-secondary uppercase tracking-widest">API Key</p>
            <p className="text-text-secondary font-mono text-sm">{apiKey.slice(0, 4)}…{apiKey.slice(-4)}</p>
          </div>
        </div>
        <button onClick={onClear} className="btn-danger">
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <div className="card p-4 animate-fade-in">
      <p className="section-title mb-3">Torn API Key</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <input
            type={show ? 'text' : 'password'}
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            placeholder="Paste your Torn API key…"
            className="input-field pr-16"
          />
          <button
            type="button"
            onClick={() => setShow(s => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary text-xs transition-colors"
          >
            {show ? 'HIDE' : 'SHOW'}
          </button>
        </div>
        <button
          type="submit"
          disabled={!inputVal.trim() || validating}
          className="btn-primary whitespace-nowrap"
        >
          {validating ? (
            <span className="flex items-center gap-2">
              <LoadSpinner size={12} /> Validating…
            </span>
          ) : 'Connect'}
        </button>
      </form>
      {validationError && (
        <p className="text-neon-red text-xs mt-2 animate-fade-in">{validationError}</p>
      )}
      <p className="text-text-secondary text-xs mt-2">
        Your key is stored locally in your browser and never sent anywhere except directly to api.torn.com.
        Create a read-only key at{' '}
        <a
          href="https://www.torn.com/preferences.php#tab=api"
          target="_blank"
          rel="noopener noreferrer"
          className="text-neon-blue hover:underline"
        >
          torn.com/preferences
        </a>.
      </p>
    </div>
  );
}

function LoadSpinner({ size = 16 }) {
  return (
    <svg
      width={size} height={size}
      viewBox="0 0 24 24"
      className="animate-spin"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="10" strokeOpacity=".25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  );
}
