import { useState, useCallback } from 'react';
import api from '../services/api';

/**
 * Custom hook for dataset lifecycle, upload validation, schema mapping, and quality checks.
 */
export function useDataset() {
  const [activeDataset, setActiveDataset] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isMapping, setIsMapping] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  /**
   * Upload and register a CSV/XLSX file
   */
  const upload = useCallback(async (file, sessionId = null, signal = null) => {
    if (!file) throw new Error('No file provided for upload.');

    // Client-side quick extension check
    const lowerName = file.name.toLowerCase();
    if (!lowerName.endsWith('.csv') && !lowerName.endsWith('.xlsx')) {
      const extErr = new Error("Unsupported file type. Please upload a '.csv' or '.xlsx' spreadsheet.");
      extErr.code = 'UNSUPPORTED_FILE_TYPE';
      throw extErr;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      const res = await api.uploadDataset(file, sessionId, { signal });
      const datasetState = {
        ...res,
        is_mapped: false,
      };
      setActiveDataset(datasetState);
      return datasetState;
    } catch (err) {
      if (err.name === 'AbortError') throw err;
      setUploadError(err);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, []);

  /**
   * Confirm or update canonical schema mappings
   */
  const confirmMapping = useCallback(async (datasetId, mappingData, sessionId = null, signal = null) => {
    if (!datasetId) throw new Error('No dataset ID provided for mapping confirmation.');

    setIsMapping(true);
    try {
      const res = await api.updateDatasetMapping(datasetId, mappingData, sessionId, { signal });
      
      setActiveDataset(prev => {
        if (!prev || prev.dataset_id !== datasetId) return prev;
        return {
          ...prev,
          is_mapped: true,
          mapped_schema: res.mapped_schema,
          data_quality: res.data_quality,
          summary: res.summary,
          normalized_preview: res.normalized_preview,
        };
      });

      return res;
    } finally {
      setIsMapping(false);
    }
  }, []);

  /**
   * Refresh dataset status from backend
   */
  const fetchDataset = useCallback(async (datasetId, sessionId = null, signal = null) => {
    if (!datasetId) return null;
    try {
      const res = await api.getDataset(datasetId, sessionId, { signal });
      setActiveDataset(prev => ({
        ...(prev || {}),
        ...res,
      }));
      return res;
    } catch (err) {
      if (err.name === 'AbortError') throw err;
      console.warn('Failed to refresh dataset:', err);
      return null;
    }
  }, []);

  const clear = useCallback(() => {
    setActiveDataset(null);
    setUploadError(null);
  }, []);

  return {
    activeDataset,
    setActiveDataset,
    isUploading,
    isMapping,
    uploadError,
    upload,
    confirmMapping,
    fetchDataset,
    clear,
  };
}

export default useDataset;
