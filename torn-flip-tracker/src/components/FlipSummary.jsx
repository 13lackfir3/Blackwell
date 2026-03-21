import { analyzeFlip, formatMoney, formatMoneyFull } from '../utils/calculations';

export default function FlipSummary({ listings, itemName }) {
  const analysis = analyzeFlip(listings);
  if (!analysis) return null;

  const {
    lowestPrice,
    secondPrice,
    thirdPrice,
    sellersAtLowest,
    netSellFromSecond,
    profitPerUnit,
    marginPct,
    totalListings,
    totalQuantity,
  } = analysis;

  const isGoodFlip = marginPct !== null && marginPct >= 5;
  const isMehFlip = marginPct !== null && marginPct >= 1 && marginPct < 5;

  return (
    <div className="card p-4 animate-slide-up">
      <div className="flex items-start justify-between flex-wrap gap-2 mb-4">
        <div>
          <p className="section-title">Flip Analysis</p>
          {itemName && <p className="text-text-primary font-semibold mt-0.5">{itemName}</p>}
        </div>
        {marginPct !== null && (
          <span className={`badge text-sm px-3 py-1 ${
            isGoodFlip ? 'badge-green' : isMehFlip ? 'badge-gold' : 'badge-red'
          }`}>
            {isGoodFlip ? '✓ Profitable' : isMehFlip ? '~ Marginal' : '✗ Loss'}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatBox
          label="Buy Price (lowest)"
          value={formatMoney(lowestPrice)}
          valueClass="neon-text-green"
          sub={`${sellersAtLowest} seller${sellersAtLowest !== 1 ? 's' : ''} at this price`}
        />
        <StatBox
          label="2nd Price Level"
          value={secondPrice ? formatMoney(secondPrice) : '—'}
          valueClass="text-text-primary"
          sub={secondPrice ? `Gap: ${formatMoney(secondPrice - lowestPrice)}` : 'No next level'}
        />
        <StatBox
          label="3rd Price Level"
          value={thirdPrice ? formatMoney(thirdPrice) : '—'}
          valueClass="text-text-secondary"
          sub="Reference"
        />
        <StatBox
          label="Net Sell Price"
          value={netSellFromSecond ? formatMoney(netSellFromSecond) : '—'}
          valueClass="text-neon-blue"
          sub="After 5% market tax"
        />
        <StatBox
          label="Profit / Unit"
          value={profitPerUnit !== null ? formatMoneyFull(profitPerUnit) : '—'}
          valueClass={profitPerUnit > 0 ? 'neon-text-green' : 'text-neon-red'}
          sub="Net vs buy cost"
        />
        <StatBox
          label="Margin"
          value={marginPct !== null ? `${marginPct.toFixed(1)}%` : '—'}
          valueClass={isGoodFlip ? 'neon-text-green' : isMehFlip ? 'neon-text-gold' : 'text-neon-red'}
          sub="After tax"
        />
      </div>

      <div className="divider mt-4 pt-3 flex gap-4 text-xs text-text-secondary flex-wrap">
        <span>Total listings: <span className="text-text-primary">{totalListings}</span></span>
        <span>Total qty: <span className="text-text-primary">{totalQuantity.toLocaleString()}</span></span>
        {profitPerUnit !== null && profitPerUnit > 0 && (
          <span className="ml-auto text-neon-green text-xs">
            Buy low @ {formatMoney(lowestPrice)}, sell undercutting 2nd price
          </span>
        )}
      </div>
    </div>
  );
}

function StatBox({ label, value, valueClass, sub }) {
  return (
    <div className="bg-torn-surface border border-torn-border rounded p-3">
      <p className="text-text-secondary text-xs uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-semibold text-base ${valueClass}`}>{value}</p>
      {sub && <p className="text-text-secondary text-xs mt-0.5">{sub}</p>}
    </div>
  );
}
