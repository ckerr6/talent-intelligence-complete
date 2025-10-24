import { useState, useRef, useEffect } from 'react';
import {
  Sparkles, Send, X, Minimize2, Loader2,
  MessageSquare, Lightbulb
} from 'lucide-react';
import Button from '../common/Button';
import Badge from '../common/Badge';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  suggestions?: string[];
}

interface FloatingAIAssistantProps {
  context?: 'profile' | 'search' | 'network' | 'general';
  contextData?: {
    personName?: string;
    personId?: string;
    currentPage?: string;
  };
}

const QUICK_PROMPTS = {
  profile: [
    "Summarize this candidate's experience",
    "What are their technical strengths?",
    "How should I reach out to them?",
    "Compare them to similar candidates",
    "What questions should I ask them?"
  ],
  search: [
    "How can I refine my search?",
    "Suggest better filters",
    "Show me top blockchain engineers",
    "Find candidates at Series A startups",
    "Who has the most GitHub activity?"
  ],
  network: [
    "How can I reach this person?",
    "Who are our mutual connections?",
    "Find the shortest path to them",
    "Suggest warm intro strategy",
    "Who else knows this person?"
  ],
  general: [
    "How does this platform work?",
    "What makes a good candidate?",
    "Show me example searches",
    "Explain match scoring",
    "How do I import more data?"
  ]
};

