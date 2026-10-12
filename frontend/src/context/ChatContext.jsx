import React, { createContext, useContext, useCallback } from 'react';
import useDataset from '../hooks/useDataset';
import useChatHook from '../hooks/useChat';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const dataset = useDataset();

  // Chat hook initialized with dataset states
  const chat = useChatHook(
    dataset.activeDataset,
    dataset.confirmMapping,
    dataset.clear
  );

  const [stagedFile, setStagedFile] = React.useState(null);

  const handleStageFile = useCallback((file) => {
    if (!file) return;
    setStagedFile(file);
  }, []);

  const handleClearStagedFile = useCallback(() => {
    setStagedFile(null);
  }, []);

  /**
   * Coordinated Prompt Submission with optional staged file attachment
   */
  const handleSendPromptWithFile = useCallback(async (promptText, fileOverride = null) => {
    const file = fileOverride || stagedFile;

    if (file) {
      setStagedFile(null);
      const userText = promptText && promptText.trim()
        ? promptText.trim()
        : 'Forecast demand for the next 14 periods';

      // 1. Add user message right away on the right side with file chip!
      chat.addMessage('user', userText, 'text', {
        filename: file.name,
        size: file.size,
      });

      try {
        const activeSession = chat.sessionId || (await chat.checkBackendHealth());
        const uploadedDataset = await dataset.upload(file, activeSession);

        // Auto-confirm mapping based on detected suggestions or fallback heuristics
        const suggestions = uploadedDataset.suggested_mapping || uploadedDataset.column_suggestions || {};
        const columns = uploadedDataset.columns || [];
        const dtypes = uploadedDataset.dtypes || {};

        // 1. Resolve date column from suggestions or fallback heuristics
        let dateCol = suggestions.date || suggestions.date_column || null;
        if (!dateCol && Array.isArray(columns)) {
          dateCol = columns.find((c) => /date|timestamp|day|time|period|order_date/i.test(c)) || null;
          if (!dateCol && dtypes) {
            dateCol = Object.keys(dtypes).find((k) => dtypes[k] === 'datetime') || null;
          }
        }

        // 2. Resolve demand column from suggestions or fallback heuristics
        let demandCol = suggestions.demand || suggestions.demand_column || null;
        if (!demandCol && Array.isArray(columns)) {
          demandCol = columns.find((c) => /demand|sales|quantity|qty|volume|orders|units|count/i.test(c)) || null;
          if (!demandCol && dtypes) {
            demandCol = Object.keys(dtypes).find((k) => 
              dtypes[k] === 'numeric' && !/price|cost|id|store|zip|year|day|month/i.test(k)
            ) || null;
          }
        }

        // If either date or demand cannot be detected, present the interactive schema mapping card
        if (!dateCol || !demandCol) {
          chat.addMessage(
            'assistant',
            'Your dataset was uploaded successfully. Please select which columns represent your **Date** and **Demand / Sales** below to generate your projections.',
            'schema_mapping',
            uploadedDataset
          );
          return;
        }

        const mappingData = {
          date_column: dateCol,
          demand_column: demandCol,
          product_id_column: suggestions.product_id || suggestions.product_id_column || null,
          store_id_column: suggestions.store_id || suggestions.store_id_column || null,
          price_column: suggestions.price || suggestions.price_column || null,
          promotion_column: suggestions.promotion || suggestions.promotion_column || null,
        };

        const normalizedDataset = await dataset.confirmMapping(
          uploadedDataset.dataset_id,
          mappingData,
          activeSession
        );

        const fullNormalizedDataset = {
          ...uploadedDataset,
          is_mapped: true,
          mapped_schema: normalizedDataset.mapped_schema,
          data_quality: normalizedDataset.data_quality,
          summary: normalizedDataset.summary,
          normalized_preview: normalizedDataset.normalized_preview,
        };
        dataset.setActiveDataset(fullNormalizedDataset);

        // Dispatch prompt against the new dataset (skip duplicate user message)
        await chat.handleSendPrompt(userText, fullNormalizedDataset, true);
      } catch (err) {
        console.error('File upload & prompt failed:', err);
        const friendlyMessage =
          err.status >= 500 || err.code === 'BACKEND_DISCONNECTED' || err.code === 'INTERNAL_SERVER_ERROR'
            ? 'Internal server error: The forecasting service is temporarily unreachable. Please try again shortly.'
            : (err.message || 'Unable to process uploaded dataset. Please try again.');

        chat.addMessage('assistant', friendlyMessage, 'error', {
          code: err.code || 'INTERNAL_SERVER_ERROR',
          detail: err.detail,
        });
      }
    } else {
      // Regular prompt
      return chat.handleSendPrompt(promptText);
    }
  }, [chat, dataset, stagedFile]);

  /**
   * Coordinated Mapping Confirmation
   */
  const handleConfirmMapping = useCallback(async (mappingData) => {
    if (!dataset.activeDataset) {
      chat.addMessage('assistant', 'No active dataset available for mapping.', 'error');
      return;
    }

    try {
      const res = await dataset.confirmMapping(
        dataset.activeDataset.dataset_id,
        mappingData,
        chat.sessionId
      );

      const quality = res.data_quality || {};
      const normSummary = res.summary || {};

      let reply = `Schema confirmed and dataset normalized!
• **Date Range:** ${normSummary.date_range?.start || 'N/A'} to ${normSummary.date_range?.end || 'N/A'}
• **Inferred Frequency:** ${normSummary.inferred_frequency || 'Daily'}
• **Total Usable Records:** ${normSummary.total_records?.toLocaleString()}
• **Total Historical Demand:** ${normSummary.total_demand?.toLocaleString()}
• **Average Demand / Period:** ${normSummary.average_demand_per_period?.toFixed(1)}`;

      if (quality.warnings?.length > 0) {
        reply += `\n\n⚠️ **Data Quality Notes:** ${quality.warnings.join('; ')}`;
      }

      chat.addMessage('assistant', reply, 'schema_mapping', res);
    } catch (err) {
      console.error('Schema mapping failed:', err);
      chat.addMessage('assistant', `**Mapping Error**: ${err.message}`, 'error', {
        code: err.code || 'MAPPING_ERROR',
        detail: err.detail,
      });
    }
  }, [chat, dataset]);

  const value = {
    // Session & Connection
    sessionId: chat.sessionId,
    backendConnected: chat.backendConnected,
    backendInfo: chat.backendInfo,
    checkBackendHealth: chat.checkBackendHealth,
    resetChat: chat.resetChat,

    // Conversation State
    messages: chat.messages,
    pendingClarification: chat.pendingClarification,
    addMessage: chat.addMessage,
    handleSendPrompt: chat.handleSendPrompt,
    handleRegenerate: chat.handleRegenerate,
    handleSelectClarificationOption: chat.handleSelectClarificationOption,

    // Dataset & Staged File State
    activeDataset: dataset.activeDataset,
    stagedFile,
    setStagedFile,
    handleStageFile,
    handleClearStagedFile,
    handleSendPromptWithFile,
    isUploading: dataset.isUploading,
    isMapping: dataset.isMapping,
    uploadError: dataset.uploadError,
    confirmMapping: handleConfirmMapping,

    // Forecasting, Analytics & Evaluation
    isForecasting: chat.isForecasting,
    isEvaluating: chat.isEvaluating,
    isAnalyzing: chat.isAnalyzing,
    isResponding: chat.isResponding,
    isGenerating: chat.isForecasting || chat.isEvaluating || chat.isAnalyzing || chat.isResponding,
    activeForecast: chat.activeForecast,
    runForecast: chat.runForecast,
    runEvaluation: chat.runEvaluation,
    runAnalytics: chat.runAnalytics,
    cancelActiveRequest: chat.cancelActiveRequest,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;
