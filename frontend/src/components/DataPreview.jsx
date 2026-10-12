import React, { useState } from 'react';
import { Table, ChevronLeft, ChevronRight, FileSpreadsheet } from 'lucide-react';
import { formatNumber, formatInteger } from '../utils/formatters';

/**
 * DataPreview displays a tabular preview of uploaded or normalized dataset rows.
 */
export default function DataPreview({
  previewRows = [],
  columns = [],
  rowCount = null,
  filename = '',
  className = '',
  pageSize = 5,
}) {
  const [currentPage, setCurrentPage] = useState(1);

  if (!previewRows || previewRows.length === 0) {
    return (
      <div className={`p-4 rounded-xl border border-[#262626] bg-[#161616] text-center text-xs text-neutral-500 ${className}`}>
        No data preview available.
      </div>
    );
  }

  // Derive columns if not explicitly passed
  const displayColumns = columns.length > 0 ? columns : Object.keys(previewRows[0] || {});
  const totalPages = Math.ceil(previewRows.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const currentRows = previewRows.slice(startIndex, startIndex + pageSize);

  return (
    <div className={`rounded-xl border border-[#262626] bg-[#141414] overflow-hidden ${className}`}>
      {/* Header bar */}
      <div className="px-3.5 py-2.5 border-b border-[#222222] bg-[#181818] flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-neutral-300">
          <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
          <span className="font-medium text-neutral-200">
            {filename || 'Data Preview'}
          </span>
          {rowCount !== null && (
            <span className="text-[11px] text-neutral-500">
              ({formatInteger(rowCount)} total rows)
            </span>
          )}
        </div>

        {/* Pagination controls if more than pageSize rows */}
        {totalPages > 1 && (
          <div className="flex items-center space-x-1.5 text-xs text-neutral-400">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-[#262626] disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px]">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-[#262626] disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Table content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-[#181818] border-b border-[#222222] text-neutral-400 font-medium text-[11px]">
              {displayColumns.map((col, idx) => (
                <th key={idx} className="p-2.5 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f1f1f] font-mono text-[11px] text-neutral-300">
            {currentRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-[#1a1a1a] transition-colors">
                {displayColumns.map((col, cIdx) => {
                  const val = row[col];
                  return (
                    <td key={cIdx} className="p-2.5 whitespace-nowrap">
                      {val === null || val === undefined ? (
                        <span className="text-neutral-600">—</span>
                      ) : typeof val === 'number' ? (
                        formatNumber(val)
                      ) : (
                        String(val)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
