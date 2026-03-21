import { formatMoney, MARKET_TAX } from '../utils/calculations';

export default function ListingsTable({ listings }) {
  if (!listings || listings.length === 0) return null;

  const sorted = [...listings].sort((a, b) => a.cost - b.cost);
  const lowestPrice = sorted[0]?.cost;
  const secondPrice = sorted.find(l => l.cost > lowestPrice)?.cost;

  // Show max 30 rows to keep UI clean
  const display = sorted.slice(0, 30);

  return (
    <div className="card animate-slide-up overflow-hidden">
      <div className="p-4 border-b border-torn-border flex items-center justify-between">
        <p className="section-title">Market Listings</p>
        <span className="badge-blue badge">{sorted.length} listings</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-torn-border">
              <th className="text-left text-text-secondary text-xs uppercase tracking-widest font-semibold px-4 py-2.5">
                #
              </th>
              <th className="text-right text-text-secondary text-xs uppercase tracking-widest font-semibold px-4 py-2.5">
                Price
              </th>
              <th className="text-right text-text-secondary text-xs uppercase tracking-widest font-semibold px-4 py-2.5">
                Qty
              </th>
              <th className="text-right text-text-secondary text-xs uppercase tracking-widest font-semibold px-4 py-2.5">
                Net Sell
              </th>
              <th className="text-right text-text-secondary text-xs uppercase tracking-widest font-semibold px-4 py-2.5">
                vs Lowest
              </th>
              <th className="px-4 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {display.map((listing, idx) => {
              const isLowest = listing.cost === lowestPrice;
              const isSecond = listing.cost === secondPrice;
              const netSell = Math.floor(listing.cost * (1 - MARKET_TAX));
              const diffFromLowest = listing.cost - lowestPrice;

              return (
                <tr
                  key={`${listing.id}-${idx}`}
                  className={`border-b border-torn-border/50 transition-colors hover:bg-torn-surface/60 ${
                    isLowest ? 'bg-neon-green/5' : ''
                  }`}
                >
                  <td className="px-4 py-2.5 text-text-secondary text-xs">{idx + 1}</td>
                  <td className="px-4 py-2.5 text-right font-mono font-semibold">
                    <span className={isLowest ? 'neon-text-green' : isSecond ? 'neon-text-gold' : 'text-text-primary'}>
                      {formatMoney(listing.cost)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right text-text-secondary">
                    {listing.quantity.toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 text-right text-text-secondary text-xs">
                    {formatMoney(netSell)}
                  </td>
                  <td className="px-4 py-2.5 text-right text-xs">
                    {diffFromLowest === 0 ? (
                      <span className="badge-green badge">lowest</span>
                    ) : (
                      <span className="text-text-secondary">+{formatMoney(diffFromLowest)}</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    {isLowest && (
                      <span className="badge-green badge">BUY</span>
                    )}
                    {isSecond && (
                      <span className="badge-gold badge">FLIP↑</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sorted.length > 30 && (
          <p className="text-text-secondary text-xs text-center py-3 border-t border-torn-border">
            Showing top 30 of {sorted.length} listings
          </p>
        )}
      </div>
    </div>
  );
}
