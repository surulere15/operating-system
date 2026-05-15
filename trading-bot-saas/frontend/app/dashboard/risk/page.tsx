'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  Shield,
  AlertTriangle,
  TrendingDown,
  Activity,
  Target,
  BarChart3,
  CheckCircle,
  XCircle,
  Info,
  Zap,
  DollarSign,
  Percent,
  Award
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RiskMetrics {
  total_value: number;
  total_invested: number;
  total_pnl: number;
  value_at_risk_95: number;
  value_at_risk_99: number;
  conditional_var_95: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  current_drawdown: number;
  current_drawdown_percent: number;
  risk_score: number;
  risk_level: string;
  total_exposure: number;
  exposure_by_exchange: Record<string, number>;
  exposure_by_symbol: Record<string, number>;
  total_trades: number;
  active_bots: number;
}

interface CorrelationData {
  correlation_matrix: Record<string, Record<string, number>>;
  symbols: string[];
  diversification_score: number;
}

export default function RiskManagementPage() {
  const router = useRouter();
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [correlationData, setCorrelationData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRiskData();
  }, []);

  const fetchRiskData = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [riskRes, correlationRes] = await Promise.all([
        axios.get(`${API_URL}/api/risk/portfolio`, { headers }),
        axios.get(`${API_URL}/api/risk/correlation`, { headers })
      ]);

      if (riskRes.data.success) {
        setRiskMetrics(riskRes.data.risk_metrics);
      }

      if (correlationRes.data.success) {
        setCorrelationData(correlationRes.data.correlation);
      }

    } catch (error: any) {
      console.error('Failed to fetch risk data:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'very low':
        return 'text-green-400 bg-green-500/20';
      case 'low':
        return 'text-blue-400 bg-blue-500/20';
      case 'moderate':
        return 'text-yellow-400 bg-yellow-500/20';
      case 'high':
        return 'text-orange-400 bg-orange-500/20';
      case 'very high':
        return 'text-red-400 bg-red-500/20';
      default:
        return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score < 20) return 'text-green-400';
    if (score < 40) return 'text-blue-400';
    if (score < 60) return 'text-yellow-400';
    if (score < 80) return 'text-orange-400';
    return 'text-red-400';
  };

  const getCorrelationColor = (correlation: number) => {
    const abs_corr = Math.abs(correlation);
    if (abs_corr > 0.7) return 'bg-red-500/20 text-red-400';
    if (abs_corr > 0.4) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-green-500/20 text-green-400';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading risk analysis...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!riskMetrics) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Risk Management</h1>
          </div>
          <p className="text-gray-300">
            Institutional-grade portfolio risk analysis and monitoring
          </p>
        </div>

        {/* Risk Score Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-8 mb-8 border border-white/10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-2">Portfolio Risk Score</h2>
              <p className="text-gray-400 text-sm">
                Comprehensive risk assessment (0-100, lower is better)
              </p>
            </div>
            <div className={`px-6 py-3 rounded-xl font-bold text-2xl ${getRiskLevelColor(riskMetrics.risk_level)}`}>
              {riskMetrics.risk_level}
            </div>
          </div>

          <div className="relative">
            {/* Progress Bar */}
            <div className="w-full h-8 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${
                  riskMetrics.risk_score < 20 ? 'bg-green-500' :
                  riskMetrics.risk_score < 40 ? 'bg-blue-500' :
                  riskMetrics.risk_score < 60 ? 'bg-yellow-500' :
                  riskMetrics.risk_score < 80 ? 'bg-orange-500' :
                  'bg-red-500'
                }`}
                style={{ width: `${riskMetrics.risk_score}%` }}
              />
            </div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-2xl font-bold ${getRiskScoreColor(riskMetrics.risk_score)}`}>
                {riskMetrics.risk_score.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
            <div className="text-center">
              <div className="text-gray-400 text-xs mb-1">Very Low</div>
              <div className="text-green-400 font-semibold">0-20</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-xs mb-1">Low</div>
              <div className="text-blue-400 font-semibold">20-40</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-xs mb-1">Moderate</div>
              <div className="text-yellow-400 font-semibold">40-60</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-xs mb-1">High</div>
              <div className="text-orange-400 font-semibold">60-80</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400 text-xs mb-1">Very High</div>
              <div className="text-red-400 font-semibold">80-100</div>
            </div>
          </div>
        </div>

        {/* Value at Risk (VaR) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold">VaR 95%</h3>
                <p className="text-gray-400 text-xs">Maximum expected loss (95% confidence)</p>
              </div>
            </div>
            <div className="text-3xl font-bold text-red-400">
              ${riskMetrics.value_at_risk_95.toFixed(2)}
            </div>
            <p className="text-gray-400 text-sm mt-2">
              95% chance loss won't exceed this amount
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-600/20 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <h3 className="text-white font-semibold">VaR 99%</h3>
                <p className="text-gray-400 text-xs">Maximum expected loss (99% confidence)</p>
              </div>
            </div>
            <div className="text-3xl font-bold text-red-500">
              ${riskMetrics.value_at_risk_99.toFixed(2)}
            </div>
            <p className="text-gray-400 text-sm mt-2">
              99% chance loss won't exceed this amount
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <TrendingDown className="w-6 h-6 text-orange-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold">CVaR 95%</h3>
                <p className="text-gray-400 text-xs">Expected tail loss</p>
              </div>
            </div>
            <div className="text-3xl font-bold text-orange-400">
              ${riskMetrics.conditional_var_95.toFixed(2)}
            </div>
            <p className="text-gray-400 text-sm mt-2">
              Average loss when VaR is breached
            </p>
          </div>
        </div>

        {/* Risk-Adjusted Returns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-400" />
              Risk-Adjusted Returns
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <div className="text-gray-400 text-sm mb-1">Sharpe Ratio</div>
                  <p className="text-xs text-gray-500">Return per unit of total risk</p>
                </div>
                <div className={`text-2xl font-bold ${
                  riskMetrics.sharpe_ratio > 2 ? 'text-green-400' :
                  riskMetrics.sharpe_ratio > 1 ? 'text-blue-400' :
                  riskMetrics.sharpe_ratio > 0 ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {riskMetrics.sharpe_ratio.toFixed(2)}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <div className="text-gray-400 text-sm mb-1">Sortino Ratio</div>
                  <p className="text-xs text-gray-500">Return per unit of downside risk</p>
                </div>
                <div className={`text-2xl font-bold ${
                  riskMetrics.sortino_ratio > 2 ? 'text-green-400' :
                  riskMetrics.sortino_ratio > 1 ? 'text-blue-400' :
                  riskMetrics.sortino_ratio > 0 ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {riskMetrics.sortino_ratio.toFixed(2)}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <div className="text-gray-400 text-sm mb-1">Volatility</div>
                  <p className="text-xs text-gray-500">Standard deviation of returns</p>
                </div>
                <div className="text-2xl font-bold text-purple-400">
                  ${riskMetrics.volatility.toFixed(2)}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-red-400" />
              Drawdown Analysis
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <div className="text-gray-400 text-sm mb-1">Maximum Drawdown</div>
                  <p className="text-xs text-gray-500">Largest peak-to-trough decline</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-red-400">
                    ${riskMetrics.max_drawdown.toFixed(2)}
                  </div>
                  <div className="text-sm text-red-400">
                    {riskMetrics.max_drawdown_percent.toFixed(2)}%
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                <div>
                  <div className="text-gray-400 text-sm mb-1">Current Drawdown</div>
                  <p className="text-xs text-gray-500">Active decline from peak</p>
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${
                    riskMetrics.current_drawdown_percent > 15 ? 'text-red-400' :
                    riskMetrics.current_drawdown_percent > 10 ? 'text-orange-400' :
                    riskMetrics.current_drawdown_percent > 5 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    ${riskMetrics.current_drawdown.toFixed(2)}
                  </div>
                  <div className={`text-sm ${
                    riskMetrics.current_drawdown_percent > 15 ? 'text-red-400' :
                    riskMetrics.current_drawdown_percent > 10 ? 'text-orange-400' :
                    riskMetrics.current_drawdown_percent > 5 ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {riskMetrics.current_drawdown_percent.toFixed(2)}%
                  </div>
                </div>
              </div>

              {riskMetrics.current_drawdown_percent > 10 && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-400">
                    <strong>Warning:</strong> Current drawdown exceeds 10%. Consider reducing risk exposure.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Exposure Analysis */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
          <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Position Exposure
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="p-4 bg-white/5 rounded-lg">
              <div className="text-gray-400 text-sm mb-2">Total Exposure</div>
              <div className="text-2xl font-bold text-white mb-1">
                ${riskMetrics.total_exposure.toFixed(2)}
              </div>
              <div className="text-sm text-gray-400">
                {((riskMetrics.total_exposure / riskMetrics.total_value) * 100).toFixed(1)}x leverage
              </div>
            </div>

            <div className="p-4 bg-white/5 rounded-lg">
              <div className="text-gray-400 text-sm mb-2">Active Bots</div>
              <div className="text-2xl font-bold text-purple-400">
                {riskMetrics.active_bots}
              </div>
            </div>

            <div className="p-4 bg-white/5 rounded-lg">
              <div className="text-gray-400 text-sm mb-2">Total Trades</div>
              <div className="text-2xl font-bold text-blue-400">
                {riskMetrics.total_trades}
              </div>
            </div>
          </div>

          {Object.keys(riskMetrics.exposure_by_exchange).length > 0 && (
            <div className="mb-6">
              <h4 className="text-white font-semibold mb-3">By Exchange</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(riskMetrics.exposure_by_exchange).map(([exchange, exposure]) => (
                  <div key={exchange} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                    <span className="text-gray-300 text-sm">{exchange.toUpperCase()}</span>
                    <span className="text-white font-semibold">${exposure.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Object.keys(riskMetrics.exposure_by_symbol).length > 0 && (
            <div>
              <h4 className="text-white font-semibold mb-3">By Symbol</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(riskMetrics.exposure_by_symbol).slice(0, 6).map(([symbol, exposure]) => (
                  <div key={symbol} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                    <span className="text-gray-300 text-sm">{symbol}</span>
                    <span className="text-white font-semibold">${exposure.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Correlation Matrix */}
        {correlationData && correlationData.symbols.length >= 2 && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-white font-semibold mb-1 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-green-400" />
                  Portfolio Diversification
                </h3>
                <p className="text-gray-400 text-sm">Correlation matrix for risk diversification</p>
              </div>
              <div className="text-right">
                <div className="text-gray-400 text-sm mb-1">Diversification Score</div>
                <div className={`text-3xl font-bold ${
                  correlationData.diversification_score > 70 ? 'text-green-400' :
                  correlationData.diversification_score > 40 ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {correlationData.diversification_score.toFixed(0)}%
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="p-2 text-gray-400 text-sm"></th>
                    {correlationData.symbols.map(symbol => (
                      <th key={symbol} className="p-2 text-gray-300 text-sm font-semibold">
                        {symbol}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {correlationData.symbols.map(sym1 => (
                    <tr key={sym1}>
                      <td className="p-2 text-gray-300 text-sm font-semibold">{sym1}</td>
                      {correlationData.symbols.map(sym2 => {
                        const correlation = correlationData.correlation_matrix[sym1]?.[sym2] || 0;
                        return (
                          <td key={sym2} className="p-2">
                            <div className={`px-2 py-1 rounded text-center text-sm font-semibold ${getCorrelationColor(correlation)}`}>
                              {correlation.toFixed(2)}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-gray-300">
                  <strong className="text-blue-400">Interpretation:</strong> Values close to +1 or -1 indicate high correlation (similar movement).
                  Values near 0 indicate low correlation (diversification). Green = well diversified, Red = highly correlated.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Info Card */}
        <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
            <div>
              <h4 className="text-purple-400 font-semibold mb-2">Institutional-Grade Risk Management</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• <strong>VaR (Value at Risk):</strong> Measures maximum expected loss at given confidence levels</li>
                <li>• <strong>Sharpe Ratio:</strong> Return per unit of risk (>1 is good, >2 is excellent)</li>
                <li>• <strong>Sortino Ratio:</strong> Like Sharpe but focuses on downside risk</li>
                <li>• <strong>Correlation Matrix:</strong> Identifies portfolio diversification opportunities</li>
                <li>• <strong>Drawdown:</strong> Measures decline from portfolio peak</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
