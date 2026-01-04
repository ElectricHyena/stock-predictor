export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">About Stock Predictor</h1>

        <div className="space-y-8">
          <section className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Our Mission</h2>
            <p className="text-gray-300 leading-relaxed">
              Stock Predictor aims to empower traders and investors with advanced machine learning analysis to identify stocks with predictable price movements. We believe that data-driven insights can help you make better trading decisions.
            </p>
          </section>

          <section className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">How It Works</h2>
            <div className="space-y-4 text-gray-300">
              <p>
                Our platform uses sophisticated machine learning models to analyze:
              </p>
              <ul className="list-disc list-inside space-y-2">
                <li>Historical price patterns and trends</li>
                <li>Trading volume and market sentiment</li>
                <li>Technical indicators and chart patterns</li>
                <li>News sentiment and market catalysts</li>
              </ul>
              <p>
                Based on this analysis, we calculate a predictability score for each stock, indicating how likely it is to follow predictable patterns.
              </p>
            </div>
          </section>

          <section className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Predictability Score</h2>
            <p className="text-gray-300 mb-4">
              Our proprietary predictability score ranges from 0-100 and is based on four key factors:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-bold text-white mb-2">Information (30%)</h3>
                <p className="text-gray-400 text-sm">Quality and availability of price/volume data</p>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2">Pattern (25%)</h3>
                <p className="text-gray-400 text-sm">Consistency of price movement patterns</p>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2">Timing (25%)</h3>
                <p className="text-gray-400 text-sm">Accuracy of timing predictions</p>
              </div>
              <div>
                <h3 className="font-bold text-white mb-2">Direction (20%)</h3>
                <p className="text-gray-400 text-sm">Accuracy of price direction predictions</p>
              </div>
            </div>
          </section>

          <section className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Disclaimer</h2>
            <p className="text-gray-300 leading-relaxed">
              Past performance does not guarantee future results. Stock Predictor's analysis and predictions are based on historical data and machine learning models. They should not be considered financial advice. Always conduct your own research and consult with a financial advisor before making investment decisions. Trading and investing carry risk, including the potential loss of principal.
            </p>
          </section>

          <section className="bg-slate-800/50 backdrop-blur rounded-lg p-6 border border-slate-700">
            <h2 className="text-2xl font-bold text-white mb-4">Contact Us</h2>
            <p className="text-gray-300 mb-4">
              Have questions or feedback? We'd love to hear from you.
            </p>
            <div className="space-y-2 text-gray-400">
              <p>Email: support@stockpredictor.com</p>
              <p>Twitter: @StockPredictor</p>
              <p>GitHub: github.com/stockpredictor</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
