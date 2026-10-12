import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Layers,
  Package,
  ShieldAlert,
  Percent,
  Info,
  CheckCircle2,
  Sliders,
  AlertTriangle,
} from 'lucide-react';
import { formatNumber, formatPercentage } from '../../utils/formatters';

export default function BusinessInsightsCard({ analytics, onRecalculateInventory }) {
  const [leadTimeInput, setLeadTimeInput] = useState(
    analytics?.inventory_insights?.lead_time_periods || 7
  );
  const [serviceLevelInput, setServiceLevelInput] = useState(
    analytics?.inventory_insights?.service_level || 0.95
  );

  const trend = analytics?.trend || {};
  const rankings = analytics?.product_rankings || [];
  const seasonality = analytics?.seasonality || {};
  const inventory = analytics?.inventory_insights || {};
  const correlations = analytics?.correlations || {};

  const handleUpdateInventory = (e) => {
    e.preventDefault();
    if (onRecalculateInventory) {
      onRecalculateInventory({
        lead_time_days: Number(leadTimeInput) || 7,
        service_level: Number(serviceLevelInput) || 0.95,
      });
    }
  };

  return (
    <div className="rounded-2xl border border-[#262626] bg-[#181818] p-5 space-y-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#262626] pb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-[#193228] text-emerald-400 border border-[#234b3c]">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              Business & Operational Insights
            </h3>
            <p className="text-xs text-neutral-400">
              Empirical historical trends, calendar cycles, and inventory estimates directly from validated backend results.
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c]">
          Backend Validated
        </span>
      </div>

      {/* 1. Sales Trend Section */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
          Historical Sales Trend & Volume
        </h4>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Trend Direction</span>
            <div className="flex items-center space-x-1.5 mt-0.5">
              {trend.direction === 'upward' && <TrendingUp className="w-4 h-4 text-emerald-400" />}
              {trend.direction === 'downward' && <TrendingDown className="w-4 h-4 text-rose-400" />}
              {trend.direction === 'stable' && <Minus className="w-4 h-4 text-blue-400" />}
              <span className="text-sm font-bold capitalize text-slate-200">
                {trend.direction || 'Stable'}
              </span>
            </div>
            <span className="text-[10px] text-slate-500 block">
              slope: {trend.slope > 0 ? `+${trend.slope}` : trend.slope}/period
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Half-Split Growth</span>
            <span className={`text-base font-bold font-mono ${
              trend.growth_rate_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {trend.growth_rate_pct >= 0 ? `+${trend.growth_rate_pct}%` : `${trend.growth_rate_pct}%`}
            </span>
            <span className="text-[10px] text-slate-500 block">first vs second half</span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Historical Run-Rate</span>
            <span className="text-base font-bold font-mono text-slate-200">
              {formatNumber(trend.mean_demand, 1)}
            </span>
            <span className="text-[10px] text-slate-500 block">
              units/period (std: ±{formatNumber(trend.std_demand, 1)})
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-semibold text-slate-400 block">Demand Volatility (CV)</span>
            <span className="text-base font-bold font-mono text-amber-400">
              {trend.coefficient_of_variation ?? '—'}
            </span>
            <span className="text-[10px] text-slate-500 block">
              {trend.coefficient_of_variation > 0.5 ? 'high volatility' : 'moderate predictability'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Product Rankings (Pareto) */}
      {rankings && rankings.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            Product Contribution & Rankings (Pareto Analysis)
          </h4>

          <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                  <th className="p-2.5">Rank</th>
                  <th className="p-2.5">Product SKU</th>
                  <th className="p-2.5 text-right">Total Volume</th>
                  <th className="p-2.5 text-right">Average / Day</th>
                  <th className="p-2.5 text-right">Volume Share</th>
                  <th className="p-2.5 text-right">Cumulative</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 font-mono text-xs">
                {rankings.slice(0, 5).map((prod) => (
                  <tr key={prod.product_id} className="hover:bg-slate-900/40">
                    <td className="p-2.5 text-slate-400 font-sans">{prod.rank}</td>
                    <td className="p-2.5 font-sans font-medium text-slate-200">{prod.product_id}</td>
                    <td className="p-2.5 text-right text-blue-400 font-bold">{formatNumber(prod.total_volume, 0)}</td>
                    <td className="p-2.5 text-right text-slate-300">{formatNumber(prod.avg_demand, 1)}</td>
                    <td className="p-2.5 text-right text-slate-300">{formatPercentage(prod.volume_share_pct)}</td>
                    <td className="p-2.5 text-right text-slate-400">{formatPercentage(prod.cumulative_share_pct)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Seasonality Patterns */}
      {seasonality.has_seasonality && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-pink-400" />
              Day-of-Week Seasonality Patterns
            </h4>
            {seasonality.weekend_lift_pct !== undefined && (
              <span className="text-[11px] text-slate-400">
                Weekend Lift: <strong className="text-emerald-400">+{seasonality.weekend_lift_pct}%</strong>
              </span>
            )}
          </div>

          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            {seasonality.pattern_summary}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-7 gap-2">
            {Object.entries(seasonality.day_of_week_indices || {}).map(([day, stats]) => (
              <div
                key={day}
                className={`p-2 rounded-lg border text-center ${
                  day === seasonality.peak_day
                    ? 'bg-blue-950/40 border-blue-800 text-blue-300'
                    : day === seasonality.trough_day
                    ? 'bg-slate-950 border-slate-800 text-slate-400'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-300'
                }`}
              >
                <span className="text-[10px] font-semibold block uppercase">{day.slice(0, 3)}</span>
                <span className="text-xs font-mono font-bold block mt-0.5">
                  {stats.index}x
                </span>
                <span className={`text-[10px] font-mono ${
                  stats.deviation_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {stats.deviation_pct >= 0 ? `+${stats.deviation_pct}%` : `${stats.deviation_pct}%`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Grounded Inventory Sizing (Safety Stock & ROP) */}
      <div className="space-y-3 pt-2 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Package className="w-3.5 h-3.5 text-amber-400" />
            Inventory Planning Estimates (Safety Stock & Reorder Point)
          </h4>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/40">
            Planning Estimate Only
          </span>
        </div>

        {inventory?.is_available ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Lead Time Parameter</span>
                <span className="text-base font-bold font-mono text-slate-200">
                  {inventory.lead_time_periods} Periods
                </span>
                <span className="text-[10px] text-slate-500 block">deterministic lead time</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Lead Time Demand</span>
                <span className="text-base font-bold font-mono text-slate-200">
                  {formatNumber(inventory.expected_lead_time_demand, 0)} Units
                </span>
                <span className="text-[10px] text-slate-500 block">expected consumption</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">
                  Safety Stock ({inventory.service_level * 100}% SL)
                </span>
                <span className="text-base font-bold font-mono text-emerald-400">
                  {formatNumber(inventory.safety_stock_estimate, 0)} Units
                </span>
                <span className="text-[10px] text-slate-500 block">buffer for demand variance</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] uppercase font-semibold text-slate-400 block">Reorder Point (ROP)</span>
                <span className="text-base font-bold font-mono text-blue-400">
                  {formatNumber(inventory.reorder_point_estimate, 0)} Units
                </span>
                <span className="text-[10px] text-slate-500 block">trigger replenishment order</span>
              </div>
            </div>

            {/* Parameter Adjustment Form */}
            <form onSubmit={handleUpdateInventory} className="flex flex-wrap items-center gap-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
              <span className="text-slate-400 font-medium">Re-simulate parameters:</span>
              <div className="flex items-center space-x-1">
                <label className="text-slate-500 text-[11px]">Lead Time (days):</label>
                <input
                  type="number"
                  min="1"
                  max="180"
                  value={leadTimeInput}
                  onChange={(e) => setLeadTimeInput(e.target.value)}
                  className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-xs"
                />
              </div>

              <div className="flex items-center space-x-1">
                <label className="text-slate-500 text-[11px]">Service Level:</label>
                <select
                  value={serviceLevelInput}
                  onChange={(e) => setServiceLevelInput(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
                >
                  <option value="0.90">90% (Z=1.28)</option>
                  <option value="0.95">95% (Z=1.65)</option>
                  <option value="0.98">98% (Z=2.05)</option>
                  <option value="0.99">99% (Z=2.33)</option>
                </select>
              </div>

              <button
                type="submit"
                className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium ml-auto transition-colors"
              >
                Update Estimates
              </button>
            </form>

            {/* Explicit Assumptions Disclaimer */}
            <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <span>{inventory.assumptions}</span>
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-4 space-y-3 text-xs">
            <p className="text-slate-300">
              {inventory?.reason || 'Inventory parameters not specified.'}
            </p>
            <form onSubmit={handleUpdateInventory} className="flex flex-wrap items-center gap-2">
              <div className="flex items-center space-x-1.5">
                <label className="text-slate-400">Supplier Lead Time (days):</label>
                <input
                  type="number"
                  min="1"
                  max="180"
                  value={leadTimeInput}
                  onChange={(e) => setLeadTimeInput(e.target.value)}
                  placeholder="e.g. 7"
                  className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono text-xs"
                />
              </div>

              <button
                type="submit"
                className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
              >
                Calculate Safety Stock & ROP
              </button>
            </form>
          </div>
        )}
      </div>

      {/* 5. Empirical Correlations & Causality Warning */}
      {correlations && Object.keys(correlations).length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Percent className="w-3.5 h-3.5 text-purple-400" />
            Empirical Correlations & Disclaimers
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {correlations.promotion && (
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Promotions vs Demand</span>
                  <span className="font-mono text-purple-400 font-bold">
                    r = {correlations.promotion.correlation}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Promotional lift: +{correlations.promotion.promotional_lift_pct}% vs baseline run-rate.
                </p>
                <p className="text-[10px] text-amber-400/90 italic pt-1 border-t border-slate-850">
                  {correlations.promotion.disclaimer}
                </p>
              </div>
            )}

            {correlations.price && (
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Price vs Demand</span>
                  <span className="font-mono text-purple-400 font-bold">
                    r = {correlations.price.correlation}
                  </span>
                </div>
                <p className="text-[10px] text-amber-400/90 italic pt-1 border-t border-slate-850">
                  {correlations.price.disclaimer}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
