'use client'

import { CheckCircle, Circle, ExternalLink, ArrowRight } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface OnboardingChecklistProps {
  hasAPIKeys: boolean
  hasBots: boolean
  hasActiveBots: boolean
  hasTrades: boolean
  onDismiss: () => void
}

export default function OnboardingChecklist({
  hasAPIKeys,
  hasBots,
  hasActiveBots,
  hasTrades,
  onDismiss
}: OnboardingChecklistProps) {
  const router = useRouter()

  const steps = [
    {
      id: 'account',
      title: 'Create Account',
      completed: true,
      action: null
    },
    {
      id: 'api-keys',
      title: 'Add API Keys',
      subtitle: 'Connect your exchange account',
      completed: hasAPIKeys,
      action: () => router.push('/dashboard/api-keys'),
      time: '2 min',
      priority: 'high'
    },
    {
      id: 'create-bot',
      title: 'Create Your First Bot',
      subtitle: 'Set up automated trading',
      completed: hasBots,
      action: () => {}, // Will trigger create bot modal
      time: '3 min',
      priority: 'high'
    },
    {
      id: 'start-trading',
      title: 'Start Trading',
      subtitle: 'Launch your bot',
      completed: hasActiveBots,
      action: () => router.push('/dashboard'),
      time: '1 min',
      priority: 'medium'
    },
    {
      id: 'first-trade',
      title: 'Complete First Trade',
      subtitle: 'See your bot in action!',
      completed: hasTrades,
      action: () => router.push('/dashboard/trades'),
      time: 'Automatic',
      priority: 'low'
    }
  ]

  const completedCount = steps.filter(s => s.completed).length
  const totalSteps = steps.length
  const progress = Math.round((completedCount / totalSteps) * 100)

  // Auto-dismiss when complete
  if (progress === 100) {
    return null
  }

  const nextStep = steps.find(s => !s.completed)

  return (
    <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg p-6 shadow-lg">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">Getting Started 🚀</h3>
          <p className="text-blue-100 text-sm">{completedCount} of {totalSteps} steps complete</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-blue-100 hover:text-white transition text-sm"
        >
          Dismiss
        </button>
      </div>

      {/* Progress Bar - Zeigarnik Effect (industry standard) */}
      <div className="mb-6">
        <div className="w-full bg-blue-800/30 rounded-full h-3">
          <div
            className="bg-white h-3 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-blue-100 text-xs mt-2">{progress}% complete</p>
      </div>

      {/* Steps */}
      <div className="space-y-3 mb-6">
        {steps.map((step, idx) => (
          <div
            key={step.id}
            className={`flex items-center gap-4 p-3 rounded-lg transition ${
              step.completed
                ? 'bg-white/10'
                : idx === steps.findIndex(s => !s.completed)
                ? 'bg-white/20 border-2 border-white/40'
                : 'bg-white/5'
            }`}
          >
            <div className="flex-shrink-0">
              {step.completed ? (
                <CheckCircle className="w-6 h-6 text-green-400" />
              ) : (
                <Circle className="w-6 h-6 text-blue-200" />
              )}
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h4 className={`font-semibold ${step.completed ? 'text-white/70' : 'text-white'}`}>
                  {step.title}
                </h4>
                {step.time && !step.completed && (
                  <span className="text-xs text-blue-200">({step.time})</span>
                )}
                {step.priority === 'high' && !step.completed && (
                  <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-200 text-xs font-semibold rounded">
                    REQUIRED
                  </span>
                )}
              </div>
              {step.subtitle && !step.completed && (
                <p className="text-blue-100 text-sm">{step.subtitle}</p>
              )}
            </div>

            {!step.completed && step.action && (
              <button
                onClick={step.action}
                className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition text-sm font-semibold flex items-center gap-1"
              >
                {idx === steps.findIndex(s => !s.completed) ? 'Start' : 'Do Later'}
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Next Step CTA */}
      {nextStep && nextStep.action && (
        <button
          onClick={nextStep.action}
          className="w-full py-3 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition font-semibold flex items-center justify-center gap-2"
        >
          Continue Setup: {nextStep.title}
          <ArrowRight className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}
