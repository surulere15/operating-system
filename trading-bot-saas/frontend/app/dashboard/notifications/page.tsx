'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Mail, MessageSquare, Bell, Save, CheckCircle, Info, ExternalLink } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function NotificationsPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const [preferences, setPreferences] = useState({
    email_enabled: true,
    telegram_enabled: false,
    telegram_chat_id: ''
  })

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const response = await axios.get(
        `${API_URL}/api/notifications/preferences`,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setPreferences({
        email_enabled: response.data.email_enabled,
        telegram_enabled: response.data.telegram_enabled,
        telegram_chat_id: response.data.telegram_chat_id || ''
      })
    } catch (err) {
      console.error('Failed to load preferences:', err)
    } finally {
      setLoading(false)
    }
  }

  const savePreferences = async () => {
    setSaving(true)
    setError('')
    setSuccess(false)

    const token = localStorage.getItem('token')

    try {
      await axios.patch(
        `${API_URL}/api/notifications/preferences`,
        {
          email_enabled: preferences.email_enabled,
          telegram_chat_id: preferences.telegram_chat_id || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Notification Settings</h1>
          <p className="text-gray-400">Manage how you receive trade alerts</p>
        </div>

        {/* Success Message */}
        {success && (
          <div className="bg-green-500/10 border border-green-500 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span className="text-green-400">Settings saved successfully!</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 text-red-400">
            {error}
          </div>
        )}

        {/* Email Notifications */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Mail className="w-6 h-6 text-blue-400" />
            </div>

            <div className="flex-1">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">Email Notifications</h3>
                  <p className="text-sm text-gray-400">Get email alerts when trades are executed</p>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={preferences.email_enabled}
                    onChange={(e) => setPreferences({ ...preferences, email_enabled: e.target.checked })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5" />
                  <div className="text-sm text-gray-300">
                    <p className="mb-2">You'll receive emails for:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Trade opened (entry confirmation)</li>
                      <li>Trade closed (P&L summary)</li>
                      <li>Daily trading summary</li>
                      <li>Important risk alerts</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Telegram Notifications */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-green-400" />
            </div>

            <div className="flex-1">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-1">Telegram Alerts</h3>
                <p className="text-sm text-gray-400">Real-time notifications via Telegram bot</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Telegram Chat ID
                  </label>
                  <input
                    type="text"
                    value={preferences.telegram_chat_id}
                    onChange={(e) => setPreferences({ ...preferences, telegram_chat_id: e.target.value })}
                    placeholder="Enter your Telegram chat ID"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    {preferences.telegram_chat_id ? '✅ Telegram enabled' : 'Enter chat ID to enable Telegram notifications'}
                  </p>
                </div>

                {/* Setup Instructions */}
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                  <h4 className="font-semibold text-white mb-3 flex items-center gap-2">
                    <Info className="w-4 h-4 text-green-400" />
                    How to get your Telegram Chat ID
                  </h4>
                  <ol className="text-sm text-gray-300 space-y-2 list-decimal list-inside">
                    <li>
                      Open Telegram and search for{' '}
                      <a
                        href="https://t.me/userinfobot"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-400 hover:underline inline-flex items-center gap-1"
                      >
                        @userinfobot
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </li>
                    <li>Start a chat with the bot and send /start</li>
                    <li>The bot will reply with your Chat ID (e.g., "123456789")</li>
                    <li>Copy and paste your Chat ID above</li>
                    <li>Click "Save Changes" below</li>
                  </ol>

                  <div className="mt-3 p-3 bg-gray-900/50 rounded border border-gray-700">
                    <p className="text-xs text-gray-400">
                      <strong className="text-white">Note:</strong> After saving your Chat ID, you'll need to start a conversation
                      with our bot{' '}
                      <span className="text-green-400 font-mono">@TradingBotAlerts_bot</span> to receive notifications.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Notification Types */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-start gap-4 mb-4">
            <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Bell className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">What You'll Receive</h3>
              <p className="text-sm text-gray-400">All notification types are included</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <h4 className="font-semibold text-white text-sm">Trade Opened</h4>
              </div>
              <p className="text-xs text-gray-400">
                Instant alert when your bot enters a new position with entry price, stop-loss, and take-profit levels.
              </p>
            </div>

            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                <h4 className="font-semibold text-white text-sm">Trade Closed</h4>
              </div>
              <p className="text-xs text-gray-400">
                Summary when position closes including P&L, exit reason, and updated account balance.
              </p>
            </div>

            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-purple-400"></div>
                <h4 className="font-semibold text-white text-sm">Daily Summary</h4>
              </div>
              <p className="text-xs text-gray-400">
                End-of-day recap with total trades, win rate, and daily P&L performance.
              </p>
            </div>

            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-red-400"></div>
                <h4 className="font-semibold text-white text-sm">Risk Alerts</h4>
              </div>
              <p className="text-xs text-gray-400">
                Important warnings when daily loss limits are approached or risk thresholds are exceeded.
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={savePreferences}
            disabled={saving}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <Save className="w-5 h-5 animate-pulse" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                Save Changes
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  )
}
