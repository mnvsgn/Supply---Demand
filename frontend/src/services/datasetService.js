/**
 * Dataset Service for file uploading, schema mapping, and preview/analytics retrieval.
 */

import api, {
  uploadDataset,
  getDataset,
  updateDatasetMapping,
  getDatasetMapping,
  getDatasetAnalytics,
} from './api';

/**
 * Upload a CSV or XLSX dataset file to the backend
 * @param {File} file
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function upload(file, sessionId = null, options = {}) {
  return uploadDataset(file, sessionId, options);
}

/**
 * Fetch dataset metadata and summary
 * @param {string} datasetId
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function fetchDataset(datasetId, sessionId = null, options = {}) {
  return getDataset(datasetId, sessionId, options);
}

/**
 * Confirm or update column mappings for a dataset
 * @param {string} datasetId
 * @param {object} mapping
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function updateMapping(datasetId, mapping, sessionId = null, options = {}) {
  return updateDatasetMapping(datasetId, mapping, sessionId, options);
}

/**
 * Fetch active column mapping for a dataset
 * @param {string} datasetId
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function fetchMapping(datasetId, sessionId = null, options = {}) {
  return getDatasetMapping(datasetId, sessionId, options);
}

/**
 * Fetch raw or normalized preview rows
 * @param {string} datasetId
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function fetchPreview(datasetId, sessionId = null, options = {}) {
  const dataset = await getDataset(datasetId, sessionId, options);
  return {
    raw_preview: dataset.preview || [],
    normalized_preview: dataset.normalized_preview || [],
    columns: dataset.columns || [],
    row_count: dataset.row_count || 0,
  };
}

/**
 * Fetch grounded statistical business analytics for a dataset
 * @param {string} datasetId
 * @param {object} params
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function fetchAnalytics(datasetId, params = {}, sessionId = null, options = {}) {
  return getDatasetAnalytics(datasetId, params, sessionId, options);
}

export const datasetService = {
  upload,
  fetchDataset,
  updateMapping,
  fetchMapping,
  fetchPreview,
  fetchAnalytics,
};

export default datasetService;
