/**
 * Administrator API Service.
 * Coordinates authentication, dashboard metrics, model performance,
 * system telemetry, and operational forecast verification.
 */

import api from './api';

const TOKEN_KEY = 'demandiq_admin_token';
const USERNAME_KEY = 'demandiq_admin_username';

export function getAdminToken() {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getAdminUsername() {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(USERNAME_KEY) || 'Administrator';
}

export function isAuthenticated() {
  return Boolean(getAdminToken());
}

/**
 * Authenticate administrator with username & password
 */
export async function login(username, password) {
  const res = await api.request('admin/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

  if (res && res.token) {
    sessionStorage.setItem(TOKEN_KEY, res.token);
    sessionStorage.setItem(USERNAME_KEY, res.username || username);
  }

  return res;
}

/**
 * Invalidate active administrator session token
 */
export async function logout() {
  const token = getAdminToken();
  try {
    if (token) {
      await api.request('admin/logout', {
        method: 'POST',
        adminToken: token,
      });
    }
  } catch (err) {
    console.debug('Admin logout background cleanup:', err);
  } finally {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USERNAME_KEY);
  }
}

/**
 * Fetch overview dashboard metrics and activity feed
 */
export async function getDashboard(options = {}) {
  const token = getAdminToken();
  return api.request('admin/dashboard', {
    adminToken: token,
    ...options,
  });
}

/**
 * Fetch 3-section model performance metrics and comparison table
 */
export async function getModelPerformance(options = {}) {
  const token = getAdminToken();
  return api.request('admin/performance', {
    adminToken: token,
    ...options,
  });
}

/**
 * Fetch runtime system information, library versions, and configuration
 */
export async function getSystemInfo(options = {}) {
  const token = getAdminToken();
  return api.request('admin/system-info', {
    adminToken: token,
    ...options,
  });
}

/**
 * Fetch recent activity audit log
 */
export async function getActivityLog(limit = 50, options = {}) {
  const token = getAdminToken();
  return api.request(`admin/activity?limit=${limit}`, {
    adminToken: token,
    ...options,
  });
}

/**
 * Verify predicted values against actual observations
 */
export async function verifyForecast(eventId, actualObservations, options = {}) {
  const token = getAdminToken();
  return api.request(`admin/forecasts/${eventId}/verify`, {
    method: 'POST',
    adminToken: token,
    body: JSON.stringify({ actual_observations: actualObservations }),
    ...options,
  });
}

export const adminService = {
  login,
  logout,
  getAdminToken,
  getAdminUsername,
  isAuthenticated,
  getDashboard,
  getModelPerformance,
  getSystemInfo,
  getActivityLog,
  verifyForecast,
};

export default adminService;
