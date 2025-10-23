// Core types for the Talent Intelligence Platform

export interface Person {
  person_id: string;
  full_name: string;
  linkedin_url: string;
  location?: string;
  headline?: string;
  created_at?: string;
  refreshed_at?: string;  // Changed from updated_at to match backend
}

export interface Employment {
  employment_id: string;
  person_id: string;
  company_id: string;
  company_name: string;
  title?: string;
  start_date?: string;
  end_date?: string | null;
  duration?: string;
  is_current: boolean;
}

export interface Email {
  email: string;
  email_type: string;
  is_primary: boolean;
}

export interface GitHubProfile {
  github_profile_id: string;
  github_username: string;
  github_name?: string;
  github_email?: string;
  followers: number;
  following: number;
  public_repos: number;
  bio?: string;
  location?: string;
  twitter_username?: string;
}

export interface GitHubContribution {
  contribution_id: string;
  repository_id: string;
  repo_name: string;
  repo_full_name: string; // e.g., "Uniswap/default-token-list"
  description?: string;
  language?: string;
  stars: number;
  forks: number;
  is_fork: boolean;
  contribution_count: number;
  contributed_at?: string;
  owner_company_id?: string;
  owner_company_name?: string;
}

export interface FullProfile {
  person: Person;
  employment: Employment[];
  emails: Email[];
  github_profile?: GitHubProfile;
  github_contributions: GitHubContribution[];
  network_stats?: NetworkStats;
}

export interface NetworkConnection {
  person_id: string;
  name: string;
  headline?: string;
  location?: string;
  connection_type: 'coworker' | 'github_collaborator';
  company_name?: string;
  repo_name?: string;
}

export interface NetworkPath {
  path_length: number;
  nodes: PathNode[];
  edges: PathEdge[];
}

export interface PathNode {
  person_id: string;
  name: string;
  headline?: string;
  location?: string;
  position: number;
}

export interface PathEdge {
  from: string;
  to: string;
  type: 'coworker' | 'github_collaborator' | 'unknown';
  company?: string;
  repo?: string;
}

export interface NetworkStats {
  total_connections: number;
  coworker_connections: number;
  github_connections: number;
  top_companies: Array<{
    company_name: string;
    connection_count: number;
  }>;
}

export interface CandidateScore {
  score_id: string;
  person_id: string;
  overall_score: number;
  relevance_score: number;
  code_quality_score: number;
  reachability_score: number;
  explanation: {
    relevance: string;
    code_quality: string;
    reachability: string;
  };
  scored_at: string;
}

export interface CandidateList {
  list_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  member_count: number;
  members?: ListMember[];
}

export interface ListMember {
  person_id: string;
  full_name: string;
  headline?: string;
  location?: string;
  linkedin_url: string;
  added_at: string;
  notes?: string;
}

export interface Note {
  note_id: string;
  person_id: string;
  note_text: string;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  tag: string;
  tag_type: 'manual' | 'auto' | 'ai';
  created_at: string;
}

export interface SavedSearch {
  search_id: string;
  name: string;
  filters: SearchFilters;
  created_at: string;
  last_used: string;
}

export interface SearchFilters {
  company?: string;
  location?: string;
  headline?: string;
  has_email?: boolean;
  has_github?: boolean;
  languages?: string[];
  network_distance?: number;
  min_score?: number;
}

export interface SearchResult {
  person: Person;
  score?: number;
  network_distance?: number;
  match_reasons?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    offset: number;
    limit: number;
    total: number;
  };
}

export interface Company {
  company_id: string;
  company_name: string;
  linkedin_url?: string;
  website?: string;
  employee_count?: number;
}

export interface HiringPattern {
  company_name: string;
  hire_count: number;
  common_titles: string[];
}

export interface TalentFlow {
  source: string;
  target: string;
  flow_count: number;
}

export interface TechnologyDistribution {
  language: string;
  repo_count: number;
  percentage: number;
  stars: number;
  forks: number;
}

export interface DeveloperActivity {
  active_developers: number;
  active_repositories: number;
  total_contributions: number;
  date_range: {
    start: string;
    end: string;
  };
}

