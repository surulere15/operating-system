'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  Bell,
  Plus,
  Trash2,
  Power,
  TrendingUp,
  Activity,
  Target,
  BarChart3,
  Clock,
  Check,
  X,
  Mail,
  MessageCircle,
  Repeat,
  AlertCircle
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Alert {
  id: number;
  name: string;
  description: string;
  alert_type: string;
  symbol: string;
  condition: string;
  target_value: number;
  indicator: string;
  portfolio_metric: string;
  is_active: boolean;
  notify_email: boolean;
  notify_telegram: boolean;
  repeat: boolean;
  times_triggered: number;
  last_triggered_at: string | null;
  created_at: string;
}

interface AlertHistory {
  id: number;
  alert_id: number;
  triggered_at: string;
  trigger_value: number;
  message: string;
  notified_email: boolean;
  notified_telegram: boolean;
}

const ALERT_TYPES = [
  { value: 'price', label: 'Price Alert', icon: TrendingUp, description: 'Alert on price movements' },
  { value: 'indicator', label: 'Indicator Alert', icon: BarChart3, description: 'Alert on technical indicators' },
  { value: 'portfolio', label: 'Portfolio Alert', icon: Target, description: 'Alert on portfolio metrics' }
];

const CONDITIONS = {
  price: [
    { value: 'above', label: 'Above' },
    { value: 'below', label: 'Below' },
    { value: 'crosses_above', label: 'Crosses Above' },
    { value: 'crosses_below', label: 'Crosses Below' },
    { value: 'change_percent', label: 'Change %' }
  ],
  indicator: [
    { value: 'above', label: 'Above' },
    { value: 'below', label: 'Below' }
  ],
  portfolio: [
    { value: 'above', label: 'Above' },
    { value: 'below', label: 'Below' }
  ]
};

const INDICATORS = [
  { value: 'rsi', label: 'RSI' },
  { value: 'macd', label: 'MACD' },
  { value: 'ma', label: 'Moving Average' },
  { value: 'ema', label: 'EMA' }
];

const PORTFOLIO_METRICS = [
  { value: 'total_pnl', label: 'Total P&L' },
  { value: 'risk_score', label: 'Risk Score' },
  { value: 'current_drawdown_percent', label: 'Drawdown %' },
  { value: 'total_exposure', label: 'Total Exposure' }
];

