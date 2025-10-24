import { useState, useEffect } from 'react';
import {
  Filter, X, Sparkles, Save, Clock, TrendingUp,
  MapPin, Briefcase, Code, Mail, Github, Search, ChevronDown,
  Zap, Target
} from 'lucide-react';
import Button from '../common/Button';
import Card from '../common/Card';
import Badge from '../common/Badge';

export interface SmartFilterValues {
  // Basic
  companies: string[];
  locations: string[];
  titles: string[];
  skills: string[];
  
  // Boolean
  has_email?: boolean;
  has_github?: boolean;
  has_linkedin?: boolean;
  
  // Ranges
  years_of_experience?: { min?: number; max?: number };
  github_stars?: { min?: number; max?: number };
  merged_prs?: { min?: number; max?: number };
  
  // Network
  max_network_distance?: number;
  
  // Date
  last_active_within_days?: number;
}

interface AIFilterSuggestion {
  id: string;
  label: string;
  description: string;
  filters: Partial<SmartFilterValues>;
  icon: JSX.Element;
  useCase: string;
}

interface FilterPreset {
  id: string;
  name: string;
  filters: SmartFilterValues;
  lastUsed?: string;
  useCount: number;
}

interface SmartFiltersProps {
  initialFilters?: SmartFilterValues;
  onFiltersChange: (filters: SmartFilterValues) => void;
  onSearch: () => void;
  resultCount?: number;
  isLoading?: boolean;
}

// AI-Powered Filter Suggestions
const AI_SUGGESTIONS: AIFilterSuggestion[] = [
  {
    id: 'senior-blockchain',
    label: 'Senior Blockchain Engineers',
    description: 'Experienced engineers with Ethereum/Solidity experience',
    filters: {
      titles: ['Senior Engineer', 'Staff Engineer', 'Principal Engineer'],
      skills: ['Solidity', 'Ethereum', 'Smart Contracts'],
      years_of_experience: { min: 5 },
      merged_prs: { min: 20 }
    },
    icon: <Code className="w-4 h-4" />,
    useCase: 'Building DeFi protocol'
  },
  {
    id: 'reachable-talent',
    label: 'Highly Reachable Candidates',
    description: 'Verified email + active GitHub + close network',
    filters: {
      has_email: true,
      has_github: true,
      max_network_distance: 2,
      last_active_within_days: 90
    },
    icon: <Target className="w-4 h-4" />,
    useCase: 'Quick hiring needs'
  },
  {
    id: 'rising-stars',
    label: 'Rising Stars',
    description: 'Early career with high GitHub activity',
    filters: {
      years_of_experience: { min: 2, max: 5 },
      merged_prs: { min: 30 },
      github_stars: { min: 50 }
    },
    icon: <TrendingUp className="w-4 h-4" />,
    useCase: 'Growth-stage startups'
  },
  {
    id: 'sf-bay-area',
    label: 'San Francisco Bay Area',
    description: 'Local talent or open to relocation',
    filters: {
      locations: ['San Francisco', 'Bay Area', 'Palo Alto', 'Mountain View'],
      has_email: true
    },
    icon: <MapPin className="w-4 h-4" />,
    useCase: 'On-site roles'
  }
];

const POPULAR_COMPANIES = [
  'Google', 'Meta', 'Amazon', 'Apple', 'Microsoft',
  'Coinbase', 'Uniswap', 'Compound', 'Aave', 'MakerDAO',
  'Stripe', 'Airbnb', 'Uber', 'Twitter', 'Snap'
];

const POPULAR_LOCATIONS = [
  'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
  'Remote', 'Los Angeles, CA', 'Boston, MA', 'Chicago, IL'
];

const POPULAR_SKILLS = [
  'Solidity', 'Ethereum', 'Smart Contracts', 'DeFi', 'Web3',
  'React', 'TypeScript', 'Node.js', 'Python', 'Go',
  'Rust', 'GraphQL', 'PostgreSQL', 'AWS', 'Kubernetes'
];

const DEFAULT_FILTERS: SmartFilterValues = {
  companies: [],
  locations: [],
  titles: [],
  skills: []
};

