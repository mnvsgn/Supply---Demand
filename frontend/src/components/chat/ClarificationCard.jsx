import React from 'react';
import { HelpCircle, ArrowRight, Tag, Calendar, Layers } from 'lucide-react';

export default function ClarificationCard({ clarification, onSelectOption }) {
  if (!clarification) return null;

  const { title, question, options = [] } = clarification;

  return (
    <div className="rounded-xl border border-purple-800/40 bg-purple-950/20 p-4 space-y-3 shadow-sm">
      <div className="flex items-center space-x-2 text-purple-400">
        <HelpCircle className="w-4 h-4 flex-shrink-0" />
        <h4 className="text-xs font-bold uppercase tracking-wider">
          {title || 'Clarification Needed'}
        </h4>
      </div>

      <p className="text-xs text-slate-200 leading-relaxed">
        {question}
      </p>

      {/* Actionable Option Pills */}
      {options.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {options.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => onSelectOption && onSelectOption(opt)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-purple-900/40 text-purple-200 hover:text-white border border-purple-800/50 hover:border-purple-600 text-xs font-medium transition-all shadow-sm group"
            >
              <span>{opt.label || opt.text || opt}</span>
              <ArrowRight className="w-3 h-3 text-purple-400 group-hover:translate-x-0.5 transition-transform" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
