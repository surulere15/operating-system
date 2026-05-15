'use client'

import { useState } from 'react'
import { X, CheckCircle, ArrowRight, ArrowLeft, Play, TrendingUp, Shield, Zap } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface OnboardingWizardProps {
  onComplete: () => void
  onSkip: () => void
}

export default function OnboardingWizard({ onComplete, onSkip }: OnboardingWizardProps) {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [userData, setUserData] = useState({
    experience: '',
    tradingMode: '',
    goals: [] as string[]
  })

  const totalSteps = 5

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete()
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSkip = () => {
    if (confirm('Skip onboarding? You can always access the setup wizard from your dashboard.')) {
      onSkip()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header with Progress */}
        <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-white">Welcome to Trading Bot SaaS! 🚀</h2>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-white transition"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Progress Bar - Industry Standard (75% abandon without it) */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-400">Step {currentStep} of {totalSteps}</span>
              <span className="text-sm text-gray-400">{Math.round((currentStep / totalSteps) * 100)}% Complete</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentStep / totalSteps) * 100}%` }}
              />
            </div>
          </div>

          {/* Step Indicators */}
          <div className="flex justify-between">
            {['Experience', 'Mode', 'Goals', 'Setup', 'Launch'].map((label, idx) => (
              <div key={idx} className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  idx + 1 < currentStep
                    ? 'bg-green-600 text-white'
                    : idx + 1 === currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {idx + 1 < currentStep ? <CheckCircle className="w-5 h-5" /> : idx + 1}
                </div>
                <span className="text-xs text-gray-400 mt-1 hidden sm:block">{label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="p-8">
          {currentStep === 1 && (
            <Step1_Experience userData={userData} setUserData={setUserData} />
          )}
          {currentStep === 2 && (
            <Step2_TradingMode userData={userData} setUserData={setUserData} />
          )}
          {currentStep === 3 && (
            <Step3_Goals userData={userData} setUserData={setUserData} />
          )}
          {currentStep === 4 && (
            <Step4_Setup userData={userData} />
          )}
          {currentStep === 5 && (
            <Step5_Launch userData={userData} router={router} />
          )}
        </div>

        {/* Navigation Footer */}
        <div className="sticky bottom-0 bg-gray-800 border-t border-gray-700 p-6 flex justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition flex items-center gap-2"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>

          <button
            onClick={handleNext}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition flex items-center gap-2"
          >
            {currentStep === totalSteps ? 'Get Started' : 'Continue'}
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

// Step 1: Experience Level (3Commas' approach - different paths for users)
function Step1_Experience({ userData, setUserData }: any) {
  const experienceLevels = [
    {
      id: 'beginner',
      title: 'Beginner',
      icon: <Zap className="w-8 h-8" />,
      description: 'New to crypto trading',
      features: ['Guided setup', 'Conservative settings', 'Video tutorials', 'Template bots'],
      recommended: true
    },
    {
      id: 'intermediate',
      title: 'Intermediate',
      icon: <TrendingUp className="w-8 h-8" />,
      description: '1+ years trading experience',
      features: ['Quick setup', 'Moderate risk', 'Custom strategies', 'Advanced analytics']
    },
    {
      id: 'expert',
      title: 'Expert',
      icon: <Shield className="w-8 h-8" />,
      description: 'Algorithmic trading pro',
      features: ['Full control', 'API access', 'Custom indicators', 'Code integration']
    }
  ]

  return (
    <div>
      <h3 className="text-2xl font-bold text-white mb-2">What's your trading experience?</h3>
      <p className="text-gray-400 mb-8">We'll customize your setup based on your skill level</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {experienceLevels.map(level => (
          <button
            key={level.id}
            onClick={() => setUserData({ ...userData, experience: level.id })}
            className={`p-6 rounded-lg border-2 transition text-left relative ${
              userData.experience === level.id
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-gray-700 bg-gray-700/50 hover:border-gray-600'
            }`}
          >
            {level.recommended && (
              <div className="absolute -top-3 left-4 px-3 py-1 bg-green-500 text-white text-xs font-semibold rounded-full">
                RECOMMENDED
              </div>
            )}

            <div className="text-blue-400 mb-4">{level.icon}</div>
            <h4 className="text-xl font-bold text-white mb-2">{level.title}</h4>
            <p className="text-gray-400 text-sm mb-4">{level.description}</p>

            <ul className="space-y-2">
              {level.features.map((feature, idx) => (
                <li key={idx} className="text-sm text-gray-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
          </button>
        ))}
      </div>
    </div>
  )
}

// Step 2: Trading Mode (3Commas standard - Paper trading first)
function Step2_TradingMode({ userData, setUserData }: any) {
  const modes = [
    {
      id: 'paper',
      title: 'Paper Trading (Testnet)',
      subtitle: 'Practice with fake money',
      icon: '📝',
      pros: ['Zero risk', 'Learn the platform', 'Test strategies', 'See real results'],
      cons: ['Virtual profits only'],
      recommended: true,
      badge: 'RECOMMENDED FOR BEGINNERS'
    },
    {
      id: 'live',
      title: 'Live Trading',
      subtitle: 'Trade with real money',
      icon: '💰',
      pros: ['Real profits', 'Full features', 'All markets', 'Immediate trading'],
      cons: ['Real risk', 'Requires experience'],
      recommended: false,
      badge: 'FOR EXPERIENCED TRADERS'
    }
  ]

  return (
    <div>
      <h3 className="text-2xl font-bold text-white mb-2">Choose your trading mode</h3>
      <p className="text-gray-400 mb-8">
        {userData.experience === 'beginner'
          ? 'We recommend starting with paper trading to learn risk-free'
          : 'You can start with either mode and switch anytime'
        }
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {modes.map(mode => (
          <button
            key={mode.id}
            onClick={() => setUserData({ ...userData, tradingMode: mode.id })}
            className={`p-6 rounded-lg border-2 transition text-left relative ${
              userData.tradingMode === mode.id
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-gray-700 bg-gray-700/50 hover:border-gray-600'
            }`}
          >
            {mode.recommended && userData.experience === 'beginner' && (
              <div className="absolute -top-3 left-4 px-3 py-1 bg-green-500 text-white text-xs font-semibold rounded-full">
                {mode.badge}
              </div>
            )}

            <div className="text-4xl mb-4">{mode.icon}</div>
            <h4 className="text-xl font-bold text-white mb-1">{mode.title}</h4>
            <p className="text-gray-400 text-sm mb-4">{mode.subtitle}</p>

            <div className="mb-4">
              <p className="text-sm font-semibold text-green-400 mb-2">✅ Advantages:</p>
              <ul className="space-y-1">
                {mode.pros.map((pro, idx) => (
                  <li key={idx} className="text-sm text-gray-300">• {pro}</li>
                ))}
              </ul>
            </div>

            <div>
              <p className="text-sm font-semibold text-yellow-400 mb-2">⚠️ Considerations:</p>
              <ul className="space-y-1">
                {mode.cons.map((con, idx) => (
                  <li key={idx} className="text-sm text-gray-300">• {con}</li>
                ))}
              </ul>
            </div>
          </button>
        ))}
      </div>

      {userData.tradingMode === 'paper' && (
        <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <p className="text-blue-400 text-sm">
            💡 <strong>Good choice!</strong> You can migrate to live trading anytime after you're comfortable with the platform.
          </p>
        </div>
      )}
    </div>
  )
}

// Step 3: Goals (Personalization - 2026 trend)
function Step3_Goals({ userData, setUserData }: any) {
  const goals = [
    { id: 'passive-income', label: 'Generate passive income', icon: '💰' },
    { id: 'learn-trading', label: 'Learn automated trading', icon: '📚' },
    { id: 'diversify', label: 'Diversify investments', icon: '📊' },
    { id: 'test-strategies', label: 'Test trading strategies', icon: '🧪' },
    { id: 'scale-trading', label: 'Scale existing trading', icon: '📈' },
    { id: '24-7-trading', label: '24/7 automated trading', icon: '🤖' }
  ]

  const toggleGoal = (goalId: string) => {
    const currentGoals = userData.goals || []
    if (currentGoals.includes(goalId)) {
      setUserData({ ...userData, goals: currentGoals.filter((g: string) => g !== goalId) })
    } else {
      setUserData({ ...userData, goals: [...currentGoals, goalId] })
    }
  }

  return (
    <div>
      <h3 className="text-2xl font-bold text-white mb-2">What are your goals?</h3>
      <p className="text-gray-400 mb-8">Select all that apply (we'll personalize your experience)</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map(goal => (
          <button
            key={goal.id}
            onClick={() => toggleGoal(goal.id)}
            className={`p-4 rounded-lg border-2 transition text-left flex items-center gap-4 ${
              userData.goals?.includes(goal.id)
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-gray-700 bg-gray-700/50 hover:border-gray-600'
            }`}
          >
            <span className="text-3xl">{goal.icon}</span>
            <span className="text-white font-semibold">{goal.label}</span>
            {userData.goals?.includes(goal.id) && (
              <CheckCircle className="w-6 h-6 text-blue-400 ml-auto" />
            )}
          </button>
        ))}
      </div>

      <p className="text-gray-400 text-sm mt-6">
        Selected: {userData.goals?.length || 0} goals
      </p>
    </div>
  )
}

// Step 4: Setup Checklist
function Step4_Setup({ userData }: any) {
  const setupSteps = [
    {
      title: 'Add API Keys',
      description: 'Connect your exchange account securely',
      time: '2 minutes',
      link: '/dashboard/api-keys'
    },
    {
      title: 'Create Your First Bot',
      description: 'Choose a template or customize settings',
      time: '3 minutes',
      link: '/dashboard?action=create-bot'
    },
    {
      title: userData.tradingMode === 'paper' ? 'Start Paper Trading' : 'Start Live Trading',
      description: 'Launch your bot and monitor performance',
      time: '1 minute',
      link: '/dashboard'
    }
  ]

  return (
    <div>
      <h3 className="text-2xl font-bold text-white mb-2">Next steps to get started</h3>
      <p className="text-gray-400 mb-8">Here's what you'll do after this wizard</p>

      <div className="space-y-4">
        {setupSteps.map((step, idx) => (
          <div key={idx} className="bg-gray-700 rounded-lg p-6 border border-gray-600">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold">{idx + 1}</span>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-bold text-white mb-1">{step.title}</h4>
                <p className="text-gray-400 text-sm mb-2">{step.description}</p>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500">⏱️ {step.time}</span>
                  {userData.experience === 'beginner' && idx === 0 && (
                    <span className="text-xs text-blue-400 flex items-center gap-1">
                      <Play className="w-3 h-3" />
                      Video tutorial available
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-6 bg-green-500/10 border border-green-500/20 rounded-lg">
        <h4 className="font-semibold text-green-400 mb-2">📚 Your Personalized Setup</h4>
        <ul className="space-y-2 text-sm text-gray-300">
          <li>• Experience level: <strong>{userData.experience}</strong></li>
          <li>• Trading mode: <strong>{userData.tradingMode === 'paper' ? 'Paper Trading' : 'Live Trading'}</strong></li>
          <li>• Goals: <strong>{userData.goals?.length || 0} selected</strong></li>
          {userData.experience === 'beginner' && (
            <li className="text-blue-400">• Beginner-friendly templates will be recommended</li>
          )}
        </ul>
      </div>
    </div>
  )
}

// Step 5: Launch
function Step5_Launch({ userData, router }: any) {
  return (
    <div className="text-center">
      <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
        <CheckCircle className="w-12 h-12 text-white" />
      </div>

      <h3 className="text-3xl font-bold text-white mb-4">You're All Set! 🎉</h3>
      <p className="text-gray-400 text-lg mb-8">
        Your {userData.tradingMode === 'paper' ? 'paper trading' : 'live trading'} account is ready
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon="🔑"
          title="API Keys"
          description="Connect your exchange"
          action="Add Now"
          onClick={() => router.push('/dashboard/api-keys')}
        />
        <StatCard
          icon="🤖"
          title="Create Bot"
          description="Set up your first bot"
          action="Create"
          onClick={() => router.push('/dashboard')}
        />
        <StatCard
          icon="📊"
          title="Dashboard"
          description="Monitor performance"
          action="View"
          onClick={() => router.push('/dashboard')}
        />
      </div>

      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 text-left">
        <h4 className="font-semibold text-blue-400 mb-3">💡 Pro Tips:</h4>
        <ul className="space-y-2 text-sm text-gray-300">
          <li>• Start with conservative settings ($35-50 capital, 60%+ confidence)</li>
          <li>• Monitor your first trades closely to understand bot behavior</li>
          <li>• {userData.tradingMode === 'paper' ? 'Practice for 1-2 weeks before going live' : 'Set strict risk limits (max 10% daily loss)'}</li>
          <li>• Join our community for tips and strategies</li>
        </ul>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({ icon, title, description, action, onClick }: any) {
  return (
    <div className="bg-gray-700 rounded-lg p-6 border border-gray-600">
      <div className="text-4xl mb-3">{icon}</div>
      <h4 className="text-lg font-bold text-white mb-1">{title}</h4>
      <p className="text-gray-400 text-sm mb-4">{description}</p>
      <button
        onClick={onClick}
        className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-semibold"
      >
        {action}
      </button>
    </div>
  )
}
