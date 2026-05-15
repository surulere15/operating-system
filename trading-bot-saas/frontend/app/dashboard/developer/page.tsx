'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import {
  Code,
  Key,
  Webhook,
  Plus,
  Copy,
  Trash2,
  Eye,
  EyeOff,
  Activity,
  Zap,
  CheckCircle,
  XCircle,
  BarChart3,
  AlertTriangle,
  Lock,
  Unlock
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface APIKey {
  id: number;
  name: string;
  key_prefix: string;
  can_read_data: boolean;
  can_execute_trades: boolean;
  can_manage_bots: boolean;
  rate_limit_per_minute: number;
  rate_limit_per_hour: number;
  total_requests: number;
  last_used_at: string | null;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
}

interface WebhookEndpoint {
  id: number;
  name: string;
  url: string;
  secret: string;
  listen_trade_signals: boolean;
  listen_price_alerts: boolean;
  listen_portfolio_updates: boolean;
  is_active: boolean;
  total_triggers: number;
  total_failures: number;
  last_triggered_at: string | null;
  created_at: string;
}

export default function DeveloperPage() {
  const router = useRouter();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateKeyModal, setShowCreateKeyModal] = useState(false);
  const [showCreateWebhookModal, setShowCreateWebhookModal] = useState(false);
  const [newKey, setNewKey] = useState({
    name: '',
    can_read_data: true,
    can_execute_trades: false,
    can_manage_bots: false
  });
  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    listen_trade_signals: true,
    listen_price_alerts: false,
    listen_portfolio_updates: false
  });
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [keysRes, webhooksRes] = await Promise.all([
        axios.get(`${API_URL}/api/developer/keys`, { headers }),
        axios.get(`${API_URL}/api/developer/webhooks`, { headers })
      ]);

      if (keysRes.data.success) {
        setApiKeys(keysRes.data.keys);
      }

      if (webhooksRes.data.success) {
        setWebhooks(webhooksRes.data.webhooks);
      }

    } catch (error: any) {
      console.error('Failed to fetch developer data:', error);
      if (error.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const createAPIKey = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/developer/keys`,
        {
          name: newKey.name,
          permissions: {
            can_read_data: newKey.can_read_data,
            can_execute_trades: newKey.can_execute_trades,
            can_manage_bots: newKey.can_manage_bots
          }
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setCreatedKey(response.data.api_key.key);
        fetchData();
      }
    } catch (error: any) {
      console.error('Failed to create API key:', error);
      alert(error.response?.data?.detail || 'Failed to create API key');
    }
  };

  const deleteAPIKey = async (keyId: number, keyName: string) => {
    if (!confirm(`Delete API key "${keyName}"? This cannot be undone.`)) return;

    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/developer/keys/${keyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('✅ API key deleted');
      fetchData();
    } catch (error: any) {
      console.error('Failed to delete API key:', error);
      alert(error.response?.data?.detail || 'Failed to delete API key');
    }
  };

  const createWebhook = async () => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/developer/webhooks`,
        newWebhook,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setCreatedSecret(response.data.webhook.secret);
        fetchData();
      }
    } catch (error: any) {
      console.error('Failed to create webhook:', error);
      alert(error.response?.data?.detail || 'Failed to create webhook');
    }
  };

  const deleteWebhook = async (webhookId: number, webhookName: string) => {
    if (!confirm(`Delete webhook "${webhookName}"?`)) return;

    try:
      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/developer/webhooks/${webhookId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('✅ Webhook deleted');
      fetchData();
    } catch (error: any) {
      console.error('Failed to delete webhook:', error);
      alert(error.response?.data?.detail || 'Failed to delete webhook');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('✅ Copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
            <p className="mt-4">Loading developer tools...</p>
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
          <div className="flex items-center gap-3 mb-2">
            <Code className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Developer API</h1>
          </div>
          <p className="text-gray-300">
            Programmatic access to your trading platform with webhooks and API keys
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Key className="w-4 h-4" />
              <span>API Keys</span>
            </div>
            <div className="text-2xl font-bold text-white">{apiKeys.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Webhook className="w-4 h-4" />
              <span>Webhooks</span>
            </div>
            <div className="text-2xl font-bold text-purple-400">{webhooks.length}</div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Activity className="w-4 h-4" />
              <span>Total Requests</span>
            </div>
            <div className="text-2xl font-bold text-blue-400">
              {apiKeys.reduce((sum, k) => sum + k.total_requests, 0).toLocaleString()}
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
              <Zap className="w-4 h-4" />
              <span>Webhook Triggers</span>
            </div>
            <div className="text-2xl font-bold text-green-400">
              {webhooks.reduce((sum, w) => sum + w.total_triggers, 0).toLocaleString()}
            </div>
          </div>
        </div>

        {/* API Keys Section */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-1">API Keys</h2>
              <p className="text-gray-400 text-sm">Generate keys for programmatic access</p>
            </div>
            <button
              onClick={() => setShowCreateKeyModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create Key
            </button>
          </div>

          {apiKeys.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Key className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No API keys created yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map(key => (
                <div key={key.id} className="p-4 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-white font-semibold mb-1">{key.name}</h3>
                      <div className="flex items-center gap-2">
                        <code className="text-sm text-gray-400 bg-black/30 px-2 py-1 rounded">
                          {key.key_prefix}...
                        </code>
                        {key.is_active ? (
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-semibold">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-500/20 text-gray-400 rounded text-xs font-semibold">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteAPIKey(key.id, key.name)}
                      className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-gray-400">Read Data:</span>
                      <span className="ml-2 text-white">
                        {key.can_read_data ? '✅' : '❌'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Execute Trades:</span>
                      <span className="ml-2 text-white">
                        {key.can_execute_trades ? '✅' : '❌'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Requests:</span>
                      <span className="ml-2 text-white">{key.total_requests.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Rate Limit:</span>
                      <span className="ml-2 text-white">{key.rate_limit_per_minute}/min</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Webhooks Section */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 mb-8 border border-white/10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-1">Webhooks</h2>
              <p className="text-gray-400 text-sm">Receive real-time event notifications</p>
            </div>
            <button
              onClick={() => setShowCreateWebhookModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create Webhook
            </button>
          </div>

          {webhooks.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Webhook className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No webhooks configured yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {webhooks.map(webhook => (
                <div key={webhook.id} className="p-4 bg-white/5 rounded-lg border border-white/10">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-white font-semibold mb-1">{webhook.name}</h3>
                      <div className="text-sm text-gray-400 mb-2">{webhook.url}</div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {webhook.listen_trade_signals && (
                          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                            Trade Signals
                          </span>
                        )}
                        {webhook.listen_price_alerts && (
                          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                            Price Alerts
                          </span>
                        )}
                        {webhook.listen_portfolio_updates && (
                          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">
                            Portfolio Updates
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteWebhook(webhook.id, webhook.name)}
                      className="p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                    <div>
                      <span className="text-gray-400">Triggers:</span>
                      <span className="ml-2 text-white">{webhook.total_triggers.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Failures:</span>
                      <span className="ml-2 text-red-400">{webhook.total_failures}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Success Rate:</span>
                      <span className="ml-2 text-green-400">
                        {webhook.total_triggers > 0
                          ? ((webhook.total_triggers - webhook.total_failures) / webhook.total_triggers * 100).toFixed(1)
                          : 0}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* API Documentation */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Code className="w-5 h-5 text-blue-400" />
            Quick Start Guide
          </h3>
          <div className="space-y-4 text-gray-300 text-sm">
            <div>
              <h4 className="text-white font-semibold mb-2">1. Authentication</h4>
              <code className="block bg-black/30 p-3 rounded text-xs overflow-x-auto">
                curl {API_URL}/api/bots \<br/>
                &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY"
              </code>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-2">2. Webhook Signature Verification</h4>
              <code className="block bg-black/30 p-3 rounded text-xs overflow-x-auto">
                const crypto = require('crypto');<br/>
                const signature = req.headers['x-webhook-signature'];<br/>
                const hash = crypto.createHmac('sha256', SECRET).update(JSON.stringify(req.body)).digest('hex');<br/>
                const isValid = signature === hash;
              </code>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-2">3. Example: Get Portfolio Data</h4>
              <code className="block bg-black/30 p-3 rounded text-xs overflow-x-auto">
                const response = await fetch('{API_URL}/api/risk/portfolio', {'{'}<br/>
                &nbsp;&nbsp;headers: {'{'} 'Authorization': 'Bearer YOUR_API_KEY' {'}'}<br/>
                {'}'});
              </code>
            </div>
          </div>
        </div>

        {/* Create API Key Modal */}
        {showCreateKeyModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-8 max-w-2xl w-full border border-white/20">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Create API Key</h2>
                <button
                  onClick={() => {
                    setShowCreateKeyModal(false);
                    setCreatedKey(null);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {createdKey ? (
                <div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 mb-6">
                    <div className="flex items-start gap-3 mb-4">
                      <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="text-green-400 font-semibold mb-2">API Key Created!</h3>
                        <p className="text-gray-300 text-sm mb-4">
                          Save this key now - it won't be shown again!
                        </p>
                        <div className="bg-black/30 p-4 rounded-lg">
                          <code className="text-green-400 text-sm break-all">{createdKey}</code>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(createdKey)}
                      className="w-full px-4 py-2 bg-green-500/20 text-green-400 rounded-lg font-semibold hover:bg-green-500/30 transition flex items-center justify-center gap-2"
                    >
                      <Copy className="w-4 h-4" />
                      Copy to Clipboard
                    </button>
                  </div>

                  <button
                    onClick={() => {
                      setShowCreateKeyModal(false);
                      setCreatedKey(null);
                      setNewKey({ name: '', can_read_data: true, can_execute_trades: false, can_manage_bots: false });
                    }}
                    className="w-full px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Key Name
                    </label>
                    <input
                      type="text"
                      value={newKey.name}
                      onChange={(e) => setNewKey({...newKey, name: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="e.g., Production API Key"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-white mb-3">
                      Permissions
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newKey.can_read_data}
                          onChange={(e) => setNewKey({...newKey, can_read_data: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <div className="flex-1">
                          <div className="text-white font-semibold">Read Data</div>
                          <div className="text-gray-400 text-xs">View bots, trades, and portfolio data</div>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newKey.can_execute_trades}
                          onChange={(e) => setNewKey({...newKey, can_execute_trades: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <div className="flex-1">
                          <div className="text-white font-semibold">Execute Trades</div>
                          <div className="text-gray-400 text-xs">Place and manage trades</div>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newKey.can_manage_bots}
                          onChange={(e) => setNewKey({...newKey, can_manage_bots: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <div className="flex-1">
                          <div className="text-white font-semibold">Manage Bots</div>
                          <div className="text-gray-400 text-xs">Create, update, and delete bots</div>
                        </div>
                      </label>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => setShowCreateKeyModal(false)}
                      className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={createAPIKey}
                      disabled={!newKey.name}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition disabled:opacity-50"
                    >
                      Generate Key
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Create Webhook Modal */}
        {showCreateWebhookModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-8 max-w-2xl w-full border border-white/20">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Create Webhook</h2>
                <button
                  onClick={() => {
                    setShowCreateWebhookModal(false);
                    setCreatedSecret(null);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {createdSecret ? (
                <div>
                  <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 mb-6">
                    <div className="flex items-start gap-3 mb-4">
                      <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h3 className="text-green-400 font-semibold mb-2">Webhook Created!</h3>
                        <p className="text-gray-300 text-sm mb-4">
                          Save this secret - use it to verify webhook signatures!
                        </p>
                        <div className="bg-black/30 p-4 rounded-lg">
                          <code className="text-green-400 text-sm break-all">{createdSecret}</code>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(createdSecret)}
                      className="w-full px-4 py-2 bg-green-500/20 text-green-400 rounded-lg font-semibold hover:bg-green-500/30 transition flex items-center justify-center gap-2"
                    >
                      <Copy className="w-4 h-4" />
                      Copy Secret
                    </button>
                  </div>

                  <button
                    onClick={() => {
                      setShowCreateWebhookModal(false);
                      setCreatedSecret(null);
                      setNewWebhook({ name: '', url: '', listen_trade_signals: true, listen_price_alerts: false, listen_portfolio_updates: false });
                    }}
                    className="w-full px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Webhook Name
                    </label>
                    <input
                      type="text"
                      value={newWebhook.name}
                      onChange={(e) => setNewWebhook({...newWebhook, name: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="e.g., Trade Signals Webhook"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={newWebhook.url}
                      onChange={(e) => setNewWebhook({...newWebhook, url: e.target.value})}
                      className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                      placeholder="https://your-server.com/webhook"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-white mb-3">
                      Event Types
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newWebhook.listen_trade_signals}
                          onChange={(e) => setNewWebhook({...newWebhook, listen_trade_signals: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <span className="text-white">Trade Signals</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newWebhook.listen_price_alerts}
                          onChange={(e) => setNewWebhook({...newWebhook, listen_price_alerts: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <span className="text-white">Price Alerts</span>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                        <input
                          type="checkbox"
                          checked={newWebhook.listen_portfolio_updates}
                          onChange={(e) => setNewWebhook({...newWebhook, listen_portfolio_updates: e.target.checked})}
                          className="w-5 h-5 rounded"
                        />
                        <span className="text-white">Portfolio Updates</span>
                      </label>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => setShowCreateWebhookModal(false)}
                      className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg font-semibold hover:bg-white/20 transition"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={createWebhook}
                      disabled={!newWebhook.name || !newWebhook.url}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-600 transition disabled:opacity-50"
                    >
                      Create Webhook
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
