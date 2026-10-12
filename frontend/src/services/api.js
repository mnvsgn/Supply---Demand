/**
 * Centralized API service configuration and client methods.
 * Strictly communicates with FastAPI backend at /api/v1 (or VITE_API_BASE_URL).
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Generic request helper with consistent JSON error parsing and abort signal support.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL.replace(/\/+$/, '')}/${endpoint.replace(/^\/+/, '')}`;
  
  const headers = {
    ...(!options.isFormData && { 'Content-Type': 'application/json' }),
    ...(options.sessionId && { 'X-Session-ID': options.sessionId }),
    ...(options.adminToken && { Authorization: `Bearer ${options.adminToken}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}`;
      let detail = null;
      let errorCode = 'API_ERROR';

      if (data) {
        errorMsg = data.message || data.error || (typeof data.detail === 'string' ? data.detail : null) || errorMsg;
        detail = data.detail || null;
        errorCode = data.code || `HTTP_${response.status}`;
      }

      const err = new Error(errorMsg);
      err.status = response.status;
      err.code = errorCode;
      err.detail = detail;
      throw err;
    }

    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      // Re-throw abort errors cleanly for cancellation handling
      throw error;
    }
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      const connErr = new Error('Cannot connect to backend server. Please verify FastAPI is running at http://localhost:8000.');
      connErr.code = 'BACKEND_DISCONNECTED';
      connErr.status = 0;
      throw connErr;
    }
    throw error;
  }
}

/**
 * Health check endpoint
 */
export async function getBackendHealth(options = {}) {
  return request('health', options);
}

/**
 * Temporary Session Management
 */
export async function createSession(ttlMinutes = 60, idleTimeoutMinutes = 30, options = {}) {
  return request('sessions', {
    method: 'POST',
    body: JSON.stringify({
      ttl_minutes: ttlMinutes,
      idle_timeout_minutes: idleTimeoutMinutes,
    }),
    ...options,
  });
}

export async function getSession(sessionId, options = {}) {
  return request(`sessions/${sessionId}`, options);
}

export async function deleteSession(sessionId, options = {}) {
  return request(`sessions/${sessionId}`, {
    method: 'DELETE',
    ...options,
  });
}

/**
 * Session Conversation History
 */
export async function getSessionConversation(sessionId, options = {}) {
  return request(`sessions/${sessionId}/conversation`, {
    sessionId,
    ...options,
  });
}

export async function appendSessionConversationMessage(sessionId, message, options = {}) {
  return request(`sessions/${sessionId}/conversation`, {
    method: 'POST',
    body: JSON.stringify({
      role: message.role || 'user',
      content: message.content || '',
      metadata: message.metadata || null,
    }),
    sessionId,
    ...options,
  });
}

// Backwards-compatible aliases
export const getSessionHistory = getSessionConversation;
export const appendSessionHistory = appendSessionConversationMessage;

/**
 * Dataset Ingestion & Metadata
 */
export async function uploadDataset(file, sessionId = null, options = {}) {
  const formData = new FormData();
  formData.append('file', file);

  return request('datasets/upload', {
    method: 'POST',
    body: formData,
    isFormData: true,
    sessionId,
    ...options,
  });
}

export async function getDataset(datasetId, sessionId = null, options = {}) {
  return request(`datasets/${datasetId}`, {
    sessionId,
    ...options,
  });
}

/**
 * Schema Mapping & Data Quality
 */
export async function updateDatasetMapping(datasetId, mapping, sessionId = null, options = {}) {
  return request(`datasets/${datasetId}/mapping`, {
    method: 'POST',
    body: JSON.stringify(mapping),
    sessionId,
    ...options,
  });
}

export async function getDatasetMapping(datasetId, sessionId = null, options = {}) {
  return request(`datasets/${datasetId}/mapping`, {
    sessionId,
    ...options,
  });
}

/**
 * Multi-Step Forecasting Engine
 */
export async function generateForecast(datasetId, options = {}, sessionId = null, fetchOptions = {}) {
  const payload = {
    model_type: options.model_type || 'auto',
    horizon: Number(options.horizon) || 14,
    target_level: options.target_level || 'aggregate',
    product_id: options.product_id || null,
    confidence_level: options.confidence_level ?? 0.95,
    primary_metric: options.primary_metric || 'wape',
    use_rolling_origin: Boolean(options.use_rolling_origin),
    backtest_folds: Number(options.backtest_folds) || 3,
  };

  return request(`datasets/${datasetId}/forecast`, {
    method: 'POST',
    body: JSON.stringify(payload),
    sessionId,
    ...fetchOptions,
  });
}

/**
 * Model Evaluation & Comparative Backtesting
 */
export async function evaluateModels(datasetId, options = {}, sessionId = null, fetchOptions = {}) {
  const payload = {
    horizon: Number(options.horizon) || 14,
    target_level: options.target_level || 'aggregate',
    product_id: options.product_id || null,
    primary_metric: options.primary_metric || 'wape',
    use_rolling_origin: Boolean(options.use_rolling_origin),
    backtest_folds: Number(options.backtest_folds) || 3,
  };

  return request(`datasets/${datasetId}/evaluate`, {
    method: 'POST',
    body: JSON.stringify(payload),
    sessionId,
    ...fetchOptions,
  });
}

/**
 * Grounded Business Analytics & Inventory Planning
 */
export async function getDatasetAnalytics(datasetId, options = {}, sessionId = null, fetchOptions = {}) {
  const payload = {
    lead_time_days: options.lead_time_days ?? null,
    service_level: options.service_level ?? 0.95,
    current_inventory: options.current_inventory ?? null,
    product_id: options.product_id ?? null,
  };

  return request(`datasets/${datasetId}/analytics`, {
    method: 'POST',
    body: JSON.stringify(payload),
    sessionId,
    ...fetchOptions,
  });
}

export default {
  getBackendHealth,
  createSession,
  getSession,
  deleteSession,
  getSessionConversation,
  appendSessionConversationMessage,
  getSessionHistory,
  appendSessionHistory,
  uploadDataset,
  getDataset,
  updateDatasetMapping,
  getDatasetMapping,
  generateForecast,
  evaluateModels,
  getDatasetAnalytics,
  request,
  baseUrl: API_BASE_URL,
};
