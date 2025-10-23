import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, Sparkles, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AskAIChatProps {
  personId: string;
  personName: string;
  onAsk: (question: string, history: Array<{ role: string; content: string }>) => Promise<string>;
}

export default function AskAIChat({ personId, personName, onAsk }: AskAIChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build conversation history for context
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const answer = await onAsk(input.trim(), history);

      const aiMessage: Message = {
        role: 'assistant',
        content: answer,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQuestions = [
    'What level of seniority are they?',
    'Do they have blockchain experience?',
    'Would they be good for a backend role?',
    'What kind of companies have they worked at?',
    'What are their strongest technical skills?',
  ];

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 flex items-center space-x-3 px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-2xl hover:shadow-3xl hover:scale-105 transition-all duration-200 z-50"
      >
        <Sparkles className="w-6 h-6" />
        <span className="font-semibold">Ask AI about {personName.split(' ')[0]}</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50 max-h-[600px]">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <MessageCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold">Ask AI</h3>
            <p className="text-xs text-purple-100">About {personName}</p>
          </div>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-white/80 hover:text-white transition-colors text-2xl leading-none"
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50" style={{ maxHeight: '400px' }}>
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Sparkles className="w-12 h-12 text-purple-300 mx-auto mb-3" />
            <p className="text-gray-600 font-medium mb-2">Ask me anything!</p>
            <p className="text-sm text-gray-500 mb-4">
              I can answer questions about {personName.split(' ')[0]}'s experience, skills, and fit for roles.
            </p>
            
            {/* Suggested Questions */}
            <div className="space-y-2 mt-4">
              <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">
                Try asking:
              </p>
              {suggestedQuestions.slice(0, 3).map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="block w-full text-left px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:border-purple-300 hover:bg-purple-50 transition-colors"
                >
                  "{question}"
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, idx) => (
          <div
            key={idx}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-800'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex items-center space-x-2 mb-2">
                  <Sparkles className="w-4 h-4 text-purple-500" />
                  <span className="text-xs font-semibold text-purple-600">AI Assistant</span>
                </div>
              )}
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
              <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-purple-100' : 'text-gray-400'}`}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 text-purple-500 animate-spin" />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Powered by GPT-4o-mini • Ask follow-up questions for deeper insights
        </p>
      </form>
    </div>
  );
}

