import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Network, Users, Filter, Layout, X } from 'lucide-react';
import axios from 'axios';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import Badge from '../components/common/Badge';
import MultiSelect from '../components/common/MultiSelect';
import EnhancedNetworkGraph from '../components/network/EnhancedNetworkGraph';

interface Person {
  person_id: string;
  name: string;
  title?: string;
}

export default function EnhancedNetworkPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // State for multi-node selection
  const [selectedPeople, setSelectedPeople] = useState<Person[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Person[]>([]);
  const [searching, setSearching] = useState(false);
  
  // Graph controls
  const [maxDegree, setMaxDegree] = useState(2);
  const [selectedTechnologies, setSelectedTechnologies] = useState<string[]>([]);
  const [availableTechnologies, setAvailableTechnologies] = useState<{value: string; label: string}[]>([]);
  const [selectedConnectionTypes, setSelectedConnectionTypes] = useState<string[]>(['coworker', 'github_collaborator']);
  const [employmentStatus, setEmploymentStatus] = useState<string>('all');
  const [layoutType, setLayoutType] = useState<string>('force-directed');
  const [companyFilter, setCompanyFilter] = useState('');
  
  // Graph state
  const [showGraph, setShowGraph] = useState(false);
  const [graphKey, setGraphKey] = useState(0); // Force re-render
  
  // Initialize from URL params
  useEffect(() => {
    const personIds = searchParams.getAll('person');
    if (personIds.length > 0) {
      // Fetch person details
      fetchPeopleDetails(personIds);
    }
  }, []);
  
  const fetchPeopleDetails = async (personIds: string[]) => {
    try {
      const promises = personIds.map(id => 
        axios.get(`http://localhost:8000/api/people/${id}`)
      );
      const results = await Promise.all(promises);
      const people = results.map(r => ({
        person_id: r.data.person_id,
        name: r.data.full_name,
        title: r.data.headline
      }));
      setSelectedPeople(people);
      setShowGraph(true);
    } catch (err) {
      console.error('Error fetching people:', err);
    }
  };
  
  // Search for people
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    
    const timeoutId = setTimeout(async () => {
      setSearching(true);
      try {
        const response = await axios.get('http://localhost:8000/api/people', {
          params: {
            search: searchQuery,
            limit: 20
          }
        });
        
        const results = (response.data.data || []).map((p: any) => ({
          person_id: p.person_id,
          name: p.full_name,
          title: p.headline
        }));
        setSearchResults(results);
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);
    
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);
  
  // Fetch available technologies
  useEffect(() => {
    const fetchTechnologies = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/advanced/technologies');
        const techs = response.data.technologies.map((t: any) => ({
          value: t.name,
          label: `${t.name} (${t.person_count})`
        }));
        setAvailableTechnologies(techs);
      } catch (err) {
        console.error('Error fetching technologies:', err);
      }
    };
    fetchTechnologies();
  }, []);
  
  const addPerson = (person: Person) => {
    if (selectedPeople.length >= 4) {
      alert('Maximum 4 people can be selected');
      return;
    }
    
    if (selectedPeople.some(p => p.person_id === person.person_id)) {
      return; // Already added
    }
    
    setSelectedPeople([...selectedPeople, person]);
    setSearchQuery('');
    setSearchResults([]);
    
    // Update URL
    const newParams = new URLSearchParams(searchParams);
    newParams.append('person', person.person_id);
    setSearchParams(newParams);
  };
  
  const removePerson = (personId: string) => {
    setSelectedPeople(selectedPeople.filter(p => p.person_id !== personId));
    
    // Update URL
    const newParams = new URLSearchParams();
    selectedPeople
      .filter(p => p.person_id !== personId)
      .forEach(p => newParams.append('person', p.person_id));
    setSearchParams(newParams);
  };
  
  const handleVisualize = () => {
    if (selectedPeople.length < 1) {
      alert('Please select at least 1 person');
      return;
    }
    setShowGraph(true);
    setGraphKey(prev => prev + 1); // Force re-render
  };
  
  const connectionTypeOptions = [
    { value: 'coworker', label: 'Co-workers' },
    { value: 'github_collaborator', label: 'GitHub Collaborators' }
  ];
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <Network className="w-8 h-8 mr-3 text-primary-600" />
          Enhanced Network Visualization
        </h1>
        <p className="mt-2 text-gray-600">
          Explore connections between multiple people, filter by technologies, and discover network connectors
        </p>
      </div>
      
      {/* Controls Card */}
      <Card>
        <div className="space-y-6">
          {/* Person Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
              <Users className="w-4 h-4 mr-2" />
              Select People (1-4)
            </label>
            
            {/* Selected People */}
            {selectedPeople.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {selectedPeople.map(person => (
                  <Badge
                    key={person.person_id}
                    variant="primary"
                    size="lg"
                    className="flex items-center gap-2"
                  >
                    <span>{person.name}</span>
                    <button
                      onClick={() => removePerson(person.person_id)}
                      className="hover:text-red-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
            
            {/* Search Input */}
            {selectedPeople.length < 4 && (
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name, company, or title..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                
                {/* Search Results Dropdown */}
                {searchResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {searchResults.map(person => (
                      <button
                        key={person.person_id}
                        onClick={() => addPerson(person)}
                        className="w-full px-4 py-2 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium text-gray-900">{person.name}</div>
                        {person.title && (
                          <div className="text-sm text-gray-600">{person.title}</div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                
                {searching && (
                  <div className="absolute right-3 top-2.5">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
                  </div>
                )}
              </div>
            )}
          </div>
          
          {/* Filter Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Max Degree */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Degrees of Separation
              </label>
              <select
                value={maxDegree}
                onChange={(e) => setMaxDegree(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value={1}>1 degree</option>
                <option value={2}>2 degrees</option>
                <option value={3}>3 degrees</option>
              </select>
            </div>
            
            {/* Connection Types */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection Types
              </label>
              <MultiSelect
                options={connectionTypeOptions}
                value={selectedConnectionTypes}
                onChange={setSelectedConnectionTypes}
                placeholder="Select connection types..."
              />
            </div>
            
            {/* Employment Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Employment Status
              </label>
              <select
                value={employmentStatus}
                onChange={(e) => setEmploymentStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All (Current & Former)</option>
                <option value="current">Current Only</option>
                <option value="former">Former Only</option>
              </select>
            </div>
            
            {/* Technologies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Filter className="w-4 h-4 inline mr-1" />
                Filter by Technologies
              </label>
              <MultiSelect
                options={availableTechnologies}
                value={selectedTechnologies}
                onChange={setSelectedTechnologies}
                placeholder="Select technologies..."
                searchable
              />
            </div>
            
            {/* Company Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Company
              </label>
              <input
                type="text"
                value={companyFilter}
                onChange={(e) => setCompanyFilter(e.target.value)}
                placeholder="e.g., Coinbase, Google"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            
            {/* Layout Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Layout className="w-4 h-4 inline mr-1" />
                Graph Layout
              </label>
              <select
                value={layoutType}
                onChange={(e) => setLayoutType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="force-directed">Force Directed</option>
                <option value="hierarchical">Hierarchical</option>
                <option value="circular">Circular</option>
              </select>
            </div>
          </div>
          
          {/* Visualize Button */}
          <div className="flex justify-end">
            <Button
              variant="primary"
              onClick={handleVisualize}
              disabled={selectedPeople.length < 1}
              icon={<Network className="w-4 h-4" />}
            >
              {showGraph ? 'Update Visualization' : 'Visualize Network'}
            </Button>
          </div>
        </div>
      </Card>
      
      {/* Network Graph */}
      {showGraph && selectedPeople.length > 0 && (
        <EnhancedNetworkGraph
          key={graphKey}
          personIds={selectedPeople.map(p => p.person_id)}
          maxDegree={maxDegree}
          technologies={selectedTechnologies}
          connectionTypes={selectedConnectionTypes}
          employmentStatus={employmentStatus}
          companyFilter={companyFilter}
          layoutType={layoutType}
        />
      )}
    </div>
  );
}

