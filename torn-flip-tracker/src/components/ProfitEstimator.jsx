import { useState } from 'react';
import { analyzeFlip, calcProfit, formatMoney, formatMoneyFull } from '../utils/calculations';

export default function ProfitEstimator({ listings }) {
  const analysis = analyzeFlip(listings);
  const [quantity, setQuantity] = useState(1);
  const [customBuy, setCustomBuy] = useState('');
  const [customSell, setCustomSell] = useState('');

  const buyPrice = customBuy !== '' ? parseInt(customBuy, 10) : analysis?.lowestPrice || 0;
  const sellPrice = customSell !== '' ? parseInt(customSell, 10) : analysis?.secondPrice || 0;

  const isValid = quantity > 0 && buyPrice > 0 && sellPrice > 0;
  const result = isValid ? calcProfit(buyPrice, sellPrice, quantity) : null;

  return (
    <div className="card p-4 animate-slide-up">
      <p className="section-title mb-4">Profit Estimator</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <div>
          <label className="label">Quantity</label>
          <input
            type="number"
            min="1"
            value={quantity}
            onChange={e => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
            className="input-field"
          />
        </div>
        <div>
          <label className="label">
            Buy Price
            {analysis?.lowestPrice && (
              <button
                onClick={() => setCustomBuy('')}
                className="ml-2 text-neon-green text-xs normal-case tracking-normal hover:underline"
              >
                use lowest ({formatMoney(analysis.lowestPrice)})
              </button>
            )}
          </label>
          <input
            type="number"
            min="1"
            value={customBuy !== '' ? customBuy : (analysis?.lowestPrice || '')}
            onChange={e => setCustomBuy(e.target.value)}
            placeholder="e.g. 50000"
            className="input-field"
          />
        </div>
        <div>
          <label className="label">
            Sell Price
            {analysis?.secondPrice && (
              <button
                onClick={() => setCustomSell('')}
                className="ml-2 text-neon-gold text-xs normal-case tracking-normal hover:underline"
              >
                use 2nd ({formatMoney(analysis.secondPrice)})
              </button>
            )}
          </label>
          <input
            type="number"
            min="1"
            value={customSell !== '' ? customSell : (analysis?.secondPrice || '')}
            onChange={e => setCustomSell(e.target.value)}
            placeholder="e.g. 60000"
            className="input-field"
          />
        </div>
      </div>

      {result ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 animate-fade-in">
          <ResultBox
            label="Total Cost"
            value={formatMoneyFull(result.totalCost)}
            sub={`${quantity} × ${formatMoney(buyPrice)}`}
            className="text-text-primary"
          />
          <ResultBox
            label="Gross Revenue"
            value={formatMoneyFull(result.totalCost + result.gross)}
            sub={`${quantity} × ${formatMoney(sellPrice)}`}
            className="text-text-primary"
          />
          <ResultBox
            label="Market Tax (5%)"
            value={`-${formatMoneyFull(result.tax)}`}
            sub="Torn market fee"
            className="text-neon-red"
          />
          <ResultBox
            label="Net Profit"
            value={formatMoneyFull(result.net)}
            sub={`ROI: ${result.roi.toFixed(1)}%`}
            className={result.net > 0 ? 'neon-text-green text-shadow-green' : 'text-neon-red'}
            large
          />
        </div>
      ) : (
        <div className="bg-torn-surface border border-torn-border rounded p-4 text-center text-text-secondary text-sm">
          {!analysis
            ? 'Search for an item to auto-fill prices, or enter custom values above.'
            : 'Enter valid quantities and prices to calculate profit.'}
        </div>
      )}
    </div>
  );
}

function ResultBox({ label, value, sub, className, large }) {
  return (
    <div className="bg-torn-surface border border-torn-border rounded p-3">
      <p className="text-text-secondary text-xs uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-semibold ${large ? 'text-xl' : 'text-base'} ${className}`}>{value}</p>
      {sub && <p className="text-text-secondary text-xs mt-0.5">{sub}</p>}
    </div>
  );
}
