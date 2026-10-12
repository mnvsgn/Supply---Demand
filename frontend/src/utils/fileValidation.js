/**
 * File validation utilities for spreadsheet uploads (CSV / XLSX).
 */

export const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];
export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
export const ALLOWED_MIME_TYPES = [
  'text/csv',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain',
];

/**
 * Validates file extension
 */
export function isExtensionAllowed(filename) {
  if (!filename) return false;
  const lower = filename.toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/**
 * Validates file size
 */
export function isSizeAllowed(fileSize) {
  return typeof fileSize === 'number' && fileSize > 0 && fileSize <= MAX_FILE_SIZE_BYTES;
}

/**
 * Validates file object before upload
 * @param {File} file
 * @returns {{ isValid: boolean, error: string | null }}
 */
export function validateFile(file) {
  if (!file) {
    return {
      isValid: false,
      error: 'No file selected. Please choose a CSV or XLSX file.',
    };
  }

  if (!isExtensionAllowed(file.name)) {
    return {
      isValid: false,
      error: `Invalid file extension. Allowed formats: ${ALLOWED_EXTENSIONS.join(', ')}`,
    };
  }

  if (file.size === 0) {
    return {
      isValid: false,
      error: 'The selected file is empty (0 bytes). Please upload a valid dataset.',
    };
  }

  if (!isSizeAllowed(file.size)) {
    return {
      isValid: false,
      error: `File size exceeds the 50 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`,
    };
  }

  return {
    isValid: true,
    error: null,
  };
}

/**
 * Validates detected or parsed headers for minimal forecasting requirements
 * @param {string[]} headers
 * @returns {{ hasDateLike: boolean, hasDemandLike: boolean, error: string | null }}
 */
export function validateHeaders(headers) {
  if (!Array.isArray(headers) || headers.length < 2) {
    return {
      hasDateLike: false,
      hasDemandLike: false,
      error: 'Dataset must have at least 2 columns (date and demand/quantity).',
    };
  }

  const lower = headers.map((h) => String(h).trim().toLowerCase());
  const datePatterns = ['date', 'time', 'timestamp', 'day', 'ds', 'period', 'week', 'month', 'year'];
  const demandPatterns = ['demand', 'sales', 'quantity', 'qty', 'units', 'volume', 'order', 'orders', 'sold', 'target', 'y'];

  const hasDateLike = lower.some((h) => datePatterns.some((p) => h.includes(p)));
  const hasDemandLike = lower.some((h) => demandPatterns.some((p) => h.includes(p)));

  let error = null;
  if (!hasDateLike && !hasDemandLike) {
    error = 'Could not detect date or demand columns. You will need to manually specify column mappings.';
  }

  return {
    hasDateLike,
    hasDemandLike,
    error,
  };
}

export default {
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  ALLOWED_MIME_TYPES,
  isExtensionAllowed,
  isSizeAllowed,
  validateFile,
  validateHeaders,
};
