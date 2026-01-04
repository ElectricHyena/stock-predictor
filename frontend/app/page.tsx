import React from 'react'
import Link from 'next/link'
import { TrendingUp, Search, BarChart3, Zap } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6">
              Find Predictable <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">Stocks</span>
            </h1>
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Advanced ML-powered predictability analysis. Discover which stocks are most likely to follow predictable patterns and make informed trading decisions.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/search"
                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition"
              >
                Start Searching
              </Link>
              <Link
                href="/about"
                className="px-8 py-3 border border-blue-600 text-blue-400 hover:bg-blue-600/10 font-semibold rounded-lg transition"
              >
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-12 text-center">Why Stock Predictor?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition">
              <Search className="w-12 h-12 text-blue-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Easy Search</h3>
              <p className="text-gray-400">
                Search stocks by ticker or company name. Find the stocks you're interested in instantly.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 hover:border-green-500 transition">
              <TrendingUp className="w-12 h-12 text-green-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Predictability Score</h3>
              <p className="text-gray-400">
                Get a comprehensive predictability score for each stock with detailed component analysis.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 hover:border-yellow-500 transition">
              <BarChart3 className="w-12 h-12 text-yellow-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">AI Predictions</h3>
              <p className="text-gray-400">
                Leverage machine learning models to get daily price predictions with win rate statistics.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700 hover:border-purple-500 transition">
              <Zap className="w-12 h-12 text-purple-400 mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Real-Time Data</h3>
              <p className="text-gray-400">
                Get up-to-date stock prices and analysis refreshed throughout the trading day.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-4xl mx-auto bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to Find Your Next Trade?</h2>
          <p className="text-blue-100 mb-8">
            Explore thousands of stocks and find the most predictable ones with our advanced analysis tools.
          </p>
          <Link
            href="/search"
            className="inline-block px-8 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-100 transition"
          >
            Start Analyzing Now
          </Link>
        </div>
      </section>

      {/* Stats Section */}
      <section className="px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-bold text-blue-400 mb-2">10,000+</p>
              <p className="text-gray-400">Stocks Analyzed</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-green-400 mb-2">99%</p>
              <p className="text-gray-400">Data Accuracy</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-purple-400 mb-2">24/7</p>
              <p className="text-gray-400">Real-Time Updates</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
