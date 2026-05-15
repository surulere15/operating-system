'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Check, Zap, Crown, Building2, CreditCard } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SubscriptionInfo {
  active: boolean
  tier: string
  status: string
  current_period_end?: string
  cancel_at_period_end?: boolean
}

export default function BillingPage() {
  const router = useRouter()
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null)

  useEffect(() => {
    loadSubscription()
  }, [])

  const loadSubscription = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/')
      return
    }

    try {
      const response = await axios.get(`${API_URL}/api/billing/subscription`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setSubscription(response.data)
    } catch (err) {
      console.error('Failed to load subscription:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubscribe = async (tier: string) => {
    const token = localStorage.getItem('token')
    setCheckoutLoading(tier)

    try {
      const response = await axios.post(
        `${API_URL}/api/billing/create-checkout-session`,
        { tier },
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create checkout session')
      setCheckoutLoading(null)
    }
  }

  const handleManageSubscription = async () => {
    const token = localStorage.getItem('token')
    setCheckoutLoading('portal')

    try {
      const response = await axios.post(
        `${API_URL}/api/billing/create-portal-session`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )

      // Redirect to Stripe portal
      window.location.href = response.data.portal_url
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to open billing portal')
      setCheckoutLoading(null)
    }
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
              <h1 className="text-2xl font-bold text-white">Billing & Subscription</h1>
              <p className="text-gray-400 text-sm">Manage your subscription and billing</p>
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
        {/* Current Subscription */}
        {subscription?.active && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8 border border-gray-700">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Current Subscription</h2>
                <div className="space-y-1">
                  <p className="text-gray-300">
                    <span className="font-semibold">{subscription.tier.toUpperCase()}</span> Plan
                  </p>
                  <p className="text-gray-400 text-sm">
                    Status: <span className="text-green-400">{subscription.status}</span>
                  </p>
                  {subscription.current_period_end && (
                    <p className="text-gray-400 text-sm">
                      {subscription.cancel_at_period_end ? 'Expires' : 'Renews'} on:{' '}
                      {new Date(subscription.current_period_end).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={handleManageSubscription}
                disabled={checkoutLoading === 'portal'}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
              >
                <CreditCard className="w-4 h-4" />
                {checkoutLoading === 'portal' ? 'Loading...' : 'Manage Subscription'}
              </button>
            </div>
          </div>
        )}

        {/* Pricing Tiers */}
        <h2 className="text-2xl font-bold text-white mb-6 text-center">
          {subscription?.active ? 'Upgrade Your Plan' : 'Choose Your Plan'}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Starter */}
          <PricingCard
            name="Starter"
            icon={<Zap className="w-8 h-8" />}
            price={29}
            features={[
              '1 Trading Bot',
              'Up to 10 Markets',
              'Basic Support',
              'Email Notifications',
              'Trade History'
            ]}
            current={subscription?.tier === 'starter'}
            onSubscribe={() => handleSubscribe('starter')}
            loading={checkoutLoading === 'starter'}
          />

          {/* Pro */}
          <PricingCard
            name="Pro"
            icon={<Crown className="w-8 h-8" />}
            price={79}
            features={[
              '3 Trading Bots',
              'Up to 40 Markets',
              'Priority Support',
              'Telegram Notifications',
              'Advanced Analytics',
              'Custom Strategies'
            ]}
            popular
            current={subscription?.tier === 'pro'}
            onSubscribe={() => handleSubscribe('pro')}
            loading={checkoutLoading === 'pro'}
          />

          {/* Elite */}
          <PricingCard
            name="Elite"
            icon={<Building2 className="w-8 h-8" />}
            price={199}
            features={[
              '10 Trading Bots',
              'All Markets',
              'Dedicated Support',
              'Real-time Alerts',
              'API Access',
              'Custom Integrations',
              'Priority Execution'
            ]}
            current={subscription?.tier === 'elite'}
            onSubscribe={() => handleSubscribe('elite')}
            loading={checkoutLoading === 'elite'}
          />

          {/* Enterprise */}
          <PricingCard
            name="Enterprise"
            icon={<Building2 className="w-8 h-8" />}
            price="Custom"
            features={[
              'Unlimited Bots',
              'All Markets',
              'White-label Solution',
              '24/7 Support',
              'Custom Development',
              'Dedicated Server',
              'SLA Guarantee'
            ]}
            onSubscribe={() => window.location.href = 'mailto:sales@tradingbot.com'}
            loading={false}
          />
        </div>

        {/* Money Back Guarantee */}
        <div className="mt-12 bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 text-center">
          <h3 className="text-xl font-bold text-white mb-2">30-Day Money Back Guarantee</h3>
          <p className="text-gray-300">
            Not satisfied? Get a full refund within 30 days, no questions asked.
          </p>
        </div>

        {/* FAQ */}
        <div className="mt-12">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">Frequently Asked Questions</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FAQItem
              question="Can I change my plan later?"
              answer="Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately for upgrades, or at the end of your billing period for downgrades."
            />
            <FAQItem
              question="How does the bot limit work?"
              answer="Each plan allows you to run a certain number of bots simultaneously. You can create more bots but only activate up to your plan's limit."
            />
            <FAQItem
              question="What payment methods do you accept?"
              answer="We accept all major credit cards (Visa, Mastercard, Amex) and debit cards through Stripe, our secure payment processor."
            />
            <FAQItem
              question="Is my API key secure?"
              answer="Yes! All API keys are encrypted with AES-256 encryption and stored securely. We never have access to your funds, only trading permissions."
            />
          </div>
        </div>
      </main>
    </div>
  )
}

// Pricing Card Component
function PricingCard({
  name,
  icon,
  price,
  features,
  popular = false,
  current = false,
  onSubscribe,
  loading
}: any) {
  return (
    <div className={`bg-gray-800 rounded-lg p-6 border ${
      popular ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-700'
    } relative`}>
      {popular && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
            MOST POPULAR
          </span>
        </div>
      )}

      {current && (
        <div className="absolute -top-3 right-4">
          <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
            CURRENT
          </span>
        </div>
      )}

      <div className="text-center mb-6">
        <div className="text-blue-400 flex justify-center mb-3">{icon}</div>
        <h3 className="text-2xl font-bold text-white mb-2">{name}</h3>
        <div className="text-4xl font-bold text-white mb-1">
          {typeof price === 'number' ? `$${price}` : price}
        </div>
        {typeof price === 'number' && (
          <p className="text-gray-400 text-sm">/month</p>
        )}
      </div>

      <ul className="space-y-3 mb-6">
        {features.map((feature: string, idx: number) => (
          <li key={idx} className="flex items-start gap-2 text-gray-300 text-sm">
            <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={onSubscribe}
        disabled={loading || current}
        className={`w-full py-3 rounded-lg font-semibold transition ${
          current
            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
            : popular
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-700 hover:bg-gray-600 text-white'
        } disabled:opacity-50`}
      >
        {loading ? 'Loading...' : current ? 'Current Plan' : typeof price === 'number' ? 'Subscribe Now' : 'Contact Sales'}
      </button>
    </div>
  )
}

// FAQ Item Component
function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h4 className="text-lg font-semibold text-white mb-2">{question}</h4>
      <p className="text-gray-400 text-sm">{answer}</p>
    </div>
  )
}
