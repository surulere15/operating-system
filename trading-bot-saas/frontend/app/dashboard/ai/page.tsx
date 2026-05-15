'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Brain, TrendingUp, TrendingDown, Target, Activity, AlertTriangle, BarChart3, Sparkles, RefreshCw, ChevronRight } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Sentiment {
  symbol: string;
  sentiment_score: number;
  sentiment_label: string;
  sentiment_emoji: string;
  win_rate: number;
  avg_pnl: number;
  momentum: number;
  total_trades_analyzed: number;
  timestamp: string;
}

interface Signal {
  signal: string;
  action: string;
  confidence: number;
  reason: string;
}

interface Prediction {
  symbol: string;
  timeframe: string;
  current_price: number;
  predicted_price: number;
  predicted_change_percent: number;
  direction: string;
  confidence: number;
  price_range: {
    lower: number;
    upper: number;
  };
  volatility: number;
  timestamp: string;
}

interface MarketOverview {
  portfolio_summary: {
    total_pnl: number;
    win_rate: number;
    symbols_tracked: number;
    total_trades: number;
  };
  symbol_insights: Array<{
    symbol: string;
    sentiment: Sentiment;
    signals: Signal[];
    recommendations: string[];
  }>;
  overall_recommendation: string;
  timestamp: string;
}

