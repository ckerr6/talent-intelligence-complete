import { useState } from 'react';
import { X, Users, Sparkles, Copy, Check, Send, ArrowRight } from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { tokens } from '../../styles/tokens';
import type { PathNode, PathEdge } from '../../types';

interface IntroRequestModalProps {
  targetPerson: {
    person_id: string;
    full_name: string;
    headline?: string;
  };
  mutualConnection: PathNode;
  connectionContext?: PathEdge;
  onClose: () => void;
  onSend?: (message: string) => void;
}

export default function IntroRequestModal({
  targetPerson,
  mutualConnection,
  connectionContext,
  onClose,
  onSend
}: IntroRequestModalProps) {
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [generatedMessage, setGeneratedMessage] = useState('');
  const [customNote, setCustomNote] = useState('');
  const [step, setStep] = useState<'preview' | 'customize' | 'send'>('preview');

  const handleGenerateMessage = async () => {
    setGenerating(true);
    
    // Simulate AI message generation
    setTimeout(() => {
      const connectionType = connectionContext?.type === 'coworker' ? 'worked together' : 'collaborated on GitHub';
      const connectionDetail = connectionContext?.company || connectionContext?.repo || '';
      
      const message = `Hi ${mutualConnection.name.split(' ')[0]},

I hope this message finds you well! I'm reaching out because I noticed you ${connectionType}${connectionDetail ? ` at ${connectionDetail}` : ''} with ${targetPerson.full_name}.

I'm currently recruiting for an exciting opportunity that I think would be a great fit for ${targetPerson.full_name.split(' ')[0]}${targetPerson.headline ? `, given their experience as ${targetPerson.headline}` : ''}.

Would you be comfortable making an introduction? I'd really appreciate your help connecting, and I promise to be respectful of their time.

${customNote ? `\nAdditional context:\n${customNote}\n` : ''}
Happy to provide more details about the role if that would be helpful!

Thanks so much,
[Your Name]`;

      setGeneratedMessage(message);
      setGenerating(false);
      setStep('customize');
    }, 1500);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedMessage);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSend = () => {
    if (onSend) {
      onSend(generatedMessage);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-white rounded-xl shadow-2xl m-4">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Request Introduction</h2>
              <p className="text-sm text-emerald-100">
                Via {mutualConnection.name} → {targetPerson.full_name}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            icon={<X className="w-5 h-5" />}
            className="text-white hover:bg-white/20"
          />
        </div>

        <div className="p-6 space-y-6">
          {/* Connection Path Visualization */}
          <Card hierarchy="secondary">
            <div className="flex items-center justify-between gap-4">
              {/* You */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-16 h-16 rounded-full bg-indigo-100 border-4 border-indigo-600 flex items-center justify-center">
                  <span className="text-indigo-600 font-bold text-lg">You</span>
                </div>
                <span className="mt-2 text-sm font-medium text-gray-900">You</span>
                <span className="text-xs text-gray-500">Requester</span>
              </div>

              {/* Arrow */}
              <div className="flex flex-col items-center">
                <ArrowRight className="w-6 h-6 text-gray-400" />
                <div className="mt-1 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                  {connectionContext?.type === 'coworker' ? '👔' : '💻'}
                  {connectionContext?.company || connectionContext?.repo || 'Connection'}
                </div>
              </div>

              {/* Mutual Connection */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-16 h-16 rounded-full bg-emerald-100 border-4 border-emerald-600 flex items-center justify-center">
                  <span className="text-emerald-600 font-bold">
                    {mutualConnection.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                  </span>
                </div>
                <span className="mt-2 text-sm font-medium text-gray-900 text-center max-w-[120px] truncate">
                  {mutualConnection.name}
                </span>
                <span className="text-xs text-gray-500">Connector</span>
              </div>

              {/* Arrow */}
              <div className="flex flex-col items-center">
                <ArrowRight className="w-6 h-6 text-gray-400" />
                <div className="mt-1 px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                  Intro
                </div>
              </div>

              {/* Target */}
              <div className="flex flex-col items-center flex-1">
                <div className="w-16 h-16 rounded-full bg-cyan-100 border-4 border-cyan-600 flex items-center justify-center">
                  <span className="text-cyan-600 font-bold">
                    {targetPerson.full_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                  </span>
                </div>
                <span className="mt-2 text-sm font-medium text-gray-900 text-center max-w-[120px] truncate">
                  {targetPerson.full_name}
                </span>
                <span className="text-xs text-gray-500">Target</span>
              </div>
            </div>
          </Card>

          {/* Why This Works */}
          <Card hierarchy="secondary">
            <div className="flex gap-3">
              <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-sm text-gray-900 mb-2">Why This Works</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-600">✓</span>
                    <span>
                      You {connectionContext?.type === 'coworker' ? 'worked with' : 'collaborated with'} {mutualConnection.name}
                      {connectionContext?.company && ` at ${connectionContext.company}`}
                      {connectionContext?.repo && ` on ${connectionContext.repo}`}
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-600">✓</span>
                    <span>
                      {mutualConnection.name.split(' ')[0]} knows {targetPerson.full_name.split(' ')[0]} personally
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-600">✓</span>
                    <span>
                      Warm introductions have 3-5x better response rates than cold outreach
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Step 1: Preview */}
          {step === 'preview' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Add Context (Optional)
                </label>
                <textarea
                  value={customNote}
                  onChange={(e) => setCustomNote(e.target.value)}
                  placeholder="Why are you reaching out? What makes this opportunity special?"
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">
                  This helps {mutualConnection.name.split(' ')[0]} understand your request and craft a better introduction
                </p>
              </div>

              <Button
                onClick={handleGenerateMessage}
                icon={<Sparkles className="w-4 h-4" />}
                className="w-full"
                loading={generating}
              >
                {generating ? 'Generating AI Message...' : 'Generate Introduction Request'}
              </Button>
            </div>
          )}

          {/* Step 2: Customize */}
          {step === 'customize' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" />
                  <span className="font-semibold text-gray-900">AI-Generated Message</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setStep('preview');
                    setGeneratedMessage('');
                  }}
                  icon={<ArrowRight className="w-4 h-4 rotate-180" />}
                >
                  Back
                </Button>
              </div>

              <Card>
                <div className="mb-3">
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    TO: {mutualConnection.name}
                  </label>
                  {mutualConnection.headline && (
                    <p className="text-xs text-gray-500">{mutualConnection.headline}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">MESSAGE</label>
                  <textarea
                    value={generatedMessage}
                    onChange={(e) => setGeneratedMessage(e.target.value)}
                    rows={14}
                    className="w-full text-sm text-gray-900 bg-transparent border-0 p-0 focus:ring-0 resize-none"
                  />
                </div>
              </Card>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  onClick={() => setStep('send')}
                  icon={<Send className="w-4 h-4" />}
                  className="flex-1"
                >
                  Review & Send
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCopy}
                  icon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                >
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>

              {/* Tips */}
              <Card hierarchy="secondary">
                <div className="flex gap-3">
                  <Sparkles className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-sm text-gray-900 mb-1">✨ Best Practices</h4>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• Be specific about why this is a good match</li>
                      <li>• Make it easy for them to say yes (provide context)</li>
                      <li>• Offer to provide more details if needed</li>
                      <li>• Thank them for their time and consideration</li>
                      <li>• Follow up if no response in 5-7 days</li>
                    </ul>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Step 3: Send Confirmation */}
          {step === 'send' && (
            <div className="space-y-4 text-center py-6">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                <Send className="w-8 h-8 text-emerald-600" />
              </div>
              
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Ready to Send?</h3>
                <p className="text-gray-600">
                  Your introduction request will be sent to {mutualConnection.name}
                </p>
              </div>

              <Card hierarchy="secondary" className="text-left">
                <h4 className="font-semibold text-sm text-gray-900 mb-2">What happens next:</h4>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">1.</span>
                    <span>{mutualConnection.name.split(' ')[0]} receives your request</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">2.</span>
                    <span>They make the introduction (if comfortable)</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">3.</span>
                    <span>You receive a notification when connected</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">4.</span>
                    <span>Follow up with {targetPerson.full_name.split(' ')[0]} directly</span>
                  </div>
                </div>
              </Card>

              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setStep('customize')}
                  className="flex-1"
                >
                  Edit Message
                </Button>
                <Button
                  onClick={handleSend}
                  icon={<Send className="w-4 h-4" />}
                  className="flex-1"
                >
                  Send Introduction Request
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

