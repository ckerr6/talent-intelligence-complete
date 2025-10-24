import { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Search } from 'lucide-react';

export interface MultiSelectOption {
  value: string;
  label: string;
  meta?: string; // Optional metadata to display (e.g., count)
}

interface MultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  searchable?: boolean;
  maxHeight?: string;
  disabled?: boolean;
  onSearchChange?: (query: string) => void; // Callback for search input changes
}

export default function MultiSelect({
  options,
  value,
  onChange,
  placeholder = 'Select options...',
  searchable = true,
  maxHeight = '300px',
  disabled = false,
  onSearchChange,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Filter options based on search
  const filteredOptions = searchQuery
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  // Get selected option labels
  const selectedLabels = options
    .filter((opt) => value.includes(opt.value))
    .map((opt) => opt.label);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
    }
  };

  const handleSelect = (optionValue: string) => {
    if (value.includes(optionValue)) {
      // Remove from selection
      onChange(value.filter((v) => v !== optionValue));
    } else {
      // Add to selection
      onChange([...value, optionValue]);
    }
  };

  const handleRemove = (optionValue: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(value.filter((v) => v !== optionValue));
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Selected items display / trigger button */}
      <div
        onClick={handleToggle}
        className={`
          min-h-[42px] px-3 py-2 border rounded-lg 
          bg-white cursor-pointer
          transition-all duration-200
          ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'hover:border-primary-500'}
          ${isOpen ? 'border-primary-500 ring-2 ring-primary-200' : 'border-gray-300'}
        `}
      >
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 flex flex-wrap gap-1.5">
            {value.length === 0 ? (
              <span className="text-gray-400 text-sm">{placeholder}</span>
            ) : (
              selectedLabels.map((label) => {
                const option = options.find((opt) => opt.label === label);
                return (
                  <span
                    key={label}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-800 rounded text-sm font-medium"
                  >
                    {label}
                    <button
                      onClick={(e) => handleRemove(option?.value || label, e)}
                      className="hover:bg-primary-200 rounded-full p-0.5 transition-colors"
                      disabled={disabled}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                );
              })
            )}
          </div>
          <div className="flex items-center gap-1">
            {value.length > 0 && !disabled && (
              <button
                onClick={handleClear}
                className="hover:bg-gray-100 rounded p-1 transition-colors"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
            <ChevronDown
              className={`w-4 h-4 text-gray-400 transition-transform ${
                isOpen ? 'transform rotate-180' : ''
              }`}
            />
          </div>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg"
          style={{ maxHeight }}
        >
          {searchable && (
            <div className="p-2 border-b border-gray-200">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    const newQuery = e.target.value;
                    setSearchQuery(newQuery);
                    // Notify parent of search changes (for dynamic autocomplete)
                    if (onSearchChange) {
                      onSearchChange(newQuery);
                    }
                  }}
                  placeholder="Search..."
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            </div>
          )}

          <div className="overflow-y-auto" style={{ maxHeight: '250px' }}>
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-4 text-center text-gray-500 text-sm">
                No options found
              </div>
            ) : (
              filteredOptions.map((option) => {
                const isSelected = value.includes(option.value);
                return (
                  <div
                    key={option.value}
                    onClick={() => handleSelect(option.value)}
                    className={`
                      px-3 py-2 cursor-pointer transition-colors
                      flex items-center justify-between
                      ${isSelected ? 'bg-primary-50 text-primary-900' : 'hover:bg-gray-50'}
                    `}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // Controlled by parent
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                      />
                      <span className="text-sm font-medium">{option.label}</span>
                    </div>
                    {option.meta && (
                      <span className="text-xs text-gray-500">{option.meta}</span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

