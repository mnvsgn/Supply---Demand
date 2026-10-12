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

  /**
   * Coordinated File Upload
   */
  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;

    chat.addMessage('user', `Uploaded dataset: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'text');

    try {
      const activeSession = chat.sessionId || (await chat.checkBackendHealth());
      const uploadedDataset = await dataset.upload(file, activeSession);

      const assistantReply = `Received and validated **${uploadedDataset.filename}**!
• **Rows:** ${uploadedDataset.row_count.toLocaleString()}
• **Columns:** ${uploadedDataset.column_count}
• **Inferred Format:** ${uploadedDataset.file_type.toUpperCase()} (${(uploadedDataset.file_size_bytes / 1024).toFixed(1)} KB)

I have inspected the column headers and auto-detected candidate timestamp and demand target fields. Review the mapping suggestions below or adjust them before running forecasts.`;

      chat.addMessage('assistant', assistantReply, 'dataset_upload', uploadedDataset);
    } catch (err) {
      console.error('File upload failed:', err);
      chat.addMessage('assistant', `**Upload Rejected**: ${err.message}`, 'error', {
        code: err.code || 'UPLOAD_FAILED',
        detail: err.detail,
      });
    }
  }, [chat, dataset]);

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
    handleSelectClarificationOption: chat.handleSelectClarificationOption,

    // Dataset State
    activeDataset: dataset.activeDataset,
    isUploading: dataset.isUploading,
    isMapping: dataset.isMapping,
    uploadError: dataset.uploadError,
    handleFileUpload,
    confirmMapping: handleConfirmMapping,

    // Forecasting, Analytics & Evaluation
    isForecasting: chat.isForecasting,
    isEvaluating: chat.isEvaluating,
    isAnalyzing: chat.isAnalyzing,
    isResponding: chat.isResponding,
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
