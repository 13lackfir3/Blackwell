export default function Header({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'search', label: 'Market Search' },
    { id: 'watchlist', label: 'Watchlist' },
  ];

  return (
    <header className="bg-torn-surface border-b border-torn-border sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14 gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-neon-green text-lg font-bold font-mono tracking-tight text-shadow-green">
              ◈ FLIP.TC
            </span>
            <span className="hidden sm:block text-text-secondary text-xs border-l border-torn-border pl-3">
              Torn City Market Analyzer
            </span>
          </div>

          {/* Tabs */}
          <nav className="flex items-center gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`px-3 py-1.5 rounded text-sm font-mono transition-all duration-150 ${
                  activeTab === tab.id
                    ? 'bg-neon-green/10 text-neon-green border border-neon-green/40'
                    : 'text-text-secondary hover:text-text-primary hover:bg-torn-card border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