export default function FloatingAIAssistant({
  context = 'general',
  contextData
}: FloatingAIAssistantProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hi! I'm your AI recruiting assistant. ${contextData?.personName ? `I can help you learn more about ${contextData.personName} and ` : ''}I can answer questions, provide insights, and suggest strategies. How can I help?`,
      timestamp: new Date(),
      suggestions: QUICK_PROMPTS[context].slice(0, 3)
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized) {
      inputRef.current?.focus();
    }
  }, [isOpen, isMinimized]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response (in production, call OpenAI API)
    await new Promise(resolve => setTimeout(resolve, 1500));

    const aiResponse = generateContextualResponse(text, context, contextData);
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: aiResponse.content,
      timestamp: new Date(),
      suggestions: aiResponse.suggestions
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsTyping(false);
  };

  const generateContextualResponse = (
    query: string,
    ctx: string,
    data?: { personName?: string; personId?: string }
  ) => {
    const lowerQuery = query.toLowerCase();

    // Context-specific responses
    if (ctx === 'profile' && data?.personName) {
      if (lowerQuery.includes('summarize') || lowerQuery.includes('experience')) {
        return {
          content: `${data.personName} has strong experience in blockchain development with contributions to major projects. They've demonstrated technical leadership through code quality and collaboration. I recommend reaching out via mutual connections or a personalized email highlighting their specific contributions.`,
          suggestions: ['What are their top projects?', 'How should I contact them?', 'Compare with other candidates']
        };
      }
      if (lowerQuery.includes('strength') || lowerQuery.includes('skill')) {
        return {
          content: `Key technical strengths:\n• Proven blockchain development (Solidity/Rust)\n• High-quality code (verified PRs)\n• Active open-source contributor\n• Strong collaboration skills\n\nThey would excel in senior IC roles or technical leadership positions.`,
          suggestions: ['Suggest outreach strategy', 'Find similar candidates', 'What questions to ask?']
        };
      }
      if (lowerQuery.includes('reach') || lowerQuery.includes('contact')) {
        return {
          content: `Best outreach strategy:\n1. **Warm intro** via mutual connection (highest success rate)\n2. **Personalized email** referencing their GitHub work\n3. LinkedIn InMail as backup\n\nI can generate an email template highlighting their specific contributions if you'd like!`,
          suggestions: ['Generate email template', 'Find mutual connections', 'When to reach out?']
        };
      }
    }

    if (ctx === 'search') {
      if (lowerQuery.includes('refine') || lowerQuery.includes('filter')) {
        return {
          content: `To refine your search, try:\n• Add skill filters (Solidity, Rust, React)\n• Filter by GitHub activity (20+ merged PRs)\n• Add location preferences\n• Use "has email" to prioritize reachable candidates\n\nWould you like me to suggest a specific filter combination?`,
          suggestions: ['Show me top blockchain devs', 'Find candidates with email', 'Search Series A companies']
        };
      }
    }

    // Generic helpful response
    return {
      content: `I can help with that! Here are some relevant insights:\n\n• Use natural language search for easier queries\n• Filter by GitHub activity to find active developers\n• Check match scores for quick candidate ranking\n• Use bulk operations for efficiency\n\nWhat specific aspect would you like to explore?`,
      suggestions: ['How does match scoring work?', 'Show me example searches', 'Explain filter options']
    };
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-110 flex items-center justify-center group"
        style={{ zIndex: 9999 }}
      >
        <Sparkles className="w-7 h-7 text-white animate-pulse" />
        <div className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full border-2 border-white flex items-center justify-center">
          <MessageSquare className="w-3 h-3 text-white" />
        </div>
      </button>
    );
  }

  if (isMinimized) {
    return (
      <div
        className="fixed bottom-6 right-6 z-50 bg-white rounded-lg shadow-2xl border-2 border-purple-300 p-4 flex items-center gap-3 cursor-pointer hover:shadow-purple-500/30 transition-all"
        onClick={() => setIsMinimized(false)}
        style={{ zIndex: 9999 }}
      >
        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">AI Assistant</h4>
          <p className="text-xs text-gray-600">{messages.length} messages</p>
        </div>
        <Button
          size="xs"
          variant="ghost"
          onClick={(e) => {
            e.stopPropagation();
            setIsOpen(false);
          }}
          icon={<X className="w-4 h-4" />}
        />
      </div>
    );
  }

  return (
    <div
      className="fixed bottom-6 right-6 z-50 w-96 max-h-[600px] flex flex-col bg-white rounded-xl shadow-2xl border-2 border-purple-300 overflow-hidden"
      style={{ zIndex: 9999 }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-white">AI Assistant</h3>
            <p className="text-xs text-purple-100">Always here to help</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="xs"
            variant="ghost"
            onClick={() => setIsMinimized(true)}
            icon={<Minimize2 className="w-4 h-4" />}
            className="text-white hover:bg-white/20"
          />
          <Button
            size="xs"
            variant="ghost"
            onClick={() => setIsOpen(false)}
            icon={<X className="w-4 h-4" />}
            className="text-white hover:bg-white/20"
          />
        </div>
      </div>

      {/* Context Badge */}
      {contextData?.personName && (
        <div className="px-4 py-2 bg-purple-50 border-b border-purple-200">
          <Badge variant="info" size="sm">
            Helping with: {contextData.personName}
          </Badge>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white border-2 border-gray-200 text-gray-900'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles className="w-3 h-3 text-purple-600" />
                  <span className="text-xs font-semibold text-purple-600">AI</span>
                </div>
              )}
              <p className="text-sm whitespace-pre-line">{message.content}</p>
              
              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(suggestion)}
                      className="block w-full text-left px-3 py-2 text-xs bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors"
                    >
                      <Lightbulb className="w-3 h-3 inline mr-1 text-purple-600" />
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
              
              <p className="text-xs opacity-50 mt-1">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border-2 border-gray-200 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                <span className="text-sm text-gray-600">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 bg-white border-t border-gray-200">
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {QUICK_PROMPTS[context].slice(0, 3).map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              className="flex-shrink-0 px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-900 rounded-full transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="p-4 bg-white border-t-2 border-gray-200">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(input);
              }
            }}
            placeholder="Ask me anything..."
            className="w-full pl-4 pr-12 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            disabled={isTyping}
          />
          <Button
            size="sm"
            onClick={() => handleSendMessage(input)}
            disabled={!input.trim() || isTyping}
            icon={<Send className="w-4 h-4" />}
            className="absolute right-2 top-1/2 -translate-y-1/2"
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

