import { useState } from 'react';
import { Sparkles, Send, Loader2, TrendingUp, HelpCircle } from 'lucide-react';

interface AIChartBuilderProps {
  companyId: string;
  companyName: string;
}

export default function AIChartBuilder({ companyId, companyName }: AIChartBuilderProps) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const suggestedQuestions = [
    `What are the hiring trends at ${companyName}?`,
    `Where does ${companyName} recruit most of their talent from?`,
    `What technologies are most popular at ${companyName}?`,
    `How does ${companyName}'s hiring compare to industry standards?`,
    `What roles is ${companyName} focusing on?`,
    `Analyze the talent pipeline at ${companyName}`,
  ];

  const handleAsk = async () => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch('/api/market/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          company_id: companyId,
          company_name: companyName,
          provider: 'openai',
        }),
      });

      const data = await res.json();

      if (data.success) {
        setResponse(data);
      } else {
        setError(data.detail || 'Failed to get AI insights');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get AI insights');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedQuestion = (q: string) => {
    setQuestion(q);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              AI-Powered Market Intelligence
            </h2>
            <p className="text-gray-600">
              Ask natural language questions about {companyName}'s hiring patterns, talent flow, and technology trends. 
              The AI will analyze the data and provide strategic insights.
            </p>
          </div>
        </div>
      </div>

      {/* Question Input */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <label className="block text-sm font-medium text-gray-900 mb-3">
          Ask a question about {companyName}
        </label>
        
        <div className="flex items-start space-x-3">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
            placeholder={`e.g., "What are the hiring trends at ${companyName}?"`}
            rows={3}
            disabled={loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleAsk}
            disabled={!question.trim() || loading}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2 font-medium"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Ask AI</span>
              </>
            )}
          </button>
        </div>

        {/* Suggested Questions */}
        {!response && !loading && (
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-2 flex items-center">
              <HelpCircle className="w-4 h-4 mr-1" />
              Suggested questions:
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.slice(0, 4).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestedQuestion(q)}
                  className="text-sm px-3 py-2 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors border border-purple-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Loader2 className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-700 font-medium">AI is analyzing market data...</p>
          <p className="text-sm text-gray-500 mt-2">This takes about 5-10 seconds</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-900 font-semibold mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* AI Response */}
      {response && !loading && (
        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Question */}
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-gray-600">Q</span>
              </div>
              <span className="text-sm font-semibold text-gray-900">Your Question</span>
            </div>
            <p className="text-gray-700 ml-10">{response.question}</p>
          </div>

          {/* AI Answer */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-gray-900">AI Insights</span>
            </div>
            <div className="ml-10 prose prose-sm max-w-none">
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                  {response.answer}
                </div>
              </div>
            </div>
          </div>

          {/* Metadata */}
          <div className="ml-10 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center space-x-4">
                <span>Data sources: {response.data_sources?.join(', ')}</span>
                <span>•</span>
                <span>Model: GPT-4o-mini</span>
              </div>
              <span>{new Date(response.generated_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3 ml-10">
            <button
              onClick={() => {
                setQuestion('');
                setResponse(null);
              }}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
            >
              Ask Another Question
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(response.answer);
                alert('Copied to clipboard!');
              }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
            >
              Copy Insights
            </button>
          </div>
        </div>
      )}

      {/* Tips */}
      {!response && !loading && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-blue-900 font-semibold mb-3 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Tips for Better Insights
          </h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>• Be specific about what you want to know</li>
            <li>• Ask about hiring trends, talent sources, or technology focus</li>
            <li>• Request strategic recommendations or competitive analysis</li>
            <li>• Compare against industry standards or specific competitors</li>
            <li>• Ask follow-up questions to dig deeper into insights</li>
          </ul>
        </div>
      )}
    </div>
  );
}

