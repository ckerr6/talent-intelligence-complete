import { useState } from 'react';
import { Sparkles, Search, Wand2, ArrowRight, AlertCircle } from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';
import type { SmartFilterValues } from './SmartFilters';

interface NaturalLanguageFilterProps {
  onFiltersGenerated: (filters: SmartFilterValues) => void;
  onClear: () => void;
}

interface ParsedFilter {
  type: 'company' | 'location' | 'title' | 'skill' | 'experience' | 'boolean';
  value: string;
  confidence: number;
}

const EXAMPLE_QUERIES = [
  'Senior Solidity engineers in San Francisco',
  'Blockchain developers with 5+ years at Coinbase',
  'React engineers in NYC with email',
  'Full-stack engineers at startups with GitHub',
  'Engineers who worked at Google or Meta',
  'Remote blockchain developers with Rust experience'
];

export default function NaturalLanguageFilter({
  onFiltersGenerated,
  onClear
}: NaturalLanguageFilterProps) {
  const [query, setQuery] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsedFilters, setParsedFilters] = useState<ParsedFilter[]>([]);
  const [showParsed, setShowParsed] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseNaturalLanguage = async (text: string) => {
    setParsing(true);
    setError(null);
    
    // Simulate AI parsing (in production, call OpenAI API)
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      const parsed: ParsedFilter[] = [];
      const lowerText = text.toLowerCase();
      
      // Parse seniority/titles
      if (lowerText.includes('senior')) {
        parsed.push({ type: 'title', value: 'Senior Engineer', confidence: 0.9 });
      } else if (lowerText.includes('staff')) {
        parsed.push({ type: 'title', value: 'Staff Engineer', confidence: 0.9 });
      } else if (lowerText.includes('principal')) {
        parsed.push({ type: 'title', value: 'Principal Engineer', confidence: 0.9 });
      } else if (lowerText.includes('lead')) {
        parsed.push({ type: 'title', value: 'Lead Engineer', confidence: 0.85 });
      }
      
      // Parse skills
      const skills = ['solidity', 'rust', 'python', 'react', 'typescript', 'node.js', 'go', 'ethereum', 'blockchain', 'web3', 'defi'];
      skills.forEach(skill => {
        if (lowerText.includes(skill)) {
          parsed.push({ 
            type: 'skill', 
            value: skill.charAt(0).toUpperCase() + skill.slice(1), 
            confidence: 0.95 
          });
        }
      });
      
      // Parse locations
      const locations = [
        { names: ['san francisco', 'sf', 'bay area'], value: 'San Francisco, CA' },
        { names: ['new york', 'nyc', 'new york city'], value: 'New York, NY' },
        { names: ['seattle'], value: 'Seattle, WA' },
        { names: ['austin'], value: 'Austin, TX' },
        { names: ['remote'], value: 'Remote' },
        { names: ['los angeles', 'la'], value: 'Los Angeles, CA' },
        { names: ['boston'], value: 'Boston, MA' }
      ];
      
      locations.forEach(loc => {
        if (loc.names.some(name => lowerText.includes(name))) {
          parsed.push({ type: 'location', value: loc.value, confidence: 0.9 });
        }
      });
      
      // Parse companies
      const companies = ['google', 'meta', 'facebook', 'amazon', 'apple', 'microsoft', 'coinbase', 'uniswap', 'stripe', 'airbnb'];
      companies.forEach(company => {
        if (lowerText.includes(company)) {
          parsed.push({ 
            type: 'company', 
            value: company.charAt(0).toUpperCase() + company.slice(1), 
            confidence: 0.95 
          });
        }
      });
      
      // Parse booleans
      if (lowerText.includes('email') || lowerText.includes('contact')) {
        parsed.push({ type: 'boolean', value: 'has_email', confidence: 0.85 });
      }
      if (lowerText.includes('github')) {
        parsed.push({ type: 'boolean', value: 'has_github', confidence: 0.9 });
      }
      
      // Parse experience
      const expMatch = lowerText.match(/(\d+)\+?\s*years?/);
      if (expMatch) {
        parsed.push({ 
          type: 'experience', 
          value: `${expMatch[1]}+ years`, 
          confidence: 0.85 
        });
      }
      
      if (parsed.length === 0) {
        setError('Could not understand the query. Try something like: "Senior engineers in SF with Solidity"');
      } else {
        setParsedFilters(parsed);
        setShowParsed(true);
      }
      
    } catch (err) {
      setError('Failed to parse query. Please try again.');
    } finally {
      setParsing(false);
    }
  };

  const handleApplyFilters = () => {
    const filters: SmartFilterValues = {
      companies: parsedFilters.filter(f => f.type === 'company').map(f => f.value),
      locations: parsedFilters.filter(f => f.type === 'location').map(f => f.value),
      titles: parsedFilters.filter(f => f.type === 'title').map(f => f.value),
      skills: parsedFilters.filter(f => f.type === 'skill').map(f => f.value),
      has_email: parsedFilters.some(f => f.value === 'has_email') || undefined,
      has_github: parsedFilters.some(f => f.value === 'has_github') || undefined,
    };
    
    onFiltersGenerated(filters);
    setShowParsed(false);
  };

  const handleClear = () => {
    setQuery('');
    setParsedFilters([]);
    setShowParsed(false);
    setError(null);
    onClear();
  };

  return (
    <Card className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              Natural Language Search
              <Badge variant="info" size="xs">AI-Powered</Badge>
            </h3>
            <p className="text-sm text-gray-600">Describe what you're looking for in plain English</p>
          </div>
        </div>

        {/* Input */}
        <div className="relative">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && query.trim()) {
                  parseNaturalLanguage(query);
                }
              }}
              placeholder='Try: "Senior Solidity engineers in San Francisco with email"'
              className="w-full pl-12 pr-32 py-4 text-lg border-2 border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 bg-white"
              disabled={parsing}
            />
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
              {query && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleClear}
                >
                  Clear
                </Button>
              )}
              <Button
                size="sm"
                onClick={() => parseNaturalLanguage(query)}
                disabled={!query.trim() || parsing}
                loading={parsing}
                icon={<Wand2 className="w-4 h-4" />}
              >
                {parsing ? 'Parsing...' : 'Parse'}
              </Button>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-900">{error}</p>
              <p className="text-xs text-red-700 mt-1">Try using example queries below</p>
            </div>
          </div>
        )}

        {/* Parsed Filters Preview */}
        {showParsed && parsedFilters.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                Understood as:
              </h4>
              <Button
                size="xs"
                variant="ghost"
                onClick={() => setShowParsed(false)}
              >
                Edit
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {parsedFilters.map((filter, idx) => (
                <div
                  key={idx}
                  className="group relative"
                >
                  <Badge
                    variant={
                      filter.type === 'company' ? 'primary' :
                      filter.type === 'location' ? 'info' :
                      filter.type === 'skill' ? 'success' :
                      filter.type === 'title' ? 'warning' :
                      'secondary'
                    }
                    size="md"
                  >
                    {filter.value}
                  </Badge>
                  {/* Confidence indicator */}
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full border-2 border-purple-300 flex items-center justify-center text-xs font-bold text-purple-600">
                    {Math.round(filter.confidence * 100)}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                onClick={handleApplyFilters}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                className="flex-1"
              >
                Apply These Filters
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowParsed(false)}
              >
                Refine
              </Button>
            </div>
          </div>
        )}

        {/* Example Queries */}
        {!showParsed && !parsing && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Example searches:</p>
            <div className="grid grid-cols-2 gap-2">
              {EXAMPLE_QUERIES.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(example);
                    parseNaturalLanguage(example);
                  }}
                  className="text-left p-3 text-sm bg-white border-2 border-gray-200 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-all"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Tips */}
        <Card hierarchy="secondary" className="bg-white/50">
          <div className="text-xs text-gray-600 space-y-1">
            <p className="font-semibold text-gray-900">💡 Pro Tips:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Use seniority levels: "Senior", "Staff", "Principal"</li>
              <li>Mention specific technologies: "Solidity", "React", "Rust"</li>
              <li>Add location preferences: "in San Francisco", "remote"</li>
              <li>Specify requirements: "with email", "with GitHub"</li>
            </ul>
          </div>
        </Card>
      </div>
    </Card>
  );
}

