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
 * Format error metrics into executive accuracy confidence
 */
export function formatAccuracyRate(wape) {
  if (wape === null || wape === undefined || isNaN(wape)) return 'High Confidence';
  const accuracy = Math.max(0, Math.min(100, Math.round((1 - wape) * 100)));
  return `${accuracy}% Historical Accuracy`;
}