export default function AlertsPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<AlertHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAlert, setNewAlert] = useState({
    name: '',
    description: '',
    alert_type: 'price',
    symbol: 'BTCUSDT',
    condition: 'above',
    target_value: 0,
    indicator: 'rsi',
    portfolio_metric: 'total_pnl',
    notify_email: true,
    notify_telegram: false,
    repeat: false
  });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchAlerts();
    fetchHistory();
  }, []);

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/alerts`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setAlerts(response.data.alerts);
      }
    } catch (error: any) {
      console.error('Failed to fetch alerts:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/alerts/history?limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setHistory(response.data.history);
      }
    } catch (error: any) {
      console.error('Failed to fetch history:', error);
    }
  };

  const createAlert = async () => {
    setCreating(true);
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/alerts`,
        newAlert,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        alert('✅ Alert created successfully!');
        setShowCreateModal(false);
        resetForm();
        fetchAlerts();
      }
    } catch (error: any) {
      console.error('Failed to create alert:', error);
      alert(error.response?.data?.detail || 'Failed to create alert');
    } finally {
      setCreating(false);
    }
  };

  const deleteAlert = async (alertId: number, alertName: string) => {
    if (!confirm(`Delete alert "${alertName}"?`)) return;

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/alerts/${alertId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('✅ Alert deleted');
      fetchAlerts();
    } catch (error: any) {
      console.error('Failed to delete alert:', error);
      alert(error.response?.data?.detail || 'Failed to delete alert');
    }
  };

  const toggleAlert = async (alertId: number) => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      await axios.post(
        `${API_URL}/api/alerts/${alertId}/toggle`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      fetchAlerts();
    } catch (error: any) {
      console.error('Failed to toggle alert:', error);
      alert(error.response?.data?.detail || 'Failed to toggle alert');
    }
  };

  const resetForm = () => {
    setNewAlert({
      name: '',
      description: '',
      alert_type: 'price',
      symbol: 'BTCUSDT',
      condition: 'above',
      target_value: 0,
      indicator: 'rsi',
      portfolio_metric: 'total_pnl',
      notify_email: true,
      notify_telegram: false,
      repeat: false
    });
  };

  const getAlertTypeIcon = (type: string) => {
    const typeData = ALERT_TYPES.find(t => t.value === type);
    const Icon = typeData?.icon || Bell;
    return <Icon className="w-5 h-5" />;
  };

  const getConditionLabel = (condition: string) => {
    return condition.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading alerts...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Bell className="w-8 h-8 text-purple-400" />
              <h1 className="text-3xl font-bold text-white">Custom Alerts</h1>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create Alert
            </button>
          </div>
          <p className="text-gray-300">
            Set custom price, indicator, and portfolio alerts with multi-channel notifications
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Bell className="w-4 h-4" />
              <span>Total Alerts</span>
            </div>
            <div className="text-2xl font-bold text-white">{alerts.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Power className="w-4 h-4" />
              <span>Active</span>
            </div>
            <div className="text-2xl font-bold text-green-400">
              {alerts.filter(a => a.is_active).length}
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Activity className="w-4 h-4" />
              <span>Triggered</span>
            </div>
            <div className="text-2xl font-bold text-purple-400">
              {alerts.reduce((sum, a) => sum + a.times_triggered, 0)}
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Clock className="w-4 h-4" />
              <span>Recent</span>
            </div>
            <div className="text-2xl font-bold text-blue-400">{history.length}</div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
          <h2 className="text-xl font-bold text-white mb-4">My Alerts</h2>

          {alerts.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Bell className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="mb-4">No alerts created yet</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition"
              >
                Create Your First Alert
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.map(alert => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border transition ${
                    alert.is_active
                      ? 'bg-white/5 border-purple-500/30'
                      : 'bg-gray-800/30 border-gray-700/30 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className={`p-2 rounded-lg ${
                          alert.is_active ? 'bg-purple-500/20' : 'bg-gray-700/20'
                        }`}>
                          {getAlertTypeIcon(alert.alert_type)}
                          <span className={alert.is_active ? 'text-purple-400' : 'text-gray-500'}>
                            {/* Icon already rendered */}
                          </span>
                        </div>
                        <div>
                          <h3 className="text-white font-semibold">{alert.name}</h3>
                          <p className="text-gray-400 text-sm">{alert.description || 'No description'}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                        <div className="text-sm">
                          <span className="text-gray-400">Type:</span>
                          <span className="text-white ml-2 capitalize">{alert.alert_type}</span>
                        </div>
                        {alert.symbol && (
                          <div className="text-sm">
                            <span className="text-gray-400">Symbol:</span>
                            <span className="text-white ml-2">{alert.symbol}</span>
                          </div>
                        )}
                        <div className="text-sm">
                          <span className="text-gray-400">Condition:</span>
                          <span className="text-white ml-2">{getConditionLabel(alert.condition)}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-400">Target:</span>
                          <span className="text-white ml-2">{alert.target_value}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 mt-3">
                        {alert.notify_email && (
                          <div className="flex items-center gap-1 text-blue-400 text-sm">
                            <Mail className="w-4 h-4" />
                            <span>Email</span>
                          </div>
                        )}
                        {alert.notify_telegram && (
                          <div className="flex items-center gap-1 text-green-400 text-sm">
                            <MessageCircle className="w-4 h-4" />
                            <span>Telegram</span>
                          </div>
                        )}
                        {alert.repeat && (
                          <div className="flex items-center gap-1 text-purple-400 text-sm">
                            <Repeat className="w-4 h-4" />
                            <span>Repeating</span>
                          </div>
                        )}
                        {alert.times_triggered > 0 && (
                          <div className="flex items-center gap-1 text-yellow-400 text-sm">
                            <Activity className="w-4 h-4" />
                            <span>Triggered {alert.times_triggered}x</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => toggleAlert(alert.id)}
                        className={`p-2 rounded-lg transition ${
                          alert.is_active
                            ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                            : 'bg-gray-700/20 text-gray-500 hover:bg-gray-700/30'
                        }`}
                        title={alert.is_active ? 'Disable' : 'Enable'}
                      >
                        <Power className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => deleteAlert(alert.id, alert.name)}
                        className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
                        title="Delete"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Alert History */}
        {history.length > 0 && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-bold text-white mb-4">Recent Triggers</h2>

            <div className="space-y-3">
              {history.map(h => (
                <div key={h.id} className="p-4 bg-white/5 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-white font-semibold">{h.message}</div>
                    <div className="text-gray-400 text-sm">
                      {new Date(h.triggered_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <div className="text-gray-400">
                      Value: <span className="text-white">{h.trigger_value}</span>
                    </div>
                    {h.notified_email && (
                      <div className="flex items-center gap-1 text-blue-400">
                        <Mail className="w-3 h-3" />
                        <span>Sent</span>
                      </div>
                    )}
                    {h.notified_telegram && (
                      <div className="flex items-center gap-1 text-green-400">
                        <MessageCircle className="w-3 h-3" />
                        <span>Sent</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Create Alert Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-white/20">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Create New Alert</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {/* Form */}
              <div className="space-y-6">
                {/* Name */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Alert Name
                  </label>
                  <input
                    type="text"
                    value={newAlert.name}
                    onChange={(e) => setNewAlert({...newAlert, name: e.target.value})}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., BTC above $50k"
                  />
                </div>

                {/* Alert Type */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Alert Type
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {ALERT_TYPES.map(type => {
                      const Icon = type.icon;
                      return (
                        <button
                          key={type.value}
                          onClick={() => setNewAlert({...newAlert, alert_type: type.value})}
                          className={`p-4 rounded-lg border-2 transition ${
                            newAlert.alert_type === type.value
                              ? 'border-purple-500 bg-purple-500/20'
                              : 'border-white/20 bg-white/5 hover:bg-white/10'
                          }`}
                        >
                          <Icon className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                          <div className="text-white text-sm font-semibold">{type.label}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Symbol (for price alerts) */}
                {newAlert.alert_type === 'price' && (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Symbol
                    </label>
                    <input
                      type="text"
                      value={newAlert.symbol}
                      onChange={(e) => setNewAlert({...newAlert, symbol: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="BTCUSDT"
                    />
                  </div>
                )}

                {/* Indicator (for indicator alerts) */}
                {newAlert.alert_type === 'indicator' && (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Indicator
                    </label>
                    <select
                      value={newAlert.indicator}
                      onChange={(e) => setNewAlert({...newAlert, indicator: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {INDICATORS.map(ind => (
                        <option key={ind.value} value={ind.value} className="bg-gray-800">
                          {ind.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Portfolio Metric (for portfolio alerts) */}
                {newAlert.alert_type === 'portfolio' && (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Portfolio Metric
                    </label>
                    <select
                      value={newAlert.portfolio_metric}
                      onChange={(e) => setNewAlert({...newAlert, portfolio_metric: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {PORTFOLIO_METRICS.map(metric => (
                        <option key={metric.value} value={metric.value} className="bg-gray-800">
                          {metric.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Condition */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Condition
                  </label>
                  <select
                    value={newAlert.condition}
                    onChange={(e) => setNewAlert({...newAlert, condition: e.target.value})}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {CONDITIONS[newAlert.alert_type as keyof typeof CONDITIONS]?.map(cond => (
                      <option key={cond.value} value={cond.value} className="bg-gray-800">
                        {cond.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target Value */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-2">
                    Target Value
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={newAlert.target_value}
                    onChange={(e) => setNewAlert({...newAlert, target_value: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="0"
                  />
                </div>

                {/* Notifications */}
                <div>
                  <label className="block text-sm font-semibold text-white mb-3">
                    Notifications
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                      <input
                        type="checkbox"
                        checked={newAlert.notify_email}
                        onChange={(e) => setNewAlert({...newAlert, notify_email: e.target.checked})}
                        className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-purple-500"
                      />
                      <Mail className="w-5 h-5 text-blue-400" />
                      <span className="text-white">Email Notification</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                      <input
                        type="checkbox"
                        checked={newAlert.notify_telegram}
                        onChange={(e) => setNewAlert({...newAlert, notify_telegram: e.target.checked})}
                        className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-purple-500"
                      />
                      <MessageCircle className="w-5 h-5 text-green-400" />
                      <span className="text-white">Telegram Notification</span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                      <input
                        type="checkbox"
                        checked={newAlert.repeat}
                        onChange={(e) => setNewAlert({...newAlert, repeat: e.target.checked})}
                        className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-purple-500"
                      />
                      <Repeat className="w-5 h-5 text-purple-400" />
                      <span className="text-white">Repeat (trigger multiple times)</span>
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4 pt-4">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createAlert}
                    disabled={creating || !newAlert.name}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creating ? 'Creating...' : 'Create Alert'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
