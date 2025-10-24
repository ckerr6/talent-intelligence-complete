import axios, { AxiosInstance } from 'axios';
import type {
  Person,
  FullProfile,
  PaginatedResponse,
  CandidateList,
  ListMember,
  Note,
  Tag,
  SavedSearch,
  SearchFilters,
  NetworkConnection,
  NetworkPath,
  NetworkStats,
  HiringPattern,
  TalentFlow,
  TechnologyDistribution,
  DeveloperActivity,
  Company,
} from '../types';
import type {
  AdvancedSearchFilters,
  AdvancedSearchResponse,
  JobDescriptionParseResponse,
  Technology,
  CompanyOption,
} from '../types/search';

class API {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use((config) => {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // ===== PEOPLE =====

  async searchPeople(
    filters: SearchFilters,
    offset: number = 0,
    limit: number = 50
  ): Promise<PaginatedResponse<Person>> {
    const params = new URLSearchParams();
    params.append('offset', offset.toString());
    params.append('limit', limit.toString());

    if (filters.company) params.append('company', filters.company);
    if (filters.location) params.append('location', filters.location);
    if (filters.headline) params.append('headline', filters.headline);
    if (filters.has_email !== undefined) params.append('has_email', filters.has_email.toString());
    if (filters.has_github !== undefined) params.append('has_github', filters.has_github.toString());

    const response = await this.client.get('/people', { params });
    return response.data;
  }

  async getPersonProfile(personId: string): Promise<FullProfile> {
    const response = await this.client.get(`/people/${personId}/full`);
    
    // Backend returns { success: true, data: profile }
    const rawProfile = response.data.data || response.data;
    
    // Transform flat structure to nested structure expected by frontend
    // Backend: { person_id, full_name, ..., emails, employment, github_profile }
    // Frontend expects: { person: { person_id, full_name, ... }, emails, employment, github_profile }
    const profile: FullProfile = {
      person: {
        person_id: rawProfile.person_id,
        full_name: rawProfile.full_name,
        linkedin_url: rawProfile.linkedin_url || rawProfile.normalized_linkedin_url,
        location: rawProfile.location,
        headline: rawProfile.headline,
        created_at: rawProfile.created_at || '',
        refreshed_at: rawProfile.refreshed_at || rawProfile.updated_at || '',
      },
      employment: rawProfile.employment || [],
      emails: rawProfile.emails || [],
      github_profile: rawProfile.github_profile,
      github_contributions: rawProfile.github_contributions || [],
      network_stats: rawProfile.network_stats,
    };
    
    return profile;
  }

  async getPerson(personId: string): Promise<Person> {
    const response = await this.client.get(`/people/${personId}`);
    return response.data;
  }

  // ===== NETWORK =====

  async getConnections(
    personId: string,
    connectionType?: 'coworker' | 'github_collaborator',
    limit: number = 100
  ): Promise<NetworkConnection[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (connectionType) params.append('connection_type', connectionType);

    const response = await this.client.get(`/network/connections/${personId}`, { params });
    return response.data.connections;
  }

  async findPath(sourceId: string, targetId: string, maxDepth: number = 3): Promise<NetworkPath> {
    const response = await this.client.get(`/network/path/${sourceId}/${targetId}`, {
      params: { max_depth: maxDepth },
    });
    return response.data;
  }

  async getNetworkDistance(sourceId: string, targetId: string): Promise<number | null> {
    const response = await this.client.get(`/network/distance/${sourceId}/${targetId}`);
    return response.data.degrees_of_separation;
  }

  async getNetworkStats(personId: string): Promise<NetworkStats> {
    const response = await this.client.get(`/network/stats/${personId}`);
    return response.data;
  }

  async getNetworkGraph(
    centerId: string,
    maxDegree: number = 2,
    limit: number = 100,
    companyFilter?: string,
    repoFilter?: string
  ) {
    const params: any = {
      center: centerId,
      max_degree: maxDegree,
      limit,
    };
    if (companyFilter) params.company_filter = companyFilter;
    if (repoFilter) params.repo_filter = repoFilter;

    const response = await this.client.get('/network/graph', { params });
    return response.data;
  }

  // ===== CANDIDATE LISTS =====

  async getLists(): Promise<CandidateList[]> {
    const response = await this.client.get('/workflow/lists');
    return response.data.lists;
  }

  async getList(listId: string): Promise<CandidateList> {
    const response = await this.client.get(`/workflow/lists/${listId}`);
    return response.data.list;
  }

  async createList(name: string, description?: string): Promise<CandidateList> {
    const response = await this.client.post('/workflow/lists', { name, description });
    return response.data.list;
  }

  async updateList(listId: string, name?: string, description?: string): Promise<CandidateList> {
    const response = await this.client.put(`/workflow/lists/${listId}`, { name, description });
    return response.data.list;
  }

  async deleteList(listId: string): Promise<void> {
    await this.client.delete(`/workflow/lists/${listId}`);
  }

  async addToList(listId: string, personId: string, notes?: string): Promise<ListMember> {
    const response = await this.client.post(`/workflow/lists/${listId}/members`, {
      person_id: personId,
      notes,
    });
    return response.data.member;
  }

  async removeFromList(listId: string, personId: string): Promise<void> {
    await this.client.delete(`/workflow/lists/${listId}/members/${personId}`);
  }

  // ===== NOTES =====

  async getNotes(personId: string): Promise<Note[]> {
    const response = await this.client.get(`/workflow/notes/${personId}`);
    return response.data.notes;
  }

  async createNote(personId: string, noteText: string): Promise<Note> {
    const response = await this.client.post('/workflow/notes', {
      person_id: personId,
      note_text: noteText,
    });
    return response.data.note;
  }

  async updateNote(noteId: string, noteText: string): Promise<Note> {
    const response = await this.client.put(`/workflow/notes/${noteId}`, { note_text: noteText });
    return response.data.note;
  }

  async deleteNote(noteId: string): Promise<void> {
    await this.client.delete(`/workflow/notes/${noteId}`);
  }

  // ===== TAGS =====

  async getTags(personId: string): Promise<Tag[]> {
    const response = await this.client.get(`/workflow/tags/${personId}`);
    return response.data.tags;
  }

  async addTag(personId: string, tag: string, tagType: string = 'manual'): Promise<Tag> {
    const response = await this.client.post('/workflow/tags', {
      person_id: personId,
      tag,
      tag_type: tagType,
    });
    return response.data.tag;
  }

  async removeTag(personId: string, tag: string): Promise<void> {
    await this.client.delete(`/workflow/tags/${personId}/${tag}`);
  }

  // ===== SAVED SEARCHES =====

  async getSavedSearches(): Promise<SavedSearch[]> {
    const response = await this.client.get('/workflow/searches');
    return response.data.searches;
  }

  async saveSearch(name: string, filters: SearchFilters): Promise<SavedSearch> {
    const response = await this.client.post('/workflow/searches', { name, filters });
    return response.data.search;
  }

  async deleteSearch(searchId: string): Promise<void> {
    await this.client.delete(`/workflow/searches/${searchId}`);
  }

  async markSearchUsed(searchId: string): Promise<void> {
    await this.client.put(`/workflow/searches/${searchId}/use`);
  }

  // ===== ANALYTICS =====

  async getTopRepositories(companyId?: string, limit: number = 20): Promise<any[]> {
    const params: any = { limit };
    if (companyId) params.company_id = companyId;

    const response = await this.client.get('/analytics/top-repositories', { params });
    return response.data;
  }

  async getTopContributors(companyId?: string, limit: number = 50): Promise<any[]> {
    const params: any = { limit };
    if (companyId) params.company_id = companyId;

    const response = await this.client.get('/analytics/top-contributors', { params });
    return response.data;
  }

  async getTechnologyDistribution(companyId?: string): Promise<TechnologyDistribution[]> {
    const params: any = {};
    if (companyId) params.company_id = companyId;

    const response = await this.client.get('/analytics/technology-distribution', { params });
    return response.data;
  }

  async getDeveloperActivity(companyId?: string): Promise<DeveloperActivity> {
    const params: any = {};
    if (companyId) params.company_id = companyId;

    const response = await this.client.get('/analytics/developer-activity-summary', { params });
    return response.data;
  }

  async getCompaniesForFilter(): Promise<Company[]> {
    const response = await this.client.get('/analytics/companies');
    return response.data;
  }

  // ===== STATS =====

  async getOverviewStats() {
    const response = await this.client.get('/stats/overview');
    return response.data;
  }

  // ===== AI SERVICES =====

  async generateProfileSummary(
    personId: string,
    jobContext?: string,
    provider: string = 'openai'
  ) {
    const response = await this.client.post('/ai/profile-summary', {
      person_id: personId,
      job_context: jobContext,
      provider,
    });
    return response.data;
  }

  async analyzeCodeQuality(
    personId: string,
    jobRequirements?: string,
    provider: string = 'openai'
  ) {
    const response = await this.client.post('/ai/code-analysis', {
      person_id: personId,
      job_requirements: jobRequirements,
      provider,
    });
    return response.data;
  }

  async askAI(
    personId: string,
    question: string,
    conversationHistory?: Array<{ role: string; content: string }>,
    provider: string = 'openai'
  ) {
    const response = await this.client.post('/ai/ask', {
      person_id: personId,
      question,
      conversation_history: conversationHistory,
      provider,
    });
    return response.data;
  }

  async getAIStatus() {
    const response = await this.client.get('/ai/status');
    return response.data;
  }

  // ===== ADVANCED SEARCH =====

  async advancedSearch(
    filters: AdvancedSearchFilters,
    offset: number = 0,
    limit: number = 50
  ): Promise<AdvancedSearchResponse> {
    const response = await this.client.post('/search/advanced', filters, {
      params: { offset, limit },
    });
    return response.data;
  }

  async parseJobDescription(
    jdText: string,
    autoSearch: boolean = false,
    offset: number = 0,
    limit: number = 50
  ): Promise<JobDescriptionParseResponse> {
    const response = await this.client.post('/search/parse-jd', {
      jd_text: jdText,
      auto_search: autoSearch,
    }, {
      params: { offset, limit },
    });
    return response.data;
  }

  async getAvailableTechnologies(limit: number = 100): Promise<Technology[]> {
    const response = await this.client.get('/search/technologies', {
      params: { limit },
    });
    return response.data.technologies;
  }

  async autocompleteCompanies(query: string, limit: number = 20): Promise<CompanyOption[]> {
    const response = await this.client.get('/search/companies/autocomplete', {
      params: { q: query, limit },
    });
    return response.data.companies;
  }
}

// Export singleton instance
export const api = new API();
export default api;

