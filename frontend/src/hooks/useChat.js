import { useState, useCallback, useRef, useEffect } from 'react';
import api from '../services/api';

const FORMAL_DOMAIN_RESPONSE = `I am a specialized **Supply and Demand Forecasting Assistant**. My domain is strictly focused on supply-chain time-series analytics, historical dataset ingestion, canonical schema validation, and out-of-sample demand forecasting using statistical and machine learning models (Naive, Seasonal Naive, Random Forest, and XGBoost).

I cannot assist with general-purpose programming, trivia, creative writing, or topics outside supply-chain forecasting.

How can I help you analyze your historical demand dataset today?`;

/**
 * Determine if a user prompt is out of scope for supply and demand forecasting
 */
function isOutOfScope(prompt) {
  const p = prompt.toLowerCase();

  // Known out-of-scope triggers
  const offTopicPatterns = [
    /\b(poem|poetry|song|lyrics|story|novel|joke|riddle)\b/,
    /\b(weather in|recipe for|capital of|who is|who was|who won)\b/,
    /\b(write a python script to scrape|build a website|hack|crypto|bitcoin)\b/,
    /\b(write an essay|translate into french|tell me a bedtime)\b/,
  ];

  for (const pattern of offTopicPatterns) {
    if (pattern.test(p)) {
      return true;
    }
  }

  // Known in-domain keywords
  const inDomainKeywords = [
    'forecast', 'predict', 'demand', 'supply', 'sales', 'volume', 'horizon',
    'xgboost', 'random forest', 'naive', 'seasonal', 'wape', 'mae', 'rmse',
    'metric', 'dataset', 'csv', 'xlsx', 'data', 'mapping', 'column', 'columns',
    'schema', 'inventory', 'sku', 'product', 'store', 'date', 'frequency',
    'quality', 'gaps', 'duplicates', 'backtest', 'lag', 'trend', 'seasonality',
    'upload', 'evaluate', 'compare', 'model', 'interval', 'bound', 'history',
    'help', 'hello', 'hi', 'start', 'begin', 'how to', 'explain'
  ];

  const hasInDomainWord = inDomainKeywords.some((kw) => p.includes(kw));
  return !hasInDomainWord && p.split(' ').length > 2;
}

/**
 * Custom hook for conversation management, prompt routing, and intent dispatching.
 */