export default function SmartFilters({
  initialFilters,
  onFiltersChange,
  onSearch,
  resultCount,
  isLoading = false
}: SmartFiltersProps) {
  const [filters, setFilters] = useState<SmartFilterValues>(initialFilters || DEFAULT_FILTERS);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['basic']));
  const [showAISuggestions, setShowAISuggestions] = useState(true);
  const [showPresets, setShowPresets] = useState(false);
  const [savedPresets, setSavedPresets] = useState<FilterPreset[]>([]);

  // Load saved presets from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('filterPresets');
    if (saved) {
      setSavedPresets(JSON.parse(saved));
    }
  }, []);

  const handleFilterUpdate = (key: keyof SmartFilterValues, value: any) => {
    const updated = { ...filters, [key]: value };
    setFilters(updated);
    onFiltersChange(updated);
  };

  const handleArrayAdd = (key: keyof SmartFilterValues, value: string) => {
    const current = (filters[key] as string[]) || [];
    if (!current.includes(value)) {
      handleFilterUpdate(key, [...current, value]);
    }
  };

  const handleArrayRemove = (key: keyof SmartFilterValues, value: string) => {
    const current = (filters[key] as string[]) || [];
    handleFilterUpdate(key, current.filter(v => v !== value));
  };

  const handleApplySuggestion = (suggestion: AIFilterSuggestion) => {
    const updated = { ...filters, ...suggestion.filters };
    setFilters(updated);
    onFiltersChange(updated);
    setShowAISuggestions(false);
  };

  const handleSavePreset = () => {
    const name = prompt('Name this filter preset:');
    if (!name) return;

    const preset: FilterPreset = {
      id: Date.now().toString(),
      name,
      filters,
      lastUsed: new Date().toISOString(),
      useCount: 1
    };

    const updated = [preset, ...savedPresets];
    setSavedPresets(updated);
    localStorage.setItem('filterPresets', JSON.stringify(updated));
  };

  const handleLoadPreset = (preset: FilterPreset) => {
    setFilters(preset.filters);
    onFiltersChange(preset.filters);
    setShowPresets(false);
  };

  const handleClearAll = () => {
    const cleared: SmartFilterValues = {
      companies: [],
      locations: [],
      titles: [],
      skills: [],
      has_email: undefined,
      has_github: undefined,
      has_linkedin: undefined
    };
    setFilters(cleared);
    onFiltersChange(cleared);
  };

  const toggleSection = (section: string) => {
    const updated = new Set(expandedSections);
    if (updated.has(section)) {
      updated.delete(section);
    } else {
      updated.add(section);
    }
    setExpandedSections(updated);
  };

  const getActiveFilterCount = (): number => {
    let count = 0;
    if (filters.companies?.length) count += filters.companies.length;
    if (filters.locations?.length) count += filters.locations.length;
    if (filters.titles?.length) count += filters.titles.length;
    if (filters.skills?.length) count += filters.skills.length;
    if (filters.has_email) count++;
    if (filters.has_github) count++;
    if (filters.years_of_experience) count++;
    if (filters.merged_prs) count++;
    return count;
  };

  const activeCount = getActiveFilterCount();

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Filter className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                Smart Filters
                {activeCount > 0 && (
                  <Badge variant="primary">{activeCount} active</Badge>
                )}
              </h3>
              <p className="text-sm text-gray-600">
                {resultCount !== undefined ? (
                  isLoading ? (
                    <span className="text-gray-400">Searching...</span>
                  ) : (
                    <span className="text-emerald-600 font-semibold">
                      {resultCount.toLocaleString()} candidates found
                    </span>
                  )
                ) : (
                  'Refine your search with advanced filters'
                )}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {savedPresets.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPresets(!showPresets)}
                icon={<Clock className="w-4 h-4" />}
              >
                Presets ({savedPresets.length})
              </Button>
            )}
            {activeCount > 0 && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSavePreset}
                  icon={<Save className="w-4 h-4" />}
                >
                  Save
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearAll}
                  icon={<X className="w-4 h-4" />}
                >
                  Clear All
                </Button>
              </>
            )}
            <Button
              onClick={onSearch}
              icon={<Search className="w-4 h-4" />}
              loading={isLoading}
            >
              Search
            </Button>
          </div>
        </div>

        {/* Saved Presets */}
        {showPresets && savedPresets.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Saved Filter Presets</h4>
            <div className="grid grid-cols-2 gap-2">
              {savedPresets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handleLoadPreset(preset)}
                  className="p-3 text-left border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all"
                >
                  <div className="font-semibold text-sm text-gray-900">{preset.name}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Used {preset.useCount} time{preset.useCount !== 1 ? 's' : ''}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* AI Suggestions */}
      {showAISuggestions && activeCount === 0 && (
        <Card hierarchy="secondary" className="bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="font-bold text-gray-900">AI-Powered Suggestions</h4>
                  <p className="text-sm text-gray-600">Common searches to get you started</p>
                </div>
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={() => setShowAISuggestions(false)}
                  icon={<X className="w-3 h-3" />}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {AI_SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    onClick={() => handleApplySuggestion(suggestion)}
                    className="p-4 text-left bg-white border-2 border-transparent rounded-lg hover:border-amber-500 hover:shadow-md transition-all group"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center group-hover:bg-amber-500 transition-colors">
                        {suggestion.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm text-gray-900 truncate">
                          {suggestion.label}
                        </div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{suggestion.description}</p>
                    <Badge variant="info" size="xs">{suggestion.useCase}</Badge>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Filter Sections */}
      <Card>
        {/* Companies Filter */}
        <FilterSection
          title="Companies"
          icon={<Briefcase className="w-4 h-4" />}
          isExpanded={expandedSections.has('companies')}
          onToggle={() => toggleSection('companies')}
          activeCount={filters.companies?.length || 0}
        >
          <MultiSelectFilter
            values={filters.companies || []}
            suggestions={POPULAR_COMPANIES}
            onAdd={(value) => handleArrayAdd('companies', value)}
            onRemove={(value) => handleArrayRemove('companies', value)}
            placeholder="Add companies (e.g., Coinbase, Google)"
          />
        </FilterSection>

        {/* Locations Filter */}
        <FilterSection
          title="Locations"
          icon={<MapPin className="w-4 h-4" />}
          isExpanded={expandedSections.has('locations')}
          onToggle={() => toggleSection('locations')}
          activeCount={filters.locations?.length || 0}
        >
          <MultiSelectFilter
            values={filters.locations || []}
            suggestions={POPULAR_LOCATIONS}
            onAdd={(value) => handleArrayAdd('locations', value)}
            onRemove={(value) => handleArrayRemove('locations', value)}
            placeholder="Add locations (e.g., San Francisco, Remote)"
          />
        </FilterSection>

        {/* Skills Filter */}
        <FilterSection
          title="Skills & Technologies"
          icon={<Code className="w-4 h-4" />}
          isExpanded={expandedSections.has('skills')}
          onToggle={() => toggleSection('skills')}
          activeCount={filters.skills?.length || 0}
        >
          <MultiSelectFilter
            values={filters.skills || []}
            suggestions={POPULAR_SKILLS}
            onAdd={(value) => handleArrayAdd('skills', value)}
            onRemove={(value) => handleArrayRemove('skills', value)}
            placeholder="Add skills (e.g., Solidity, React)"
          />
        </FilterSection>

        {/* Quick Toggles */}
        <div className="border-t border-gray-200 pt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Quick Filters</h4>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleFilterUpdate('has_email', !filters.has_email)}
              className={`
                px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all
                ${filters.has_email
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-900'
                  : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }
              `}
            >
              <Mail className="w-4 h-4 inline mr-2" />
              Has Email
            </button>
            <button
              onClick={() => handleFilterUpdate('has_github', !filters.has_github)}
              className={`
                px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all
                ${filters.has_github
                  ? 'border-cyan-500 bg-cyan-50 text-cyan-900'
                  : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }
              `}
            >
              <Github className="w-4 h-4 inline mr-2" />
              Has GitHub
            </button>
            <button
              onClick={() => handleFilterUpdate('last_active_within_days', filters.last_active_within_days ? undefined : 90)}
              className={`
                px-4 py-2 rounded-lg border-2 text-sm font-medium transition-all
                ${filters.last_active_within_days
                  ? 'border-indigo-500 bg-indigo-50 text-indigo-900'
                  : 'border-gray-300 text-gray-700 hover:border-gray-400'
                }
              `}
            >
              <Zap className="w-4 h-4 inline mr-2" />
              Recently Active
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}

// Filter Section Component
interface FilterSectionProps {
  title: string;
  icon: JSX.Element;
  isExpanded: boolean;
  onToggle: () => void;
  activeCount?: number;
  children: React.ReactNode;
}

function FilterSection({
  title,
  icon,
  isExpanded,
  onToggle,
  activeCount = 0,
  children
}: FilterSectionProps) {
  return (
    <div className="border-b border-gray-200 last:border-0">
      <button
        onClick={onToggle}
        className="w-full py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="text-gray-600">{icon}</div>
          <span className="font-semibold text-gray-900">{title}</span>
          {activeCount > 0 && (
            <Badge variant="primary" size="xs">{activeCount}</Badge>
          )}
        </div>
        <ChevronDown
          className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>
      {isExpanded && (
        <div className="pb-4 animate-in slide-in-from-top duration-200">
          {children}
        </div>
      )}
    </div>
  );
}

// Multi-Select Filter Component
interface MultiSelectFilterProps {
  values: string[];
  suggestions: string[];
  onAdd: (value: string) => void;
  onRemove: (value: string) => void;
  placeholder: string;
}

function MultiSelectFilter({
  values,
  suggestions,
  onAdd,
  onRemove,
  placeholder
}: MultiSelectFilterProps) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filteredSuggestions = suggestions.filter(
    s => !values.includes(s) && s.toLowerCase().includes(inputValue.toLowerCase())
  );

  const handleAdd = (value: string) => {
    onAdd(value);
    setInputValue('');
    setShowSuggestions(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      handleAdd(inputValue.trim());
    }
  };

  return (
    <div className="space-y-3">
      {/* Selected Values */}
      {values.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {values.map((value) => (
            <Badge
              key={value}
              variant="primary"
              onRemove={() => onRemove(value)}
            >
              {value}
            </Badge>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
        
        {/* Suggestions Dropdown */}
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {filteredSuggestions.slice(0, 10).map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleAdd(suggestion)}
                className="w-full px-4 py-2 text-left hover:bg-indigo-50 transition-colors text-sm"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

