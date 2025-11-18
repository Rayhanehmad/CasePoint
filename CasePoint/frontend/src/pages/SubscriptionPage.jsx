import React, { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { 
  Check, 
  X,
  Crown,
  Star,
  Zap
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import api from '../services/api'

const SubscriptionPage = () => {
  const { user } = useAuthStore()
  const [plans, setPlans] = useState([])
  const [currentSubscription, setCurrentSubscription] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchSubscriptionData()
  }, [])

  const fetchSubscriptionData = async () => {
    try {
      // Fetch available plans
      const plansResponse = await api.get('/subscriptions/plans')
      setPlans(plansResponse.data.plans || [])

      // Fetch current subscription
      try {
        const currentResponse = await api.get('/subscriptions/current')
        setCurrentSubscription(currentResponse.data)
      } catch (error) {
        // User might not have a subscription
        setCurrentSubscription(null)
      }
    } catch (error) {
      console.error('Failed to fetch subscription data:', error)
      // Set mock data for now
      setPlans([
        {
          tier: 'basic',
          name: 'Basic Plan',
          price_monthly: 29.99,
          price_yearly: 299.99,
          features: [
            'Advanced search with filters',
            'Up to 100 searches per month',
            'Basic document upload',
            'Email support'
          ],
          limits: {
            searches_per_month: 100,
            document_uploads_per_month: 10,
            storage_mb: 1000
          }
        },
        {
          tier: 'premium',
          name: 'Premium Plan',
          price_monthly: 79.99,
          price_yearly: 799.99,
          features: [
            'AI-powered advanced search',
            'Unlimited searches',
            'Bulk document upload',
            'OCR processing',
            'Priority support'
          ],
          limits: {
            searches_per_month: -1,
            document_uploads_per_month: 100,
            storage_mb: 10000
          }
        },
        {
          tier: 'enterprise',
          name: 'Enterprise Plan',
          price_monthly: 199.99,
          price_yearly: 1999.99,
          features: [
            'All Premium features',
            'Custom integrations',
            'API access',
            'Dedicated support',
            'Custom training'
          ],
          limits: {
            searches_per_month: -1,
            document_uploads_per_month: -1,
            storage_mb: -1
          }
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubscribe = async (tier, billingPeriod = 'monthly') => {
    try {
      const response = await api.post('/subscriptions/checkout', {
        tier,
        billing_period: billingPeriod
      })
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create checkout session')
    }
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) {
      return
    }

    try {
      await api.post('/subscriptions/cancel')
      toast.success('Subscription cancelled successfully')
      fetchSubscriptionData()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel subscription')
    }
  }

  const PlanIcon = ({ tier }) => {
    switch (tier) {
      case 'basic':
        return <Star className="h-6 w-6" />
      case 'premium':
        return <Crown className="h-6 w-6" />
      case 'enterprise':
        return <Zap className="h-6 w-6" />
      default:
        return <Star className="h-6 w-6" />
    }
  }

  const isCurrentPlan = (tier) => {
    return user?.subscription_tier === tier || currentSubscription?.tier === tier
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Choose Your Plan</h1>
        <p className="text-lg text-gray-600 mt-2">
          Unlock the full power of legal research with CasePoint
        </p>
      </div>

      {/* Current Subscription Status */}
      {currentSubscription && (
        <div className="card bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-primary-900">Current Subscription</h2>
              <p className="text-primary-700">
                {currentSubscription.tier} plan • Status: {currentSubscription.status}
              </p>
              {currentSubscription.current_period_end && (
                <p className="text-sm text-primary-600 mt-1">
                  Renews on {new Date(currentSubscription.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
            <button
              onClick={handleCancelSubscription}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Cancel Subscription
            </button>
          </div>
        </div>
      )}

      {/* Free Plan */}
      <div className="card border-2 border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Star className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">Free Plan</h3>
              <p className="text-gray-600">Get started with basic search</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-gray-900">$0</p>
            <p className="text-sm text-gray-600">forever</p>
          </div>
        </div>
        
        <ul className="space-y-2 mb-6">
          <li className="flex items-center">
            <Check className="h-4 w-4 text-green-500 mr-3" />
            <span className="text-gray-700">Basic search functionality</span>
          </li>
          <li className="flex items-center">
            <Check className="h-4 w-4 text-green-500 mr-3" />
            <span className="text-gray-700">Access to public documents</span>
          </li>
          <li className="flex items-center">
            <X className="h-4 w-4 text-red-500 mr-3" />
            <span className="text-gray-400">Advanced filters</span>
          </li>
          <li className="flex items-center">
            <X className="h-4 w-4 text-red-500 mr-3" />
            <span className="text-gray-400">AI-powered search</span>
          </li>
        </ul>

        {isCurrentPlan('free') && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 text-sm font-medium">Current Plan</p>
          </div>
        )}
      </div>

      {/* Paid Plans */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isPopular = plan.tier === 'premium'
          const isCurrent = isCurrentPlan(plan.tier)
          
          return (
            <div
              key={plan.tier}
              className={`card relative ${
                isPopular 
                  ? 'border-2 border-primary-500 shadow-lg' 
                  : 'border border-gray-200'
              }`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-primary-500 text-white px-3 py-1 text-xs font-medium rounded-full">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="flex items-center space-x-3 mb-4">
                <div className={`p-2 rounded-lg ${
                  plan.tier === 'basic' ? 'bg-blue-100' :
                  plan.tier === 'premium' ? 'bg-purple-100' : 'bg-yellow-100'
                }`}>
                  <PlanIcon tier={plan.tier} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{plan.name}</h3>
                  <p className="text-gray-600">Professional legal research</p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline">
                  <span className="text-3xl font-bold text-gray-900">
                    ${plan.price_monthly}
                  </span>
                  <span className="text-gray-600 ml-2">/month</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  or ${plan.price_yearly}/year (save 17%)
                </p>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <Check className="h-4 w-4 text-green-500 mr-3 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="space-y-2">
                {isCurrent ? (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-green-800 text-sm font-medium">Current Plan</p>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleSubscribe(plan.tier, 'monthly')}
                      className={`w-full py-2 px-4 rounded-lg font-medium transition-colors duration-200 ${
                        isPopular
                          ? 'bg-primary-600 hover:bg-primary-700 text-white'
                          : 'bg-gray-900 hover:bg-gray-800 text-white'
                      }`}
                    >
                      Subscribe Monthly
                    </button>
                    <button
                      onClick={() => handleSubscribe(plan.tier, 'yearly')}
                      className="w-full py-2 px-4 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors duration-200"
                    >
                      Subscribe Yearly (Save 17%)
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* FAQ or Additional Info */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Frequently Asked Questions</h2>
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900">Can I change my plan anytime?</h3>
            <p className="text-gray-600 text-sm mt-1">
              Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-gray-900">What payment methods do you accept?</h3>
            <p className="text-gray-600 text-sm mt-1">
              We accept all major credit cards and debit cards through our secure payment processor.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-gray-900">Is there a free trial?</h3>
            <p className="text-gray-600 text-sm mt-1">
              The free plan allows you to explore our basic features. You can upgrade anytime to access advanced features.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SubscriptionPage