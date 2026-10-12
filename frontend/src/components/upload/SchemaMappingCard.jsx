import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import {
  Check,
  Calendar,
  TrendingUp,
  Tag,
  Store,
  DollarSign,
  Percent,
  Clock,
  AlertTriangle,
  ChevronDown,
  Layers,
} from 'lucide-react';

export default function SchemaMappingCard({ dataset, onConfirmed }) {
  const { confirmMapping } = useChat();

  const columns = dataset?.columns || [];
  const suggested = dataset?.suggested_mapping || {};
  const confidence = dataset?.mapping_confidence || {};
  const ambiguity = dataset?.ambiguity_warnings || [];

  const [dateCol, setDateCol] = useState(suggested.date || '');
  const [demandCol, setDemandCol] = useState(suggested.demand || '');
  const [productIdCol, setProductIdCol] = useState(suggested.product_id || '');
  const [storeIdCol, setStoreIdCol] = useState(suggested.store_id || '');
  const [priceCol, setPriceCol] = useState(suggested.price || '');
  const [promoCol, setPromoCol] = useState(suggested.promotion || '');
  const [frequency, setFrequency] = useState('auto');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!dateCol || !demandCol) return;

    setIsSubmitting(true);
    try {
      await confirmMapping({
        date_column: dateCol,
        demand_column: demandCol,
        product_id_column: productIdCol || null,
        store_id_column: storeIdCol || null,
        price_column: priceCol || null,
        promotion_column: promoCol || null,
        aggregation_frequency: frequency,
      });
      if (onConfirmed) onConfirmed();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border border-[#262626] bg-[#181818] p-5 space-y-5 shadow-sm">
      <div className="flex items-start justify-between border-b border-[#262626] pb-3">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Canonical Schema Mapping
          </h3>
          <p className="text-xs text-neutral-400 mt-0.5">
            Confirm or adjust auto-detected column roles before training forecasting models.
          </p>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c]">
          Required Confirmation
        </span>
      </div>

      {/* Ambiguity Warnings if any */}
      {ambiguity.length > 0 && (
        <div className="rounded-lg bg-amber-950/30 border border-amber-800/40 p-3 space-y-1">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-amber-400">
            <AlertTriangle className="w-4 h-4" />
            <span>Ambiguity Alerts</span>
          </div>
          <ul className="list-disc list-inside text-[11px] text-amber-200/80 space-y-0.5">
            {ambiguity.map((warn, i) => (
              <li key={i}>{warn}</li>
            ))}
          </ul>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Date Column (Required) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-blue-400" />
                Date / Timestamp <span className="text-rose-400">*</span>
              </span>
              {confidence.date && (
                <span className="text-[10px] text-slate-500 capitalize">
                  {confidence.date} confidence
                </span>
              )}
            </label>
            <div className="relative">
              <select
                value={dateCol}
                onChange={(e) => setDateCol(e.target.value)}
                required
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="" disabled>Select Date Column...</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Demand Column (Required) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                Demand / Sales Quantity <span className="text-rose-400">*</span>
              </span>
              {confidence.demand && (
                <span className="text-[10px] text-slate-500 capitalize">
                  {confidence.demand} confidence
                </span>
              )}
            </label>
            <div className="relative">
              <select
                value={demandCol}
                onChange={(e) => setDemandCol(e.target.value)}
                required
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="" disabled>Select Demand Column...</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Product ID (Optional) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-purple-400" />
                Product / Item ID (Optional)
              </span>
            </label>
            <div className="relative">
              <select
                value={productIdCol}
                onChange={(e) => setProductIdCol(e.target.value)}
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="">None (Aggregate Demand)</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Store ID (Optional) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Store className="w-3.5 h-3.5 text-amber-400" />
                Store / Location ID (Optional)
              </span>
            </label>
            <div className="relative">
              <select
                value={storeIdCol}
                onChange={(e) => setStoreIdCol(e.target.value)}
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="">None</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Price (Optional) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                Unit Price (Optional)
              </span>
            </label>
            <div className="relative">
              <select
                value={priceCol}
                onChange={(e) => setPriceCol(e.target.value)}
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="">None</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>

          {/* Promotion / Discount (Optional) */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Percent className="w-3.5 h-3.5 text-pink-400" />
                Promotion Flag (Optional)
              </span>
            </label>
            <div className="relative">
              <select
                value={promoCol}
                onChange={(e) => setPromoCol(e.target.value)}
                className="w-full appearance-none rounded-lg bg-slate-950 border border-slate-700/80 px-3 py-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
              >
                <option value="">None</option>
                {columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Aggregation Frequency Selection */}
        <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>Aggregation Frequency:</span>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
            >
              <option value="auto">Auto-detect from dates</option>
              <option value="D">Daily ('D')</option>
              <option value="W">Weekly ('W')</option>
              <option value="M">Monthly ('M')</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={!dateCol || !demandCol || isSubmitting}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-white hover:bg-neutral-200 disabled:bg-[#262626] text-black disabled:text-neutral-500 text-xs font-semibold transition-colors cursor-pointer"
          >
            <Check className="w-4 h-4 text-black" />
            <span>{isSubmitting ? 'Validating Schema...' : 'Confirm & Normalize Schema'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
