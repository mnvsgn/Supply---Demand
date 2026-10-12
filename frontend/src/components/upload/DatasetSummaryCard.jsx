import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import {
  FileSpreadsheet,
  Table,
  ChevronDown,
  ChevronUp,
  Settings2,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { formatFileSize, formatInteger } from '../../utils/formatters';
import SchemaMappingCard from './SchemaMappingCard';

export default function DatasetSummaryCard({ dataset }) {
  const { runForecast, activeDataset } = useChat();
  const [showPreview, setShowPreview] = useState(false);
  const [showMappingEditor, setShowMappingEditor] = useState(
    dataset?.requires_confirmation || !dataset?.is_mapped
  );

  const previewRows = dataset?.preview || [];
  const columns = dataset?.columns || [];
  const dtypes = dataset?.dtypes || {};
  const isMapped = activeDataset?.is_mapped || dataset?.is_mapped;

  return (
    <div className="rounded-2xl border border-[#262626] bg-[#181818] overflow-hidden shadow-sm space-y-4 p-5">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#262626] pb-4">
        <div className="flex items-start space-x-3">
          <div className="p-2.5 rounded-xl bg-[#193228] text-emerald-400 border border-[#234b3c] flex-shrink-0">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              {dataset?.filename || 'Uploaded Dataset'}
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#242424] text-neutral-300 uppercase">
                {dataset?.file_type || 'CSV'}
              </span>
            </h3>
            <p className="text-xs text-neutral-400 mt-0.5">
              {formatInteger(dataset?.row_count)} rows • {dataset?.column_count} columns •{' '}
              {formatFileSize(dataset?.file_size_bytes)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#222222] hover:bg-[#2a2a2a] text-neutral-300 hover:text-white border border-[#2c2c2c] text-xs transition-colors cursor-pointer"
          >
            <Table className="w-3.5 h-3.5 text-neutral-400" />
            <span>{showPreview ? 'Hide Preview' : 'Inspect Preview'}</span>
            {showPreview ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => setShowMappingEditor(!showMappingEditor)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#222222] hover:bg-[#2a2a2a] text-neutral-300 hover:text-white border border-[#2c2c2c] text-xs transition-colors cursor-pointer"
          >
            <Settings2 className="w-3.5 h-3.5 text-neutral-400" />
            <span>{showMappingEditor ? 'Hide Schema' : 'Edit Schema'}</span>
          </button>
        </div>
      </div>

      {/* Compact Data Preview Table */}
      {showPreview && (
        <div className="space-y-2 rounded-xl bg-slate-950 border border-slate-800 p-3">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-semibold text-slate-300">Data Sample (First {previewRows.length} rows)</span>
            <span>Never returns full dataset</span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-850">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-900 border-b border-slate-800 text-slate-300">
                  {columns.map((col) => (
                    <th key={col} className="p-2.5 font-semibold whitespace-nowrap">
                      <div>{col}</div>
                      <span className="text-[10px] text-slate-500 font-mono font-normal">
                        {dtypes[col] || 'string'}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 text-slate-300">
                {previewRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-900/50 transition-colors">
                    {columns.map((col) => (
                      <td key={col} className="p-2.5 whitespace-nowrap font-mono text-[11px] text-slate-300">
                        {row[col] !== undefined && row[col] !== null ? String(row[col]) : '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Schema Mapping Editor */}
      {showMappingEditor && (
        <SchemaMappingCard
          dataset={dataset}
          onConfirmed={() => setShowMappingEditor(false)}
        />
      )}

      {/* Ready Action Footer */}
      {!showMappingEditor && isMapped && (
        <div className="flex items-center justify-between pt-2 text-xs border-t border-[#262626]">
          <div className="flex items-center space-x-2 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span className="font-medium">Schema verified & normalized</span>
          </div>
          <button
            onClick={() => runForecast({ horizon: 14, model_type: 'auto' })}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-neutral-200 text-black font-medium transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-black" />
            <span>Forecast Demand (14 Days)</span>
          </button>
        </div>
      )}
    </div>
  );
}
