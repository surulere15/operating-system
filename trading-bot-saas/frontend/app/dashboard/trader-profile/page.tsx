'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  User, TrendingUp, Clock, Target, DollarSign, Zap, Shield, Trophy,
  CheckCircle, ArrowRight, Info, ChevronRight, Star, Sparkles
} from 'lucide-react'

interface Template {
  id: string
  name: string
  description: string
  target_audience: string
  capital_requirement: string
  time_commitment: string
  expected_monthly_return?: string
  expected_hourly_earnings?: string
  expected_daily_earnings?: string
  max_drawdown?: string
  compound_projection_12mo?: string
  white_glove_service?: boolean
}

interface BotConfiguration {
  name: string
  description: string
  recommended_strategy: string
  alternative_strategies: string[]
  position_size_percent: number
  risk_per_trade_percent: number
  max_concurrent_trades: number
  stop_loss_percent: number
  take_profit_percent: number
  trailing_stop_percent: number
  avg_trades_per_day: string
  avg_holding_period: string
  recommended_timeframes: string[]
  use_ml_predictions: boolean
  use_sentiment_analysis: boolean
  use_whale_tracking: boolean
  use_smart_execution: boolean
  use_leverage: boolean
  max_leverage: number
  expected_monthly_return: string
  expected_win_rate: string
  expected_max_drawdown: string
  time_required_per_day: string
  automation_level: string
}

