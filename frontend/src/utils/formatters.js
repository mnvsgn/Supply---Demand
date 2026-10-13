/**
 * Formatters and helper utilities for numbers, dates, and file sizes.
 */

export function formatNumber(val, decimals = 1) {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return Number(val).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatInteger(val) {
  if (val === null || val === undefined || isNaN(val)) {
    return '0';
  }
  return Number(val).toLocaleString();
}

export function formatCurrency(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  return '$' + Number(val).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPercentage(val, decimals = 1) {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }
  // If val is decimal (e.g. 0.084), multiply by 100
  const pct = Math.abs(val) <= 1 && val !== 0 ? val * 100 : val;
  return `${pct.toFixed(decimals)}%`;
}

export function formatFileSize(bytes) {
  if (!bytes || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export function formatDate(dateVal) {
  if (!dateVal) return '—';
  try {
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) return String(dateVal);
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return String(dateVal);
  }
}

export function formatTime(timestamp) {
  if (!timestamp) return '';
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

/**
 * Neutralizes CSV formula injection (DDE attacks) by prefixing dangerous characters with a single quote.
 */
export function sanitizeCsvCell(value) {
  if (value === null || value === undefined) return '';
  const str = String(value);

  // If the cell begins with formula triggers (=, +, -, @, \t, \r), prefix with a single quote
  let safeStr = str;
  if (/^[=+\-@\t\r]/.test(safeStr)) {
    safeStr = `'${safeStr}`;
  }

  // Escape internal double quotes and wrap in quotes if commas, quotes, or newlines exist
  if (/[",\n\r]/.test(safeStr)) {
    return `"${safeStr.replace(/"/g, '""')}"`;
  }
  return safeStr;
}

/**
 * Sanitizes download filenames to prevent path traversal and invalid characters.
 */
export function sanitizeFilename(name = 'forecast_export') {
  const clean = name
    .replace(/[^a-zA-Z0-9_\-]/g, '_')
    .replace(/_+/g, '_')
    .slice(0, 60);
  return clean.endsWith('.csv') ? clean : `${clean}.csv`;
}

/**
 * Exports forecast data to a safe, formula-injection-protected CSV file.
 * Includes session isolation metadata.
 */
export function exportForecastToCsv(forecastRows, filename = 'forecast_export.csv', metadata = {}) {
  if (!forecastRows || forecastRows.length === 0) return;

  const safeFilename = sanitizeFilename(filename);

  // Safe CSV headers
  const headers = ['Date', 'Predicted_Demand', 'Lower_Bound_95', 'Upper_Bound_95'];

  const rows = forecastRows.map((row) => [
    sanitizeCsvCell(row.date),
    sanitizeCsvCell(row.predicted_demand ?? row.forecast ?? ''),
    sanitizeCsvCell(row.lower_bound ?? ''),
    sanitizeCsvCell(row.upper_bound ?? ''),
  ].join(','));

  // Session metadata comments at top of file
  const metaLines = [
    `# Supply and Demand Forecasting Export`,
    `# Session: ${sanitizeCsvCell(metadata.sessionId || 'active_session')}`,
    `# Model: ${sanitizeCsvCell(metadata.modelName || 'Auto Selected')}`,
    `# Horizon: ${sanitizeCsvCell(metadata.horizon || forecastRows.length)}`,
    `# Exported_At: ${sanitizeCsvCell(new Date().toISOString())}`,
  ];

  const csvContent = [...metaLines, headers.join(','), ...rows].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  link.setAttribute('download', safeFilename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Format technical model names into executive business-friendly names
 */
export function formatBusinessModelName(rawName) {
  if (!rawName) return 'Recommended Predictive Engine';
  const lower = String(rawName).toLowerCase();
  if (lower.includes('xgboost')) {
    return 'Adaptive Trend Forecaster';
  }
  if (lower.includes('random forest') || lower.includes('random_forest')) {
    return 'Pattern Recognition Forecaster';
  }
  if (lower.includes('seasonal naive') || lower.includes('seasonal_naive')) {
    return 'Seasonal Cycle Forecaster';
  }
  if (lower.includes('naive')) {
    return 'Baseline Historical Forecaster';
  }
  if (lower.includes('auto') || lower.includes('winning')) {
    return 'Top-Performing Demand Forecaster';
  }
  return rawName;
}

/**
 * Format error metrics into executive accuracy confidence / reliability rating (0-100%).
 * Handles both percentage format (e.g. 1.21 -> 99%, 6.66 -> 93%) and decimal ratio format (e.g. 0.0666 -> 93%).
 */
export function formatAccuracyRate(wape) {
  if (wape === null || wape === undefined || isNaN(wape)) return 'High Reliability';
  const num = Number(wape);
  // If wape is given as decimal ratio (<= 1.0 and > 0), convert to percentage
  const errorPct = Math.abs(num) <= 1 && num !== 0 ? num * 100 : num;
  const accuracy = Math.max(0, Math.min(100, Math.round(100 - errorPct)));
  return `${accuracy}%`;
}

/**
 * Word to numeric mapping for English numbers
 */
const WORD_NUMBERS = {
  one: 1,
  two: 2,
  three: 3,
  four: 4,
  five: 5,
  six: 6,
  seven: 7,
  eight: 8,
  nine: 9,
  ten: 10,
  eleven: 11,
  twelve: 12,
  thirteen: 13,
  fourteen: 14,
  fifteen: 15,
  twenty: 20,
  thirty: 30,
  sixty: 60,
  ninety: 90,
};

/**
 * Natural language horizon parser
 * Accurately extracts forecast horizons from user prompts:
 * - "next day", "tomorrow", "1 day", "1d" -> 1
 * - "next week", "1 week", "7d" -> 7
 * - "next 2 weeks", "two weeks" -> 14
 * - "next month", "1 month", "30d" -> 30
 * - "next quarter" -> 90
 * - "next year" -> 365
 * - word numbers ("three days", "five days")
 * - arbitrary numeric days ("next 3 days", "10 days", "horizon 5")
 */
export function parseHorizonFromText(prompt, defaultHorizon = 14) {
  if (!prompt || typeof prompt !== 'string') return defaultHorizon;
  const p = prompt.toLowerCase().trim();

  // 1. Tomorrow / Single day / Next day
  if (/\b(tomorrow|next\s+day|following\s+day|single\s+day|one\s+day|1\s*day)\b/.test(p)) {
    return 1;
  }

  // 2. Single week / Next week
  if (/\b(next\s+week|coming\s+week|one\s+week|1\s*week)\b/.test(p)) {
    return 7;
  }

  // 3. Single month / Next month
  if (/\b(next\s+month|coming\s+month|one\s+month|1\s*month)\b/.test(p)) {
    return 30;
  }

  // 4. Next quarter
  if (/\b(next\s+quarter|coming\s+quarter|one\s+quarter|1\s*quarter)\b/.test(p)) {
    return 90;
  }

  // 5. Next year
  if (/\b(next\s+year|coming\s+year|one\s+year|1\s*year)\b/.test(p)) {
    return 365;
  }

  // 6. Numeric with explicit units (e.g. "30days", "30 days", "2 weeks", "3 months", "7d", "14d")
  const numMatch = p.match(/(\d+)\s*[-]?\s*(days?|periods?|weeks?|months?|quarters?|years?|d\b|w\b|m\b)/);
  if (numMatch) {
    const val = parseInt(numMatch[1], 10);
    const unit = numMatch[2].toLowerCase();
    if (unit.startsWith('w')) {
      return Math.max(1, Math.min(val * 7, 365));
    }
    if (unit.startsWith('m')) {
      return Math.max(1, Math.min(val * 30, 365));
    }
    if (unit.startsWith('q')) {
      return Math.max(1, Math.min(val * 90, 365));
    }
    if (unit.startsWith('y')) {
      return Math.max(1, Math.min(val * 365, 365));
    }
    return Math.max(1, Math.min(val, 365));
  }

  // 7. Word numbers with units (e.g. "three days", "two weeks")
  const wordKeys = Object.keys(WORD_NUMBERS).join('|');
  const wordRegex = new RegExp(`\\b(${wordKeys})\\s*[-]?\\s*(days?|periods?|weeks?|months?)`);
  const wordMatch = p.match(wordRegex);
  if (wordMatch) {
    const val = WORD_NUMBERS[wordMatch[1]];
    const unit = wordMatch[2].toLowerCase();
    if (unit.includes('week')) {
      return Math.max(1, Math.min(val * 7, 365));
    }
    if (unit.includes('month')) {
      return Math.max(1, Math.min(val * 30, 365));
    }
    return Math.max(1, Math.min(val, 365));
  }

  // 8. General explicit horizon phrasing (e.g. "horizon of 5", "predict 10")
  const horizonMatch = p.match(/\b(?:horizon|for|periods?)\s*(?:of)?\s*(\d+)\b/);
  if (horizonMatch) {
    return Math.max(1, Math.min(parseInt(horizonMatch[1], 10), 365));
  }

  return defaultHorizon;
}

