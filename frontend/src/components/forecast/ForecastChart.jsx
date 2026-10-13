import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts';
import { useTheme } from '../../context/ThemeContext';
import { formatNumber, formatDate } from '../../utils/formatters';
import { Eye, EyeOff, Info, Layers, Tag, Calendar, Clock } from 'lucide-react';

export default function ForecastChart({
  forecastRows = [],
  recentHistory = [],
  modelName = '',
  frequency = 'D',
  targetProduct = null,
  horizon = 14,
  units = 'Units',
}) {
  const { isDark } = useTheme();
  const [showBounds, setShowBounds] = useState(true);
  const [showHistorical, setShowHistorical] = useState(true);

  // Check if prediction intervals are valid (not identical or missing)
  const hasValidIntervals = useMemo(() => {
    if (!forecastRows || forecastRows.length === 0) return false;
    return forecastRows.some(
      (pt) =>
        pt.lower_bound !== null &&
        pt.upper_bound !== null &&
        pt.lower_bound !== undefined &&
        pt.upper_bound !== undefined &&
        Number(pt.upper_bound) > Number(pt.lower_bound)
    );
  }, [forecastRows]);

  // Combine historical observations and out-of-sample forecast points
  const chartData = useMemo(() => {
    const combined = [];

    // 1. Add historical points ONLY IF showHistorical is TRUE
    if (showHistorical && recentHistory && recentHistory.length > 0) {
      const histLen = recentHistory.length;
      recentHistory.forEach((pt, idx) => {
        const isLastHist = idx === histLen - 1;
        combined.push({
          date: pt.date,
          actual: pt.demand,
          predicted: isLastHist && forecastRows?.length > 0 ? pt.demand : null,
          lower: isLastHist && forecastRows?.length > 0 && hasValidIntervals ? pt.demand : null,
          upper: isLastHist && forecastRows?.length > 0 && hasValidIntervals ? pt.demand : null,
          type: 'history',
        });
      });
    }

    // 2. Add forecast points
    if (forecastRows && forecastRows.length > 0) {
      forecastRows.forEach((pt) => {
        const pred = pt.predicted_demand ?? pt.forecast;
        combined.push({
          date: pt.date,
          actual: null,
          predicted: pred,
          lower: hasValidIntervals ? (pt.lower_bound ?? pred) : null,
          upper: hasValidIntervals ? (pt.upper_bound ?? pred) : null,
          type: 'forecast',
        });
      });
    }

    return combined;
  }, [showHistorical, recentHistory, forecastRows, hasValidIntervals]);

  // Dynamic Y-axis domain calculation ensuring points never hug the chart ceiling
  const yDomain = useMemo(() => {
    if (!chartData || chartData.length === 0) return [0, 'auto'];

    const values = [];
    chartData.forEach((d) => {
      if (d.actual !== null && d.actual !== undefined) values.push(Number(d.actual));
      if (d.predicted !== null && d.predicted !== undefined) values.push(Number(d.predicted));
      if (showBounds && d.upper !== null && d.upper !== undefined) values.push(Number(d.upper));
      if (showBounds && d.lower !== null && d.lower !== undefined) values.push(Number(d.lower));
    });

    if (values.length === 0) return [0, 'auto'];

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const span = maxVal - minVal;

    // Minimum padding to guarantee vertical headroom & footroom
    const padding = Math.max(span * 0.15, maxVal * 0.08, 5);
    const lowerBound = Math.max(0, Math.floor(minVal - padding));
    const upperBound = Math.ceil(maxVal + padding);

    return [lowerBound, upperBound];
  }, [chartData, showBounds]);

  // First forecast date for vertical demarcation line
  const forecastStartDate = forecastRows?.[0]?.date;

  const freqLabel =
    frequency === 'D'
      ? 'Daily'
      : frequency === 'W'
      ? 'Weekly'
      : frequency === 'M'
      ? 'Monthly'
      : frequency;

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    const dataPt = payload[0]?.payload;
    const isForecast = dataPt?.type === 'forecast';

    return (
      <div className="rounded-xl border border-[#2e2e2e] bg-[#161616] p-3 shadow-lg text-xs space-y-1.5 min-w-[190px]">
        <div className="font-semibold text-neutral-200 border-b border-[#282828] pb-1 flex justify-between items-center">
          <span>{formatDate(label)}</span>
          <span
            className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
              isForecast ? 'bg-[#193228] text-emerald-400' : 'bg-[#222222] text-neutral-300'
            }`}
          >
            {isForecast ? 'Forecast' : 'Historical'}
          </span>
        </div>

        {dataPt?.actual !== null && dataPt?.actual !== undefined && (
          <div className="flex items-center justify-between text-neutral-300">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
              Actual Demand:
            </span>
            <span className="font-mono font-bold text-white">{formatNumber(dataPt.actual)} {units}</span>
          </div>
        )}

        {dataPt?.predicted !== null && dataPt?.predicted !== undefined && isForecast && (
          <div className="flex items-center justify-between text-blue-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
              Predicted Demand:
            </span>
            <span className="font-mono font-bold text-blue-300">{formatNumber(dataPt.predicted)} {units}</span>
          </div>
        )}

        {hasValidIntervals && showBounds && dataPt?.upper !== null && dataPt?.upper !== undefined && (
          <div className="text-[11px] text-neutral-400 pt-1 border-t border-[#282828] space-y-0.5">
            <div className="flex justify-between">
              <span>Upper (95% CI):</span>
              <span className="font-mono text-neutral-300">{formatNumber(dataPt.upper)}</span>
            </div>
            <div className="flex justify-between">
              <span>Lower (95% CI):</span>
              <span className="font-mono text-neutral-300">{formatNumber(dataPt.lower)}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Target Metadata Banner */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-lg bg-[#141414] border border-[#262626] text-xs text-neutral-300">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <Tag className="w-3.5 h-3.5" />
            {targetProduct ? `Product: ${targetProduct}` : 'Aggregate Total Demand'}
          </span>
          <span className="text-neutral-600">•</span>
          <span className="flex items-center gap-1 text-neutral-400">
            <Clock className="w-3.5 h-3.5 text-neutral-500" />
            Frequency: <strong className="text-neutral-300">{freqLabel}</strong>
          </span>
          <span className="text-neutral-600">•</span>
          <span className="flex items-center gap-1 text-neutral-400">
            <Calendar className="w-3.5 h-3.5 text-neutral-500" />
            Horizon: <strong className="text-neutral-300">{horizon} Periods</strong>
          </span>
          <span className="text-neutral-600">•</span>
          <span className="text-neutral-400">
            Units: <strong className="text-neutral-300">{units}</strong>
          </span>
        </div>

        <div>
          {hasValidIntervals ? (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#193228] text-emerald-400 border border-[#234b3c]">
              95% Prediction Bounds Active
            </span>
          ) : (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#222222] text-neutral-400">
              Point Estimate Only
            </span>
          )}
        </div>
      </div>

      {/* Chart Toolbar Controls */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center space-x-3 text-neutral-400">
          {recentHistory.length > 0 && (
            <div className={`flex items-center space-x-1.5 transition-opacity ${showHistorical ? 'opacity-100' : 'opacity-40'}`}>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block" />
              <span className={`text-neutral-300 ${!showHistorical ? 'line-through text-neutral-500' : ''}`}>
                Historical Observations
              </span>
            </div>
          )}
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            <span className="text-neutral-300">Predicted Horizon</span>
          </div>
          {hasValidIntervals && showBounds && (
            <div className="flex items-center space-x-1.5 text-neutral-400">
              <span className="w-2.5 h-2.5 rounded border border-blue-400/40 bg-blue-500/10 inline-block" />
              <span>95% Bounds</span>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {recentHistory.length > 0 && (
            <button
              onClick={() => setShowHistorical(!showHistorical)}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] border transition-colors cursor-pointer ${
                showHistorical
                  ? 'bg-[#222222] hover:bg-[#282828] text-neutral-200 border-[#333333]'
                  : 'bg-[#181818] hover:bg-[#222222] text-neutral-400 border-[#2a2a2a]'
              }`}
            >
              {showHistorical ? <Eye className="w-3 h-3 text-emerald-400" /> : <EyeOff className="w-3 h-3 text-neutral-500" />}
              <span>{showHistorical ? 'Hide History' : 'Show History'}</span>
            </button>
          )}

          {hasValidIntervals && (
            <button
              onClick={() => setShowBounds(!showBounds)}
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] border transition-colors cursor-pointer ${
                showBounds
                  ? 'bg-[#222222] hover:bg-[#282828] text-neutral-200 border-[#333333]'
                  : 'bg-[#181818] hover:bg-[#222222] text-neutral-400 border-[#2a2a2a]'
              }`}
            >
              {showBounds ? <Eye className="w-3 h-3 text-blue-400" /> : <EyeOff className="w-3 h-3 text-neutral-500" />}
              <span>{showBounds ? 'Hide Bounds' : 'Show Bounds'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Responsive Recharts View */}
      <div className="h-72 sm:h-80 w-full rounded-xl bg-[#141414] border border-[#262626] p-3">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            key={showHistorical ? 'with-history' : 'forecast-only'}
            data={chartData}
            margin={{ top: 20, right: 20, left: -10, bottom: 5 }}
          >
            <defs>
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              stroke={isDark ? '#262626' : '#e2e8f0'}
              vertical={false}
            />

            <XAxis
              dataKey="date"
              stroke={isDark ? '#737373' : '#64748b'}
              fontSize={11}
              tickLine={false}
              tickFormatter={(d) => {
                if (!d) return '';
                const parts = d.split('-');
                return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : d;
              }}
            />

            <YAxis
              stroke={isDark ? '#737373' : '#64748b'}
              fontSize={11}
              tickLine={false}
              domain={yDomain}
              tickFormatter={(v) => Number(v).toLocaleString()}
            />

            <Tooltip
              cursor={{
                stroke: isDark ? '#333333' : '#cbd5e1',
                strokeWidth: 1,
                strokeDasharray: '3 3',
              }}
              content={<CustomTooltip />}
            />

            {/* Demarcation line separating historical from forecast horizon */}
            {showHistorical && forecastStartDate && recentHistory.length > 0 && (
              <ReferenceLine
                x={forecastStartDate}
                stroke="#6366f1"
                strokeDasharray="4 4"
                label={{
                  value: 'Forecast Start',
                  position: 'insideTopLeft',
                  fill: isDark ? '#a5b4fc' : '#4f46e5',
                  fontSize: 10,
                  offset: 8,
                }}
              />
            )}

            {/* Historical Series */}
            {showHistorical && (
              <Area
                type="monotone"
                dataKey="actual"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#actualGradient)"
                name="Historical Demand"
                dot={{ r: 2.5, fill: '#10b981', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#34d399' }}
              />
            )}

            {/* Prediction Interval Bounds - Rendered ONLY if valid */}
            {hasValidIntervals && showBounds && (
              <>
                <Line
                  type="monotone"
                  dataKey="upper"
                  stroke="#60a5fa"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  dot={false}
                  name="Upper Bound (95%)"
                />
                <Line
                  type="monotone"
                  dataKey="lower"
                  stroke="#60a5fa"
                  strokeWidth={1}
                  strokeDasharray="3 3"
                  dot={false}
                  name="Lower Bound (95%)"
                />
              </>
            )}

            {/* Projected Forecast Series */}
            <Line
              type="monotone"
              dataKey="predicted"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={{ r: 3.5, fill: '#3b82f6', stroke: isDark ? '#1e3a8a' : '#ffffff', strokeWidth: 1.5 }}
              activeDot={{ r: 6, fill: '#60a5fa' }}
              name="Predicted Demand"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