export default function TraderProfilePage() {
  const [step, setStep] = useState<'select' | 'quick' | 'custom' | 'templates' | 'review'>('select')
  const [templates, setTemplates] = useState<Template[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [configuration, setConfiguration] = useState<BotConfiguration | null>(null)
  const [loading, setLoading] = useState(false)

  // Quick wizard form
  const [capital, setCapital] = useState(5000)
  const [hoursPerDay, setHoursPerDay] = useState(4)
  const [riskTolerance, setRiskTolerance] = useState('moderate')

  // Custom form
  const [capitalTier, setCapitalTier] = useState('medium')
  const [tradingStyle, setTradingStyle] = useState('day_trader')
  const [riskProfile, setRiskProfile] = useState('moderate')
  const [timeAvailability, setTimeAvailability] = useState('part_time')
  const [experienceLevel, setExperienceLevel] = useState('intermediate')

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get('http://localhost:8000/api/trader-profile/templates', {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.data.success) {
        setTemplates(response.data.templates)
      }
    } catch (error) {
      console.error('Error loading templates:', error)
    }
  }

  const createQuickProfile = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        'http://localhost:8000/api/trader-profile/quick',
        {
          capital,
          hours_per_day: hoursPerDay,
          risk_tolerance: riskTolerance
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      if (response.data.success) {
        setConfiguration(response.data.configuration)
        setStep('review')
      }
    } catch (error) {
      console.error('Error creating profile:', error)
      alert('Failed to create profile')
    } finally {
      setLoading(false)
    }
  }

  const createCustomProfile = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        'http://localhost:8000/api/trader-profile/custom',
        {
          capital_tier: capitalTier,
          trading_style: tradingStyle,
          risk_profile: riskProfile,
          time_availability: timeAvailability,
          experience_level: experienceLevel
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      if (response.data.success) {
        setConfiguration(response.data.configuration)
        setStep('review')
      }
    } catch (error) {
      console.error('Error creating profile:', error)
      alert('Failed to create profile')
    } finally {
      setLoading(false)
    }
  }

  const loadTemplateConfig = async (templateId: string) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `http://localhost:8000/api/trader-profile/template/${templateId}`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      if (response.data.success) {
        setSelectedTemplate(response.data.template)
        setConfiguration(response.data.configuration)
        setStep('review')
      }
    } catch (error) {
      console.error('Error loading template:', error)
      alert('Failed to load template')
    } finally {
      setLoading(false)
    }
  }

  const getTemplateIcon = (id: string) => {
    const icons: { [key: string]: JSX.Element } = {
      'hourly_earner': <Zap className="h-8 w-8" />,
      'daily_earner': <DollarSign className="h-8 w-8" />,
      'passive_income': <Clock className="h-8 w-8" />,
      'wealth_builder': <Trophy className="h-8 w-8" />,
      'beginner_safe': <Shield className="h-8 w-8" />,
      'professional_trader': <Target className="h-8 w-8" />,
      'whale_institutional': <Star className="h-8 w-8" />
    }
    return icons[id] || <User className="h-8 w-8" />
  }

  const getTemplateColor = (id: string) => {
    const colors: { [key: string]: string } = {
      'hourly_earner': 'from-yellow-500 to-orange-500',
      'daily_earner': 'from-green-500 to-emerald-500',
      'passive_income': 'from-blue-500 to-indigo-500',
      'wealth_builder': 'from-purple-500 to-pink-500',
      'beginner_safe': 'from-cyan-500 to-blue-500',
      'professional_trader': 'from-red-500 to-rose-500',
      'whale_institutional': 'from-amber-500 to-yellow-500'
    }
    return colors[id] || 'from-gray-500 to-gray-600'
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            🎯 Find Your Perfect Trading Profile
          </h1>
          <p className="text-gray-600 text-lg">
            Personalized bot configurations optimized for YOUR trading style, capital, and goals
          </p>
        </div>

        {/* Selection Step */}
        {step === 'select' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Quick Wizard */}
            <button
              onClick={() => setStep('quick')}
              className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-all border-2 border-transparent hover:border-blue-500 text-left group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg">
                  <Zap className="h-8 w-8 text-white" />
                </div>
                <ChevronRight className="h-6 w-6 text-gray-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
              </div>
              <h3 className="text-xl font-bold mb-2">⚡ Quick Wizard</h3>
              <p className="text-gray-600 mb-4">
                Answer 3 simple questions and get your optimal bot configuration in seconds
              </p>
              <div className="flex items-center text-sm text-blue-600 font-semibold">
                <span>Recommended for beginners</span>
              </div>
            </button>

            {/* Templates */}
            <button
              onClick={() => setStep('templates')}
              className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-all border-2 border-transparent hover:border-purple-500 text-left group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
                  <Sparkles className="h-8 w-8 text-white" />
                </div>
                <ChevronRight className="h-6 w-6 text-gray-400 group-hover:text-purple-500 group-hover:translate-x-1 transition-all" />
              </div>
              <h3 className="text-xl font-bold mb-2">✨ Pre-Built Templates</h3>
              <p className="text-gray-600 mb-4">
                Choose from specialized templates: Hourly Earner, Day Trader, Passive Income, and more
              </p>
              <div className="flex items-center text-sm text-purple-600 font-semibold">
                <span>Most popular option</span>
              </div>
            </button>

            {/* Custom */}
            <button
              onClick={() => setStep('custom')}
              className="bg-white rounded-xl p-8 shadow-lg hover:shadow-xl transition-all border-2 border-transparent hover:border-green-500 text-left group"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg">
                  <Target className="h-8 w-8 text-white" />
                </div>
                <ChevronRight className="h-6 w-6 text-gray-400 group-hover:text-green-500 group-hover:translate-x-1 transition-all" />
              </div>
              <h3 className="text-xl font-bold mb-2">🎯 Custom Profile</h3>
              <p className="text-gray-600 mb-4">
                Full control over every parameter. Perfect for experienced traders with specific needs
              </p>
              <div className="flex items-center text-sm text-green-600 font-semibold">
                <span>For advanced users</span>
              </div>
            </button>
          </div>
        )}

        {/* Quick Wizard */}
        {step === 'quick' && (
          <div className="bg-white rounded-xl p-8 shadow-lg max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">⚡ Quick Profile Wizard</h2>

            <div className="space-y-6">
              {/* Capital */}
              <div>
                <label className="block text-sm font-semibold mb-2">
                  1️⃣ Trading Capital
                </label>
                <input
                  type="range"
                  min="100"
                  max="100000"
                  step="100"
                  value={capital}
                  onChange={(e) => setCapital(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-2xl font-bold text-blue-600">
                    ${capital.toLocaleString()}
                  </span>
                  <span className="text-sm text-gray-500">
                    {capital < 1000 ? 'Micro' : capital < 5000 ? 'Small' : capital < 25000 ? 'Medium' : capital < 100000 ? 'Large' : 'Whale'}
                  </span>
                </div>
              </div>

              {/* Hours per day */}
              <div>
                <label className="block text-sm font-semibold mb-2">
                  2️⃣ Time Commitment (hours/day)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="12"
                  step="0.5"
                  value={hoursPerDay}
                  onChange={(e) => setHoursPerDay(Number(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between mt-2">
                  <span className="text-2xl font-bold text-purple-600">
                    {hoursPerDay} hours/day
                  </span>
                  <span className="text-sm text-gray-500">
                    {hoursPerDay >= 6 ? 'Active Trader' : hoursPerDay >= 3 ? 'Part-Time' : 'Passive'}
                  </span>
                </div>
              </div>

              {/* Risk tolerance */}
              <div>
                <label className="block text-sm font-semibold mb-2">
                  3️⃣ Risk Tolerance
                </label>
                <div className="grid grid-cols-4 gap-3">
                  {['conservative', 'moderate', 'aggressive', 'extreme'].map((risk) => (
                    <button
                      key={risk}
                      onClick={() => setRiskTolerance(risk)}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        riskTolerance === risk
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="text-2xl mb-1">
                        {risk === 'conservative' ? '🛡️' : risk === 'moderate' ? '⚖️' : risk === 'aggressive' ? '🚀' : '⚡'}
                      </div>
                      <div className="text-xs font-semibold capitalize">{risk}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setStep('select')}
                  className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-semibold"
                >
                  ← Back
                </button>
                <button
                  onClick={createQuickProfile}
                  disabled={loading}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:shadow-lg font-semibold disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Profile →'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Templates */}
        {step === 'templates' && (
          <div>
            <button
              onClick={() => setStep('select')}
              className="mb-6 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-semibold"
            >
              ← Back
            </button>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all overflow-hidden group cursor-pointer"
                  onClick={() => loadTemplateConfig(template.id)}
                >
                  {/* Header with gradient */}
                  <div className={`p-6 bg-gradient-to-br ${getTemplateColor(template.id)} text-white`}>
                    <div className="flex items-center gap-3 mb-2">
                      {getTemplateIcon(template.id)}
                      <h3 className="text-xl font-bold">{template.name}</h3>
                    </div>
                    <p className="text-white/90 text-sm">{template.description}</p>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="space-y-3 mb-4">
                      <div className="flex items-center gap-2 text-sm">
                        <DollarSign className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">{template.capital_requirement}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="h-4 w-4 text-gray-400" />
                        <span>{template.time_commitment}</span>
                      </div>
                      {template.expected_monthly_return && (
                        <div className="flex items-center gap-2 text-sm">
                          <TrendingUp className="h-4 w-4 text-green-500" />
                          <span className="font-semibold text-green-600">
                            {template.expected_monthly_return} monthly
                          </span>
                        </div>
                      )}
                      {template.expected_hourly_earnings && (
                        <div className="flex items-center gap-2 text-sm">
                          <Zap className="h-4 w-4 text-yellow-500" />
                          <span className="font-semibold text-yellow-600">
                            {template.expected_hourly_earnings}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="text-xs text-gray-500 mb-4">
                      {template.target_audience}
                    </div>

                    {template.white_glove_service && (
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-xs text-amber-800 font-semibold">
                        ⭐ White Glove Service Available
                      </div>
                    )}

                    <div className="mt-4 flex items-center text-blue-600 font-semibold group-hover:translate-x-1 transition-transform">
                      <span>View Configuration</span>
                      <ArrowRight className="h-4 w-4 ml-1" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Custom Profile */}
        {step === 'custom' && (
          <div className="bg-white rounded-xl p-8 shadow-lg max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">🎯 Custom Profile Builder</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Capital Tier */}
              <div>
                <label className="block text-sm font-semibold mb-2">Capital Tier</label>
                <select
                  value={capitalTier}
                  onChange={(e) => setCapitalTier(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="micro">Micro ($100-$1K)</option>
                  <option value="small">Small ($1K-$5K)</option>
                  <option value="medium">Medium ($5K-$25K)</option>
                  <option value="large">Large ($25K-$100K)</option>
                  <option value="whale">Whale ($100K+)</option>
                </select>
              </div>

              {/* Trading Style */}
              <div>
                <label className="block text-sm font-semibold mb-2">Trading Style</label>
                <select
                  value={tradingStyle}
                  onChange={(e) => setTradingStyle(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="scalper">Scalper (20-100+ trades/day)</option>
                  <option value="day_trader">Day Trader (5-20 trades/day)</option>
                  <option value="swing_trader">Swing Trader (1-5 trades/week)</option>
                  <option value="position_trader">Position Trader (1-2 trades/month)</option>
                </select>
              </div>

              {/* Risk Profile */}
              <div>
                <label className="block text-sm font-semibold mb-2">Risk Profile</label>
                <select
                  value={riskProfile}
                  onChange={(e) => setRiskProfile(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="conservative">Conservative (0.5-1% risk/trade)</option>
                  <option value="moderate">Moderate (1-2% risk/trade)</option>
                  <option value="aggressive">Aggressive (2-4% risk/trade)</option>
                  <option value="extreme">Extreme (4-10% risk/trade)</option>
                </select>
              </div>

              {/* Time Availability */}
              <div>
                <label className="block text-sm font-semibold mb-2">Time Availability</label>
                <select
                  value={timeAvailability}
                  onChange={(e) => setTimeAvailability(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="active">Active (6-8+ hours/day)</option>
                  <option value="part_time">Part-Time (2-4 hours/day)</option>
                  <option value="passive">Passive (&lt;1 hour/day)</option>
                </select>
              </div>

              {/* Experience Level */}
              <div className="md:col-span-2">
                <label className="block text-sm font-semibold mb-2">Experience Level</label>
                <select
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="beginner">Beginner (0-6 months)</option>
                  <option value="intermediate">Intermediate (6 months - 2 years)</option>
                  <option value="advanced">Advanced (2-5 years)</option>
                  <option value="professional">Professional (5+ years)</option>
                </select>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStep('select')}
                className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-semibold"
              >
                ← Back
              </button>
              <button
                onClick={createCustomProfile}
                disabled={loading}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg font-semibold disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Custom Profile →'}
              </button>
            </div>
          </div>
        )}

        {/* Review Configuration */}
        {step === 'review' && configuration && (
          <div className="max-w-5xl mx-auto">
            <button
              onClick={() => setStep('select')}
              className="mb-6 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-semibold"
            >
              ← Start Over
            </button>

            <div className="bg-white rounded-xl p-8 shadow-lg mb-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="h-8 w-8 text-green-500" />
                <div>
                  <h2 className="text-2xl font-bold">{configuration.name}</h2>
                  <p className="text-gray-600">{configuration.description}</p>
                </div>
              </div>

              {/* Expected Performance */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Monthly Return</div>
                  <div className="text-2xl font-bold text-green-600">
                    {configuration.expected_monthly_return}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Win Rate</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {configuration.expected_win_rate}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Trades/Day</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {configuration.avg_trades_per_day}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-orange-50 to-red-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">Max Drawdown</div>
                  <div className="text-2xl font-bold text-orange-600">
                    {configuration.expected_max_drawdown}
                  </div>
                </div>
              </div>

              {/* Configuration Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="font-bold mb-3">🎯 Trading Parameters</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Position Size:</span>
                      <span className="font-semibold">{configuration.position_size_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk per Trade:</span>
                      <span className="font-semibold">{configuration.risk_per_trade_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Max Concurrent Trades:</span>
                      <span className="font-semibold">{configuration.max_concurrent_trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Stop Loss:</span>
                      <span className="font-semibold">{configuration.stop_loss_percent}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Take Profit:</span>
                      <span className="font-semibold">{configuration.take_profit_percent}%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-bold mb-3">⏰ Time & Strategy</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Strategy:</span>
                      <span className="font-semibold">{configuration.recommended_strategy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Holding Period:</span>
                      <span className="font-semibold">{configuration.avg_holding_period}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Time Required:</span>
                      <span className="font-semibold">{configuration.time_required_per_day}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Automation:</span>
                      <span className="font-semibold">{configuration.automation_level}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Timeframes:</span>
                      <span className="font-semibold">{configuration.recommended_timeframes.join(', ')}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Features */}
              <div>
                <h3 className="font-bold mb-3">✨ Enabled Features</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {configuration.use_ml_predictions && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>ML Predictions</span>
                    </div>
                  )}
                  {configuration.use_sentiment_analysis && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Sentiment Analysis</span>
                    </div>
                  )}
                  {configuration.use_whale_tracking && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Whale Tracking</span>
                    </div>
                  )}
                  {configuration.use_smart_execution && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Smart Execution</span>
                    </div>
                  )}
                  {configuration.use_leverage && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span>Leverage (max {configuration.max_leverage}x)</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-6">
                <button className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg hover:shadow-lg font-semibold text-lg">
                  🚀 Create Bot with This Profile
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