export function useChat(activeDataset, confirmMapping, resetDataset) {
  const [sessionId, setSessionId] = useState(() => {
    return sessionStorage.getItem('supply_demand_session_id') || null;
  });
  const [messages, setMessages] = useState([]);
  const [activeForecast, setActiveForecast] = useState(null);
  const [backendConnected, setBackendConnected] = useState(null);
  const [backendInfo, setBackendInfo] = useState(null);

  const [isForecasting, setIsForecasting] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [isInitializingSession, setIsInitializingSession] = useState(false);

  // Active clarification state (e.g. choice between aggregate vs specific SKU)
  const [pendingClarification, setPendingClarification] = useState(null);

  // Abort controller ref for cancelling stale requests
  const abortControllerRef = useRef(null);

  /**
   * Helper to append message locally and record in backend session history
   */
  const addMessage = useCallback((sender, content, type = 'text', data = null) => {
    const newMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
      sender, // 'user' | 'assistant' | 'system'
      content,
      type, // 'text' | 'dataset_upload' | 'schema_mapping' | 'forecast' | 'evaluation' | 'quality_warning' | 'clarification' | 'error'
      data,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newMessage]);

    // Silently persist message to backend session conversation tracking
    const currentSession = sessionStorage.getItem('supply_demand_session_id');
    if (currentSession && (sender === 'user' || sender === 'assistant')) {
      api.appendSessionConversationMessage(currentSession, {
        role: sender,
        content: typeof content === 'string' ? content : 'Structured response',
        metadata: {
          type,
          dataset_id: data?.dataset_id || activeDataset?.dataset_id || null,
        },
      }).catch((err) => {
        console.debug('Session conversation tracking background update:', err);
      });
    }

    return newMessage;
  }, [activeDataset]);

  /**
   * Initialize or verify temporary session with backend
   */
  const initSession = useCallback(async () => {
    setIsInitializingSession(true);
    try {
      const health = await api.getBackendHealth();
      setBackendConnected(true);
      setBackendInfo(health);

      let currentId = sessionStorage.getItem('supply_demand_session_id');
      if (currentId) {
        try {
          const sess = await api.getSession(currentId);
          setSessionId(sess.session_id);
          return sess.session_id;
        } catch {
          sessionStorage.removeItem('supply_demand_session_id');
          currentId = null;
        }
      }

      if (!currentId) {
        const newSess = await api.createSession();
        sessionStorage.setItem('supply_demand_session_id', newSess.session_id);
        setSessionId(newSess.session_id);
        return newSess.session_id;
      }
    } catch (err) {
      console.warn('Backend connectivity check failed:', err);
      setBackendConnected(false);
      setBackendInfo(null);
      return null;
    } finally {
      setIsInitializingSession(false);
    }
  }, []);

  useEffect(() => {
    initSession();
    const interval = setInterval(async () => {
      try {
        const health = await api.getBackendHealth();
        setBackendConnected(true);
        setBackendInfo(health);
      } catch {
        setBackendConnected(false);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [initSession]);

  /**
   * Cancel any in-flight backend forecast or evaluation request
   */
  const cancelActiveRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsForecasting(false);
    setIsEvaluating(false);
    setIsAnalyzing(false);
    setIsResponding(false);
  }, []);

  /**
   * Run grounded business analytics (trends, rankings, seasonality, safety stock)
   */
  const runAnalytics = useCallback(async (options = {}) => {
    if (!activeDataset) {
      addMessage('assistant', 'Please upload a dataset before generating business analytics.', 'error');
      return;
    }

    cancelActiveRequest();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsAnalyzing(true);
    try {
      const analyticsRes = await api.getDatasetAnalytics(
        activeDataset.dataset_id,
        options,
        sessionId,
        { signal: controller.signal }
      );

      const assistantText = `Business analytics generated directly from validated historical observations. Review empirical sales trends, calendar seasonality, product rankings, and inventory sizing below:`;

      addMessage('assistant', assistantText, 'analytics', analyticsRes);
    } catch (err) {
      if (err.name === 'AbortError') return;

      console.error('Analytics request failed:', err);
      if (err.code === 'SESSION_NOT_FOUND' || err.status === 404) {
        addMessage(
          'assistant',
          '**Session Expired**: Your temporary session has expired. A fresh session has been initialized. Please re-upload your dataset.',
          'error'
        );
        initSession();
        return;
      }

      addMessage('assistant', `**Analytics Generation Failed**: ${err.message}`, 'error', {
        code: err.code || 'ANALYTICS_FAILED',
        detail: err.detail,
      });
    } finally {
      setIsAnalyzing(false);
      abortControllerRef.current = null;
    }
  }, [activeDataset, sessionId, cancelActiveRequest, addMessage, initSession]);

  /**
   * Run forecast on backend
   */
  const runForecast = useCallback(async (options = {}) => {
    if (!activeDataset) {
      addMessage('assistant', 'Please upload a dataset (.csv or .xlsx) before generating a forecast.', 'error');
      return;
    }

    // Auto-map if suggestions are present and unmapped
    if (!activeDataset.is_mapped) {
      if (activeDataset.suggested_mapping?.date && activeDataset.suggested_mapping?.demand) {
        try {
          await confirmMapping(activeDataset.dataset_id, {
            date_column: activeDataset.suggested_mapping.date,
            demand_column: activeDataset.suggested_mapping.demand,
            product_id_column: activeDataset.suggested_mapping.product_id || null,
            store_id_column: activeDataset.suggested_mapping.store_id || null,
            price_column: activeDataset.suggested_mapping.price || null,
            promotion_column: activeDataset.suggested_mapping.promotion || null,
          }, sessionId);
        } catch (mErr) {
          addMessage('assistant', `Please confirm column mappings before running a forecast: ${mErr.message}`, 'error');
          return;
        }
      } else {
        addMessage('assistant', 'Please confirm column mappings for Date and Demand before forecasting.', 'error');
        return;
      }
    }

    // Cancel any previous in-flight request
    cancelActiveRequest();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsForecasting(true);
    const horizon = options.horizon || 14;
    const modelType = options.model_type || 'auto';
    const targetLevel = options.target_level || 'aggregate';
    const productId = options.product_id || null;

    try {
      const forecastRes = await api.generateForecast(
        activeDataset.dataset_id,
        {
          model_type: modelType,
          horizon,
          target_level: targetLevel,
          product_id: productId,
          confidence_level: options.confidence_level ?? 0.95,
          primary_metric: options.primary_metric || 'wape',
          use_rolling_origin: Boolean(options.use_rolling_origin),
          backtest_folds: options.backtest_folds || 3,
        },
        sessionId,
        { signal: controller.signal }
      );

      setActiveForecast(forecastRes);

      const winModel = forecastRes.model_name || 'Winning Forecaster';
      const pointsCount = forecastRes.forecast?.length || 0;
      const targetDesc = productId ? `for SKU **${productId}**` : 'for aggregate demand';

      const assistantText = `Forecasting completed ${targetDesc} across the next **${pointsCount} periods**.
The winning model selected via out-of-sample chronological backtesting is **${winModel}**.
Inspect the trajectory chart and projection table below:`;

      addMessage('assistant', assistantText, 'forecast', forecastRes);
    } catch (err) {
      if (err.name === 'AbortError') return;

      console.error('Forecast request failed:', err);
      // Check for session expiration
      if (err.code === 'SESSION_NOT_FOUND' || err.status === 404) {
        addMessage(
          'assistant',
          '**Session Expired**: Your temporary session has expired. A fresh session has been created. Please re-upload your dataset to continue.',
          'error'
        );
        initSession();
        return;
      }

      addMessage('assistant', `**Forecast Generation Failed**: ${err.message}`, 'error', {
        code: err.code || 'FORECAST_FAILED',
        detail: err.detail,
      });
    } finally {
      setIsForecasting(false);
      abortControllerRef.current = null;
    }
  }, [activeDataset, sessionId, confirmMapping, cancelActiveRequest, addMessage, initSession]);

  /**
   * Run comparative model evaluation on backend
   */
  const runEvaluation = useCallback(async (options = {}) => {
    if (!activeDataset) {
      addMessage('assistant', 'Please upload a dataset before evaluating forecasting models.', 'error');
      return;
    }

    cancelActiveRequest();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsEvaluating(true);
    const horizon = options.horizon || 14;

    try {
      const evalRes = await api.evaluateModels(
        activeDataset.dataset_id,
        {
          horizon,
          target_level: options.target_level || 'aggregate',
          product_id: options.product_id || null,
          primary_metric: options.primary_metric || 'wape',
          use_rolling_origin: Boolean(options.use_rolling_origin),
          backtest_folds: options.backtest_folds || 3,
        },
        sessionId,
        { signal: controller.signal }
      );

      const winning = evalRes.selected_model_name;
      const primaryMetric = (evalRes.primary_metric || 'wape').toUpperCase();
      const assistantText = `Model evaluation complete! Backtested all candidates on the chronological validation split.
The top-performing model is **${winning}** based on lowest **${primaryMetric}** error. Compare the evaluation table below:`;

      addMessage('assistant', assistantText, 'evaluation', evalRes);
    } catch (err) {
      if (err.name === 'AbortError') return;

      console.error('Evaluation request failed:', err);
      if (err.code === 'SESSION_NOT_FOUND' || err.status === 404) {
        addMessage(
          'assistant',
          '**Session Expired**: Your temporary session has expired. A fresh session has been initialized. Please re-upload your dataset.',
          'error'
        );
        initSession();
        return;
      }

      addMessage('assistant', `**Model Evaluation Failed**: ${err.message}`, 'error', {
        code: err.code || 'EVALUATION_FAILED',
        detail: err.detail,
      });
    } finally {
      setIsEvaluating(false);
      abortControllerRef.current = null;
    }
  }, [activeDataset, sessionId, cancelActiveRequest, addMessage, initSession]);

  /**
   * Prompt Dispatcher: routes user prompts to backend operations or handles out-of-scope / clarification queries
   */
  const handleSendPrompt = useCallback(async (text) => {
    if (!text || !text.trim()) return;

    // Prevent duplicate in-flight submissions
    if (isForecasting || isEvaluating || isAnalyzing || isResponding) {
      return;
    }

    const prompt = text.trim();
    addMessage('user', prompt, 'text');
    setIsResponding(true);

    try {
      // 1. Check for Out-of-Scope Prompts
      if (isOutOfScope(prompt)) {
        await new Promise((r) => setTimeout(r, 650));
        addMessage('assistant', FORMAL_DOMAIN_RESPONSE, 'text');
        return;
      }

      const lower = prompt.toLowerCase();

      // 2. Check for Forecast Intent
      if (lower.includes('forecast') || lower.includes('predict') || lower.includes('projection')) {
        if (!activeDataset) {
          await new Promise((r) => setTimeout(r, 600));
          addMessage(
            'assistant',
            'I need a historical demand dataset before generating forecasts. Please upload a CSV or XLSX file using the attachment button or drag-and-drop zone.',
            'text'
          );
          return;
        }

        // Clarification check: check if user asked for product-specific forecast
        const normSummary = activeDataset.summary;
        const hasProducts = normSummary?.has_product_hierarchy || (normSummary?.unique_products_count > 1);
        
        if (lower.includes('product') && hasProducts && !lower.includes('sku') && !lower.includes('aggregate')) {
          await new Promise((r) => setTimeout(r, 600));
          const topProducts = normSummary?.top_products || [];
          const options = [
            { label: 'Forecast Aggregate Total Demand', target_level: 'aggregate', horizon: 14 },
            ...topProducts.slice(0, 3).map((p) => ({
              label: `Forecast SKU: ${p.product_id}`,
              target_level: 'product',
              product_id: p.product_id,
              horizon: 14,
            })),
          ];

          const clar = {
            title: 'Product Scope Clarification',
            question: `Your dataset contains ${normSummary.unique_products_count} distinct products. Would you like an aggregate forecast across all products or a single-product forecast?`,
            options,
          };
          setPendingClarification(clar);
          addMessage('assistant', clar.question, 'clarification', clar);
          return;
        }

        // Parse horizon
        const horizonMatch = lower.match(/(\d+)\s*(days?|periods?|weeks?|months?)/);
        const parsedHorizon = horizonMatch ? parseInt(horizonMatch[1], 10) : 14;

        let modelType = 'auto';
        if (lower.includes('xgboost')) modelType = 'xgboost';
        else if (lower.includes('random forest')) modelType = 'random_forest';
        else if (lower.includes('seasonal naive')) modelType = 'seasonal_naive';
        else if (lower.includes('naive')) modelType = 'naive';

        await runForecast({ horizon: parsedHorizon, model_type: modelType });
        return;
      }

      // 3. Check for Model Comparison Intent
      if (lower.includes('compare') || lower.includes('evaluate') || lower.includes('benchmark') || lower.includes('metrics')) {
        if (!activeDataset) {
          await new Promise((r) => setTimeout(r, 600));
          addMessage(
            'assistant',
            'To benchmark forecasting models, please upload a dataset containing historical demand observations.',
            'text'
          );
          return;
        }
        await runEvaluation({ horizon: 14 });
        return;
      }

      // 4. Check for Data Quality & Diagnostics Intent
      if (lower.includes('quality') || lower.includes('missing') || lower.includes('gap') || lower.includes('summary') || lower.includes('duplicate')) {
        if (!activeDataset) {
          await new Promise((r) => setTimeout(r, 600));
          addMessage(
            'assistant',
            'Please upload a dataset to run temporal alignment, missing date gap detection, and duplicate checks.',
            'text'
          );
          return;
        }

        await new Promise((r) => setTimeout(r, 600));
        const quality = activeDataset.data_quality;
        const summary = activeDataset.summary;

        let msg = `### Dataset Quality & Diagnostics Report
• **Filename:** ${activeDataset.filename}
• **Total Usable Records:** ${(summary?.total_records || activeDataset.row_count).toLocaleString()}
• **Detected Frequency:** ${quality?.detected_frequency || summary?.inferred_frequency || 'Daily'}
• **Missing Date Intervals:** ${quality?.has_date_gaps ? `⚠️ ${quality.gap_count} gaps detected` : '✅ None (continuous time grid)'}
• **Negative Demand Observations:** ${quality?.has_negative_demand ? `⚠️ ${quality.negative_demand_count} negative rows` : '✅ None'}
• **Duplicate Timestamps:** ${quality?.has_duplicate_dates ? `⚠️ ${quality.duplicate_count} duplicate rows` : '✅ None'}`;

        if (activeDataset.ambiguity_warnings?.length > 0) {
          msg += `\n\n⚠️ **Ambiguities:** ${activeDataset.ambiguity_warnings.join('; ')}`;
        }

        addMessage('assistant', msg, 'quality_warning', quality);
        return;
      }

      // 5. Check for Business Analytics, Trends, Seasonality, Product Rankings, or Inventory Intent
      if (
        lower.includes('trend') ||
        lower.includes('seasonality') ||
        lower.includes('ranking') ||
        lower.includes('pareto') ||
        lower.includes('insight') ||
        lower.includes('safety stock') ||
        lower.includes('reorder point') ||
        lower.includes('rop') ||
        lower.includes('inventory')
      ) {
        if (!activeDataset) {
          await new Promise((r) => setTimeout(r, 600));
          addMessage(
            'assistant',
            'Please upload a historical demand dataset to compute sales trends, calendar cycles, product rankings, or safety stock sizing.',
            'text'
          );
          return;
        }

        // Check if lead time parameter was provided in prompt
        const leadMatch =
          lower.match(/(\d+)\s*(?:days?|periods?|weeks?)?\s*lead/i) ||
          lower.match(/lead\s*(?:time)?\s*(?:of)?\s*(\d+)/i);
        const leadTime = leadMatch ? parseInt(leadMatch[1] || leadMatch[2], 10) : null;

        await runAnalytics({ lead_time_days: leadTime, service_level: 0.95 });
        return;
      }

      // 6. Default Guided Response
      await new Promise((r) => setTimeout(r, 600));
      if (!activeDataset) {
        addMessage(
          'assistant',
          `I am ready to assist with your supply and demand forecasting workflow.
1. **Upload your dataset** (.csv or .xlsx) using the attach button.
2. Verify or adjust auto-detected date and demand column mappings.
3. Ask me to **"Forecast total demand for the next 14 days"**, **"Show sales trends and seasonality"**, or **"Compare all forecasting models"**.`,
          'text'
        );
      } else {
        addMessage(
          'assistant',
          `Dataset **${activeDataset.filename}** is active in the current session.
You can run any of the following operations:
• **"Forecast total demand for the next 14 days"**
• **"Show sales trends, seasonality and safety stock"**
• **"Compare Naive, Random Forest, and XGBoost models"**
• **"Inspect dataset quality and missing date gaps"**`,
          'text'
        );
      }
    } finally {
      setIsResponding(false);
    }
  }, [activeDataset, isForecasting, isEvaluating, isAnalyzing, isResponding, addMessage, runForecast, runEvaluation, runAnalytics]);

  /**
   * Handle user selection on a clarification card
   */
  const handleSelectClarificationOption = useCallback(async (option) => {
    setPendingClarification(null);
    if (!option) return;

    if (option.target_level) {
      await runForecast({
        horizon: option.horizon || 14,
        target_level: option.target_level,
        product_id: option.product_id || null,
      });
    } else if (option.prompt) {
      await handleSendPrompt(option.prompt);
    }
  }, [runForecast, handleSendPrompt]);

  /**
   * Start fresh chat / clear session
   */
  const resetChat = useCallback(async () => {
    cancelActiveRequest();
    if (sessionId) {
      try {
        await api.deleteSession(sessionId);
      } catch (err) {
        console.warn('Could not delete session on reset:', err);
      }
      sessionStorage.removeItem('supply_demand_session_id');
    }
    setSessionId(null);
    setMessages([]);
    setActiveForecast(null);
    setPendingClarification(null);
    if (resetDataset) resetDataset();
    await initSession();
  }, [sessionId, cancelActiveRequest, resetDataset, initSession]);

  return {
    sessionId,
    messages,
    activeForecast,
    backendConnected,
    backendInfo,
    isForecasting,
    isEvaluating,
    isAnalyzing,
    isResponding,
    isInitializingSession,
    pendingClarification,
    addMessage,
    runForecast,
    runEvaluation,
    runAnalytics,
    handleSendPrompt,
    handleSelectClarificationOption,
    cancelActiveRequest,
    resetChat,
    checkBackendHealth: initSession,
  };
}

export default useChat;
