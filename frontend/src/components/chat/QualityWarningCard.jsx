import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function QualityWarningCard({ dataQuality, ambiguityWarnings = [] }) {
  const hasGaps = dataQuality?.has_date_gaps;
  const hasDuplicates = dataQuality?.has_duplicate_dates;
  const hasNegatives = dataQuality?.has_negative_demand;
  const warningsList = dataQuality?.warnings || [];

  return (
    <div className="rounded-xl border border-amber-800/40 bg-amber-950/20 p-4 space-y-3">
      <div className="flex items-center space-x-2 text-amber-400">
        <ShieldAlert className="w-5 h-5 flex-shrink-0" />
        <h4 className="text-xs font-bold uppercase tracking-wider">
          Data Quality & Disambiguation Report
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
        <div className={`p-2.5 rounded-lg border ${
          hasGaps ? 'bg-amber-950/40 border-amber-800/50 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          <span className="text-[10px] uppercase font-semibold block">Missing Time Gaps</span>
          <span className="font-bold">
            {hasGaps ? `${dataQuality.gap_count} gaps detected` : 'No gaps'}
          </span>
        </div>

        <div className={`p-2.5 rounded-lg border ${
          hasDuplicates ? 'bg-amber-950/40 border-amber-800/50 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          <span className="text-[10px] uppercase font-semibold block">Duplicate Dates</span>
          <span className="font-bold">
            {hasDuplicates ? `${dataQuality.duplicate_count} duplicates` : 'No duplicates'}
          </span>
        </div>

        <div className={`p-2.5 rounded-lg border ${
          hasNegatives ? 'bg-rose-950/40 border-rose-800/50 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          <span className="text-[10px] uppercase font-semibold block">Negative Demand</span>
          <span className="font-bold">
            {hasNegatives ? `${dataQuality.negative_demand_count} negative rows` : 'All non-negative'}
          </span>
        </div>
      </div>

      {ambiguityWarnings.length > 0 && (
        <div className="text-xs text-amber-200/90 space-y-1 pt-1 border-t border-amber-800/30">
          <span className="font-semibold block text-amber-400">Potential Ambiguities:</span>
          <ul className="list-disc list-inside space-y-0.5">
            {ambiguityWarnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {warningsList.length > 0 && (
        <div className="text-xs text-slate-400 space-y-1">
          <ul className="list-disc list-inside space-y-0.5">
            {warningsList.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
