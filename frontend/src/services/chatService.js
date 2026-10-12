/**
 * Chat Service for conversational supply & demand forecasting queries.
 */

import api, {
  getSessionConversation,
  appendSessionConversationMessage,
} from './api';

/**
 * Submit a conversational prompt to the backend chat API
 * @param {string} prompt
 * @param {string|null} datasetId
 * @param {string|null} sessionId
 * @param {object} options
 */
export async function submitPrompt(prompt, datasetId = null, sessionId = null, options = {}) {
  return api.request('chat', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      dataset_id: datasetId,
      session_id: sessionId,
    }),
    sessionId,
    ...options,
  });
}

/**
 * Fetch conversation history for a given session
 * @param {string} sessionId
 * @param {object} options
 */
export async function fetchHistory(sessionId, options = {}) {
  if (!sessionId) return { messages: [] };
  return getSessionConversation(sessionId, options);
}

/**
 * Append a message to backend session conversation tracking
 * @param {string} sessionId
 * @param {object} message
 * @param {object} options
 */
export async function appendMessage(sessionId, message, options = {}) {
  if (!sessionId) return null;
  return appendSessionConversationMessage(sessionId, message, options);
}

export const chatService = {
  submitPrompt,
  fetchHistory,
  appendMessage,
};

export default chatService;