export default function AIAnalysisPage() {
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [timeframe, setTimeframe] = useState<string>('24h');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchMarketOverview();
  }, []);

  const fetchMarketOverview = async () => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/ai/market-overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOverview(response.data.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch market overview:', error);
      setLoading(false);
    } finally {
      setRefreshing(false);
    }
  };

  const fetchPrediction = async (symbol: string, tf: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_URL}/api/ai/predict/${encodeURIComponent(symbol)}?timeframe=${tf}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPrediction(response.data.prediction);
    } catch (error) {
      console.error('Failed to fetch prediction:', error);
    }
  };

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    fetchPrediction(symbol, timeframe);
  };

  const handleTimeframeChange = (tf: string) => {
    setTimeframe(tf);
    if (selectedSymbol) {
      fetchPrediction(selectedSymbol, tf);
    }
  };

  const getSentimentColor = (score: number) => {
    if (score >= 70) return 'text-green-500 bg-green-500/10';
    if (score >= 60) return 'text-blue-500 bg-blue-500/10';
    if (score >= 40) return 'text-gray-500 bg-gray-500/10';
    if (score >= 30) return 'text-orange-500 bg-orange-500/10';
    return 'text-red-500 bg-red-500/10';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-500';
    if (confidence >= 60) return 'text-blue-500';
    if (confidence >= 40) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const getDirectionIcon = (direction: string) => {
    if (direction === 'up') return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (direction === 'down') return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Activity className="w-5 h-5 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
        <div className="text-center">
          <Brain className="w-16 h-16 text-blue-600 mx-auto animate-pulse" />
          <p className="mt-4 text-gray-600">Analyzing market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">AI Market Analysis</h1>
                <p className="text-gray-600">
                  AI-powered insights, predictions, and trading signals
                </p>
              </div>
            </div>
            <button
              onClick={fetchMarketOverview}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Portfolio Summary */}
        {overview?.portfolio_summary && (
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 mb-8 text-white">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-6 h-6" />
              <h2 className="text-2xl font-bold">Portfolio Overview</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-blue-100 text-sm mb-1">Total P&L</p>
                <p className="text-2xl font-bold">
                  ${overview.portfolio_summary.total_pnl.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-blue-100 text-sm mb-1">Win Rate</p>
                <p className="text-2xl font-bold">
                  {overview.portfolio_summary.win_rate.toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-blue-100 text-sm mb-1">Symbols Tracked</p>
                <p className="text-2xl font-bold">
                  {overview.portfolio_summary.symbols_tracked}
                </p>
              </div>
              <div>
                <p className="text-blue-100 text-sm mb-1">Total Trades</p>
                <p className="text-2xl font-bold">
                  {overview.portfolio_summary.total_trades}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Overall Recommendation */}
        {overview?.overall_recommendation && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8 border-l-4 border-blue-600">
            <div className="flex items-start gap-3">
              <Target className="w-6 h-6 text-blue-600 mt-1" />
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">AI Recommendation</h3>
                <p className="text-gray-700">{overview.overall_recommendation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Symbol Insights */}
        {overview?.symbol_insights && overview.symbol_insights.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Symbol Analysis</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {overview.symbol_insights.map((insight) => (
                <div
                  key={insight.symbol}
                  className="bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer hover:shadow-xl transition-shadow"
                  onClick={() => handleSymbolSelect(insight.symbol)}
                >
                  <div className="p-6">
                    {/* Symbol Header */}
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-900">{insight.symbol}</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{insight.sentiment.sentiment_emoji}</span>
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      </div>
                    </div>

                    {/* Sentiment Score */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-600">Sentiment</span>
                        <span className={`text-sm font-bold ${getSentimentColor(insight.sentiment.sentiment_score)} px-3 py-1 rounded-full`}>
                          {insight.sentiment.sentiment_label}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full transition-all"
                          style={{ width: `${insight.sentiment.sentiment_score}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>Bearish</span>
                        <span className="font-semibold">{insight.sentiment.sentiment_score.toFixed(0)}/100</span>
                        <span>Bullish</span>
                      </div>
                    </div>

                    {/* Key Metrics */}
                    <div className="grid grid-cols-3 gap-3 mb-4">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-600 mb-1">Win Rate</p>
                        <p className="text-lg font-bold text-gray-900">
                          {insight.sentiment.win_rate.toFixed(1)}%
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-600 mb-1">Avg P&L</p>
                        <p className={`text-lg font-bold ${insight.sentiment.avg_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ${insight.sentiment.avg_pnl.toFixed(2)}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-600 mb-1">Momentum</p>
                        <p className={`text-lg font-bold ${insight.sentiment.momentum >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {insight.sentiment.momentum >= 0 ? '+' : ''}{insight.sentiment.momentum.toFixed(1)}%
                        </p>
                      </div>
                    </div>

                    {/* Trading Signals */}
                    {insight.signals.length > 0 && (
                      <div className="mb-4">
                        <p className="text-sm font-semibold text-gray-900 mb-2">
                          Trading Signals ({insight.signals.length})
                        </p>
                        <div className="space-y-2">
                          {insight.signals.slice(0, 2).map((signal, idx) => (
                            <div
                              key={idx}
                              className="flex items-start gap-2 bg-gray-50 rounded-lg p-3"
                            >
                              <AlertTriangle className={`w-4 h-4 mt-0.5 ${getConfidenceColor(signal.confidence)}`} />
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs font-semibold text-gray-900">
                                    {signal.signal.replace(/_/g, ' ')}
                                  </span>
                                  <span className={`text-xs font-bold ${getConfidenceColor(signal.confidence)}`}>
                                    {signal.confidence}%
                                  </span>
                                </div>
                                <p className="text-xs text-gray-600">{signal.reason}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {insight.recommendations.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-gray-900 mb-2">AI Recommendations</p>
                        <ul className="space-y-1">
                          {insight.recommendations.slice(0, 2).map((rec, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                              <span className="text-blue-600 mt-1">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Price Prediction Panel */}
        {selectedSymbol && prediction && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-blue-600" />
                <h2 className="text-2xl font-bold text-gray-900">
                  Price Prediction: {selectedSymbol}
                </h2>
              </div>
              <div className="flex gap-2">
                {['1h', '4h', '24h', '7d'].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => handleTimeframeChange(tf)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      timeframe === tf
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Current vs Predicted */}
              <div>
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6">
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-1">Current Price</p>
                    <p className="text-3xl font-bold text-gray-900">
                      ${prediction.current_price.toFixed(2)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 mb-4">
                    {getDirectionIcon(prediction.direction)}
                    <div>
                      <p className="text-sm text-gray-600">Predicted Price ({timeframe})</p>
                      <p className="text-2xl font-bold text-blue-600">
                        ${prediction.predicted_price.toFixed(2)}
                      </p>
                    </div>
                  </div>
                  <div className={`text-2xl font-bold ${
                    prediction.predicted_change_percent >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {prediction.predicted_change_percent >= 0 ? '+' : ''}
                    {prediction.predicted_change_percent.toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* Confidence & Range */}
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">Confidence Level</span>
                    <span className={`text-lg font-bold ${getConfidenceColor(prediction.confidence)}`}>
                      {prediction.confidence.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-orange-500 to-green-500 h-2 rounded-full"
                      style={{ width: `${prediction.confidence}%` }}
                    />
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-600 mb-3">Predicted Range</p>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Upper Bound</span>
                      <span className="font-semibold text-gray-900">
                        ${prediction.price_range.upper.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Lower Bound</span>
                      <span className="font-semibold text-gray-900">
                        ${prediction.price_range.lower.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Volatility</span>
                    <span className="text-lg font-bold text-gray-900">
                      {prediction.volatility.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!overview || overview.symbol_insights.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No Trading Data Yet
            </h3>
            <p className="text-gray-600 mb-4">
              Start trading to receive AI-powered market insights and predictions
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
