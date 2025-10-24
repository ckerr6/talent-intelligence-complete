// Advanced search types matching backend models

export interface AdvancedSearchFilters {
  technologies?: string[];
  companies?: string[];
  titles?: string[];
  keywords?: string[];
  location?: string;
  min_experience_years?: number;
  has_email?: boolean;
  has_github?: boolean;
  github_min_stars?: number;
  github_min_repos?: number;
}

export interface MatchExplanation {
  matched_technologies: string[];
  matched_companies: string[];
  matched_titles: string[];
  matched_keywords: string[];
  relevance_score: number;
  match_summary: string;
}

export interface SearchResultPerson {
  person_id: string;
  full_name: string;
  linkedin_url: string;
  location?: string;
  headline?: string;
  has_email: boolean;
  has_github: boolean;
  current_company?: string;
  current_title?: string;
  years_experience?: number;
  total_github_stars?: number;
  github_username?: string;
}

export interface SearchResultWithMatch {
  person: SearchResultPerson;
  match_explanation: MatchExplanation;
}

export interface AdvancedSearchResponse {
  success: boolean;
  results: SearchResultWithMatch[];
  pagination: {
    offset: number;
    limit: number;
    total: number;
  };
  filters_applied: Record<string, any>;
  total_results: number;
  search_time_ms: number;
}

export interface ParsedJobDescription {
  technologies: string[];
  companies: string[];
  job_level?: string;
  domain_expertise: string[];
  min_experience_years?: number;
  location?: string;
  keywords: string[];
  original_jd: string;
  extraction_confidence: number;
}

export interface JobDescriptionParseResponse {
  success: boolean;
  parsed_jd: ParsedJobDescription;
  search_request?: AdvancedSearchFilters;
  search_results?: AdvancedSearchResponse;
  parse_time_ms: number;
}

export interface Technology {
  name: string;
  developer_count: number;
  repo_count: number;
  total_stars: number;
}

export interface CompanyOption {
  company_id: string;
  company_name: string;
  employee_count: number;
}

