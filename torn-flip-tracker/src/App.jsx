import { useState, useCallback } from 'react';
import { useApiKey } from './hooks/useApiKey';
import { useWatchlist } from './hooks/useWatchlist';
import { useMarketData } from './hooks/useMarketData';
import Header from './components/Header';
import ApiKeyInput from './components/ApiKeyInput';
import ItemSearch from './components/ItemSearch';
import FlipSummary from './components/FlipSummary';
import ListingsTable from './components/ListingsTable';
import ProfitEstimator from './components/ProfitEstimator';
import Watchlist from './components/Watchlist';

export default function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [currentItem, setCurrentItem] = useState(null); // { id, name }

  const { apiKey, playerInfo, validating, validationError, validateKey, clearKey, isSet } =
    useApiKey();
  const { watchlist, addItem, removeItem, isWatched } = useWatchlist();
  const { listings, loading, error, lastFetched, fetchListings, clearListings } =
    useMarketData(apiKey);

  const handleSearch = useCallback(
    async (itemId, itemName) => {
      setCurrentItem({ id: itemId, name: itemName });
      await fetchListings(itemId);
    },
    [fetchListings]
  );

  const handleWatchlistSelect = useCallback(
    (itemId, itemName) => {
      setCurrentItem({ id: itemId, name: itemName });
      fetchListings(itemId);
      setActiveTab('search');
    },
    [fetchListings]
  );

  const handleToggleWatch = useCallback(() => {
    if (!currentItem) return;
    if (isWatched(currentItem.id)) {
      removeItem(currentItem.id);
    } else {
      addItem({ id: currentItem.id, name: currentItem.name });
    }
  }, [currentItem, isWatched, addItem, removeItem]);

  return (
    <div className="min-h-screen bg-torn-bg flex flex-col">
      <Header activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-5 flex flex-col gap-4">
        {/* API Key */}
        <ApiKeyInput
          apiKey={apiKey}
          playerInfo={playerInfo}
          validating={validating}
          validationError={validationError}
          onValidate={validateKey}
          onClear={clearKey}
        />

        {!isSet && (
          <div className="card p-6 text-center text-text-secondary text-sm animate-fade-in">
            Connect your Torn API key above to start analyzing the market.
          </div>
        )}

        {isSet && (
          <>
            {activeTab === 'search' && (
              <div className="flex flex-col gap-4 animate-fade-in">
                <ItemSearch
                  onSearch={handleSearch}
                  loading={loading}
                  disabled={!isSet}
                />

                {error && (
                  <div className="card p-4 border-neon-red/40 text-neon-red text-sm">
                    {error}
                  </div>
                )}

                {listings.length > 0 && currentItem && (
                  <>
                    {/* Watchlist toggle */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-text-secondary text-xs">
                        {lastFetched && (
                          <span>
                            Fetched at {new Date(lastFetched).toLocaleTimeString()}
                          </span>
                        )}
                      </div>
                      <button
                        onClick={handleToggleWatch}
                        className={isWatched(currentItem.id) ? 'btn-danger' : 'btn-gold'}
                      >
                        {isWatched(currentItem.id) ? '− Unwatch' : '+ Watch'}
                      </button>
                    </div>

                    <FlipSummary listings={listings} itemName={currentItem.name} />
                    <ProfitEstimator listings={listings} />
                    <ListingsTable listings={listings} />
                  </>
                )}
              </div>
            )}

            {activeTab === 'watchlist' && (
              <div className="flex flex-col gap-4 animate-fade-in">
                <Watchlist
                  watchlist={watchlist}
                  apiKey={apiKey}
                  onRemove={removeItem}
                  onSelectItem={handleWatchlistSelect}
                />
              </div>
            )}
          </>
        )}
      </main>

      <footer className="border-t border-torn-border mt-auto py-4 px-4 text-center text-text-secondary text-xs">
        <p>
          FLIP.TC — Torn City Market Analyzer &nbsp;·&nbsp; Not affiliated with Torn Ltd
          &nbsp;·&nbsp; All data via{' '}
          <a
            href="https://www.torn.com/api.html"
            target="_blank"
            rel="noopener noreferrer"
            className="text-neon-blue hover:underline"
          >
            api.torn.com
          </a>
        </p>
      </footer>
    </div>
  );
}
