import React, { useState } from 'react';
import { Download, ChevronLeft, ChevronRight, FileText } from 'lucide-react';
import { formatNumber, formatDate, exportForecastToCsv } from '../../utils/formatters';

export default function ForecastTable({ forecastRows = [], filename = 'forecast_export.csv', metadata = {} }) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const totalPages = Math.ceil(forecastRows.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const currentRows = forecastRows.slice(startIndex, startIndex + pageSize);

  const handleExport = () => {
    exportForecastToCsv(forecastRows, filename, metadata);
  };

  if (!forecastRows || forecastRows.length === 0) {
    return (
      <div className="text-center py-6 text-slate-500 text-xs">
        No forecast tabular points available.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Table Action Bar */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Showing <strong>{forecastRows.length}</strong> projected future periods
        </span>

        <button
          onClick={handleExport}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/80 text-xs transition-colors"
          title="Download forecast results as CSV"
        >
          <Download className="w-3.5 h-3.5 text-blue-400" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="p-3">Period / Date</th>
              <th className="p-3 text-right">Predicted Demand</th>
              <th className="p-3 text-right">Lower Bound (95%)</th>
              <th className="p-3 text-right">Upper Bound (95%)</th>
              <th className="p-3 text-right">Uncertainty Spread</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850 font-mono text-xs">
            {currentRows.map((row, idx) => {
              const pred = row.predicted_demand ?? row.forecast;
              const lower = row.lower_bound ?? pred;
              const upper = row.upper_bound ?? pred;
              const spread = upper - lower;

              return (
                <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-3 text-slate-200 font-sans font-medium">
                    {formatDate(row.date)}
                  </td>
                  <td className="p-3 text-right font-bold text-blue-400">
                    {formatNumber(pred)}
                  </td>
                  <td className="p-3 text-right text-slate-400">
                    {formatNumber(lower)}
                  </td>
                  <td className="p-3 text-right text-slate-400">
                    {formatNumber(upper)}
                  </td>
                  <td className="p-3 text-right text-slate-500">
                    ±{formatNumber(spread / 2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
              aria-label="Previous page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300"
              aria-label="Next page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
