export const MARKET_TAX = 0.05;

/**
 * Given an array of listings sorted by cost ascending,
 * compute flip analysis.
 */
export function analyzeFlip(listings) {
  if (!listings || listings.length === 0) return null;

  // Deduplicate and sort by cost ascending
  const sorted = [...listings].sort((a, b) => a.cost - b.cost);

  const lowestPrice = sorted[0].cost;
  const lowestQty = sorted[0].quantity;

  // Find the second distinct price level
  const secondEntry = sorted.find(l => l.cost > lowestPrice);
  const secondPrice = secondEntry ? secondEntry.cost : null;

  const thirdEntry = secondPrice
    ? sorted.find(l => l.cost > secondPrice)
    : null;
  const thirdPrice = thirdEntry ? thirdEntry.cost : null;

  // Number of sellers at the lowest price
  const sellersAtLowest = sorted.filter(l => l.cost === lowestPrice).length;

  // Best flip target: buy at lowest, sell just under second price
  // (undercut second price by 1 so we become cheapest, minus tax)
  const targetBuyPrice = lowestPrice;

  // Net sell price after 5% market tax
  const netSellFromSecond = secondPrice
    ? Math.floor(secondPrice * (1 - MARKET_TAX))
    : null;

  const profitPerUnit = netSellFromSecond
    ? netSellFromSecond - targetBuyPrice
    : null;

  const marginPct = profitPerUnit && targetBuyPrice > 0
    ? (profitPerUnit / targetBuyPrice) * 100
    : null;

  return {
    lowestPrice,
    lowestQty,
    secondPrice,
    thirdPrice,
    sellersAtLowest,
    netSellFromSecond,
    profitPerUnit,
    marginPct,
    totalListings: sorted.length,
    totalQuantity: sorted.reduce((sum, l) => sum + l.quantity, 0),
  };
}

export function calcProfit(buyPrice, sellPrice, quantity) {
  const gross = (sellPrice - buyPrice) * quantity;
  const tax = sellPrice * MARKET_TAX * quantity;
  const net = gross - tax;
  const totalCost = buyPrice * quantity;
  const roi = totalCost > 0 ? (net / totalCost) * 100 : 0;
  return { gross, tax, net, totalCost, roi };
}

export function formatMoney(n) {
  if (n === null || n === undefined) return '—';
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toLocaleString()}`;
}

export function formatMoneyFull(n) {
  if (n === null || n === undefined) return '—';
  const sign = n < 0 ? '-' : '';
  return `${sign}$${Math.abs(n).toLocaleString()}`;
}
