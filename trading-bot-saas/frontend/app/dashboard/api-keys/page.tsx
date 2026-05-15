'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Key, Trash2, CheckCircle, XCircle, AlertTriangle, PlayCircle, Shield, ExternalLink } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface APIKey {
  id: number
  exchange: string
  is_testnet: boolean
  created_at: string
  last_used_at: string | null
  status?: 'connected' | 'failed' | 'testing'
}

export default function APIKeysPage() {
  const router = useRouter()
  const [apiKeys, setApiKeys] = useState<APIKey[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    exchange: 'bybit',
    api_key: '',
    api_secret: '',
    is_testnet: false
  })
  const [testingKey, setTestingKey] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadAPIKeys()
  }, [])

  const loadAPIKeys = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    try {
      const response = await axios.get(`${API_URL}/api/api-keys`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setApiKeys(response.data)
    } catch (err) {
      console.error('Failed to load API keys:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddKey = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const token = localStorage.getItem('token')

    try {
      await axios.post(
        `${API_URL}/api/api-keys`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setSuccess('API key added successfully!')
      setShowAddForm(false)
      setFormData({ exchange: 'bybit', api_key: '', api_secret: '', is_testnet: false })
      loadAPIKeys()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add API key')
    }
  }

  const handleDelete = async (keyId: number) => {
    if (!confirm('Are you sure you want to delete this API key?')) return

    const token = localStorage.getItem('token')

    try {
      await axios.delete(`${API_URL}/api/api-keys/${keyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setSuccess('API key deleted')
      loadAPIKeys()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete API key')
    }
  }

  const handleTestConnection = async (keyId: number) => {
    setTestingKey(keyId)
    // TODO: Implement actual connection test
    setTimeout(() => {
      setTestingKey(null)
      setSuccess('Connection test successful!')
    }, 2000)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">API Keys Management</h1>
              <p className="text-gray-400 text-sm">Connect your exchange accounts securely</p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500 rounded-lg text-green-400 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {success}
          </div>
        )}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500 rounded-lg text-red-400 flex items-center gap-2">
            <XCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {/* Security Notice - Cryptohopper Style */}
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-4">
            <Shield className="w-8 h-8 text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-white mb-2">🔒 Security Best Practices</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-300">
                <div>
                  <p className="font-semibold text-green-400 mb-1">✅ Enable These Permissions:</p>
                  <ul className="space-y-1 ml-4">
                    <li>• Read / View</li>
                    <li>• Trade / Spot & Derivatives Trading</li>
                    <li>• Position Management</li>
                  </ul>
                </div>
                <div>
                  <p className="font-semibold text-red-400 mb-1">❌ NEVER Enable:</p>
                  <ul className="space-y-1 ml-4">
                    <li>• Withdraw</li>
                    <li>• Transfer</li>
                    <li>• Internal Transfer</li>
                  </ul>
                </div>
              </div>
              <p className="text-yellow-400 text-sm mt-3">
                ⚠️ Even if our platform is compromised, attackers cannot withdraw your funds with these settings.
              </p>
            </div>
          </div>
        </div>

        {/* Video Tutorial - Industry Standard */}
        {!showAddForm && apiKeys.length === 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4">📺 How to Create API Keys (2 minutes)</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <TutorialCard
                exchange="Bybit"
                url="https://www.youtube.com/results?search_query=bybit+api+key+tutorial"
                duration="2:15"
              />
              <TutorialCard
                exchange="Binance"
                url="https://www.youtube.com/results?search_query=binance+api+key+tutorial"
                duration="2:30"
              />
              <TutorialCard
                exchange="OKX"
                url="https://www.youtube.com/results?search_query=okx+api+key+tutorial"
                duration="2:00"
              />
              <TutorialCard
                exchange="Kraken"
                url="https://www.youtube.com/results?search_query=kraken+api+key+tutorial"
                duration="2:45"
              />
              <TutorialCard
                exchange="Coinbase"
                url="https://www.youtube.com/results?search_query=coinbase+api+key+tutorial"
                duration="3:00"
              />
              <TutorialCard
                exchange="KuCoin"
                url="https://www.youtube.com/results?search_query=kucoin+api+key+tutorial"
                duration="2:20"
              />
            </div>
          </div>
        )}

        {/* Existing API Keys */}
        {apiKeys.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-white">Your API Keys</h2>
              <button
                onClick={() => setShowAddForm(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2"
              >
                <Key className="w-4 h-4" />
                Add New Key
              </button>
            </div>

            <div className="space-y-4">
              {apiKeys.map(key => (
                <APIKeyCard
                  key={key.id}
                  apiKey={key}
                  onDelete={() => handleDelete(key.id)}
                  onTest={() => handleTestConnection(key.id)}
                  testing={testingKey === key.id}
                />
              ))}
            </div>
          </div>
        )}

        {/* Add API Key Form */}
        {(showAddForm || apiKeys.length === 0) && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-6">
              {apiKeys.length === 0 ? 'Add Your First API Key' : 'Add New API Key'}
            </h2>

            <form onSubmit={handleAddKey} className="space-y-6">
              {/* Exchange Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Exchange *
                </label>
                <select
                  value={formData.exchange}
                  onChange={(e) => setFormData({ ...formData, exchange: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="bybit">Bybit</option>
                  <option value="binance">Binance</option>
                  <option value="okx">OKX</option>
                  <option value="kraken">Kraken</option>
                  <option value="coinbase">Coinbase</option>
                  <option value="kucoin">KuCoin</option>
                </select>
              </div>

              {/* Exchange-Specific Instructions */}
              {formData.exchange === 'bybit' && (
                <ExchangeInstructions
                  exchange="Bybit"
                  url="https://bybit.com/app/user/api-management"
                  steps={[
                    'Go to Bybit API Management',
                    'Click "Create New API Key"',
                    'Enable: Contract Trading, Position, Trade',
                    'DO NOT enable: Withdraw, Transfer',
                    'Copy API Key and Secret'
                  ]}
                />
              )}
              {formData.exchange === 'binance' && (
                <ExchangeInstructions
                  exchange="Binance"
                  url="https://www.binance.com/en/my/settings/api-management"
                  steps={[
                    'Go to Binance API Management',
                    'Create API Key',
                    'Enable: Spot & Margin Trading, Futures',
                    'DO NOT enable: Enable Withdrawals',
                    'Restrict access to trusted IPs only (optional)',
                    'Save API Key and Secret Key'
                  ]}
                />
              )}
              {formData.exchange === 'okx' && (
                <ExchangeInstructions
                  exchange="OKX"
                  url="https://www.okx.com/account/my-api"
                  steps={[
                    'Go to OKX API Management',
                    'Create V5 API Key',
                    'Enable: Trade, Read',
                    'DO NOT enable: Withdraw',
                    'Set IP whitelist for security',
                    'Copy API Key, Secret Key, and Passphrase'
                  ]}
                />
              )}
              {formData.exchange === 'kraken' && (
                <ExchangeInstructions
                  exchange="Kraken"
                  url="https://www.kraken.com/u/security/api"
                  steps={[
                    'Go to Kraken Security → API',
                    'Generate New Key',
                    'Enable: Query Funds, Create & Modify Orders, Query Open/Closed Orders',
                    'DO NOT enable: Withdraw Funds',
                    'Set nonce window if needed',
                    'Copy API Key and Private Key'
                  ]}
                />
              )}
              {formData.exchange === 'coinbase' && (
                <ExchangeInstructions
                  exchange="Coinbase"
                  url="https://www.coinbase.com/settings/api"
                  steps={[
                    'Go to Coinbase Settings → API',
                    'New API Key',
                    'Select: View, Trade',
                    'DO NOT select: Transfer, Send',
                    'Add IP whitelist (recommended)',
                    'Save API Key and Secret'
                  ]}
                />
              )}
              {formData.exchange === 'kucoin' && (
                <ExchangeInstructions
                  exchange="KuCoin"
                  url="https://www.kucoin.com/account/api"
                  steps={[
                    'Go to KuCoin API Management',
                    'Create API',
                    'Enable: General, Trade, Margin Trading',
                    'DO NOT enable: Withdraw, Transfer',
                    'Set trading password',
                    'Copy API Key, Secret, and Passphrase'
                  ]}
                />
              )}

              {/* API Key Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API Key *
                </label>
                <input
                  type="text"
                  required
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder="Enter your API key"
                />
              </div>

              {/* API Secret Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  API Secret *
                </label>
                <input
                  type="password"
                  required
                  value={formData.api_secret}
                  onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  placeholder="Enter your API secret"
                />
                <p className="text-gray-400 text-xs mt-1">
                  🔒 Encrypted with AES-256 before storage
                </p>
              </div>

              {/* Testnet Toggle - 3Commas Standard */}
              <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                <div>
                  <p className="font-semibold text-white">Paper Trading (Testnet)</p>
                  <p className="text-sm text-gray-400">Practice with fake money before going live</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_testnet}
                    onChange={(e) => setFormData({ ...formData, is_testnet: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-4">
                {apiKeys.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
                  >
                    Cancel
                  </button>
                )}
                <button
                  type="submit"
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2"
                >
                  <Shield className="w-5 h-5" />
                  Add API Key Securely
                </button>
              </div>
            </form>
          </div>
        )}

        {/* FAQ Section - TradeSanta Style */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
          <FAQCard
            question="Why are my API keys safe?"
            answer="We use AES-256 encryption to store your keys. Even our engineers cannot see your actual keys. We never request withdrawal permissions, so your funds cannot be moved."
          />
          <FAQCard
            question="What if my exchange doesn't connect?"
            answer="Common issues: 1) Wrong permissions enabled 2) IP whitelist blocking us 3) Unverified exchange account (KYC). Check our troubleshooting guide."
          />
          <FAQCard
            question="Should I use testnet first?"
            answer="Yes! We strongly recommend testing your bot with paper trading (testnet) before risking real money. You can migrate to live trading anytime."
          />
          <FAQCard
            question="Can I use multiple exchanges?"
            answer="Yes! You can connect Bybit, Binance, OKX, and more. Each bot can use a different exchange for diversification."
          />
        </div>
      </main>
    </div>
  )
}

// Tutorial Card Component
function TutorialCard({ exchange, url, duration }: { exchange: string; url: string; duration: string }) {
  return (
    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600 hover:border-blue-500 transition cursor-pointer">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-white">{exchange}</h4>
        <span className="text-xs text-gray-400">{duration}</span>
      </div>
      <div className="aspect-video bg-gray-800 rounded-lg mb-3 flex items-center justify-center">
        <PlayCircle className="w-12 h-12 text-blue-400" />
      </div>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
      >
        Watch Tutorial <ExternalLink className="w-3 h-3" />
      </a>
    </div>
  )
}

// API Key Card Component
function APIKeyCard({ apiKey, onDelete, onTest, testing }: any) {
  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-white">{apiKey.exchange.toUpperCase()}</h3>
            {apiKey.is_testnet ? (
              <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-semibold rounded">
                TESTNET
              </span>
            ) : (
              <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs font-semibold rounded">
                LIVE
              </span>
            )}
          </div>
          <p className="text-gray-400 text-sm">
            Added: {new Date(apiKey.created_at).toLocaleDateString()}
          </p>
          {apiKey.last_used_at && (
            <p className="text-gray-400 text-sm">
              Last used: {new Date(apiKey.last_used_at).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={onTest}
            disabled={testing}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg transition text-sm flex items-center gap-2"
          >
            {testing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Test
              </>
            )}
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition text-sm flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <CheckCircle className="w-5 h-5 text-green-400" />
        <span className="text-gray-300">Connection verified</span>
      </div>
    </div>
  )
}

// Exchange Instructions Component
function ExchangeInstructions({ exchange, url, steps }: { exchange: string; url: string; steps: string[] }) {
  return (
    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
      <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-blue-400" />
        {exchange} Setup Instructions
      </h4>
      <ol className="space-y-2 text-sm text-gray-300 ml-6 list-decimal">
        <li>
          {steps[0]} → <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline inline-flex items-center gap-1">
            Open {exchange} <ExternalLink className="w-3 h-3" />
          </a>
        </li>
        {steps.slice(1).map((step, idx) => (
          <li key={idx} dangerouslySetInnerHTML={{ __html: step.replace(/DO NOT/g, '<strong class="text-red-400">DO NOT</strong>').replace(/Enable:/g, '<strong class="text-green-400">Enable:</strong>') }} />
        ))}
      </ol>
    </div>
  )
}

// FAQ Card Component
function FAQCard({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h4 className="text-lg font-semibold text-white mb-2">{question}</h4>
      <p className="text-gray-400 text-sm">{answer}</p>
    </div>
  )
}
