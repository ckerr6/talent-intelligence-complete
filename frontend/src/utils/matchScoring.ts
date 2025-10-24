/**
 * Match Scoring Algorithm
 * 
 * Calculates a 0-100 score for how well a candidate matches search criteria
 * Factors: Email availability, GitHub presence, PR activity, network distance, experience
 */

import type { Person, Email, GitHubProfile, GitHubContribution } from '../types';

export interface MatchScoreFactors {
  hasEmail: boolean;
  hasGitHub: boolean;
  mergedPRs: number;
  githubStars: number;
  networkDistance?: number;
  yearsExperience?: number;
  recentActivity?: boolean;
}

export interface MatchScoreBreakdown {
  totalScore: number;
  factors: {
    email: { score: number; weight: number; label: string };
    github: { score: number; weight: number; label: string };
    contributions: { score: number; weight: number; label: string };
    network: { score: number; weight: number; label: string };
    experience: { score: number; weight: number; label: string };
  };
  tier: 'excellent' | 'good' | 'average' | 'low';
  color: string;
  badge: string;
}

/**
 * Calculate match score for a candidate
 */
export function calculateMatchScore(
  person: Person,
  emails?: Email[],
  githubProfile?: GitHubProfile,
  _githubContributions?: GitHubContribution[],
  networkDistance?: number
): MatchScoreBreakdown {
  const factors: MatchScoreFactors = {
    hasEmail: !!(emails && emails.length > 0),
    hasGitHub: !!githubProfile,
    mergedPRs: githubProfile?.total_merged_prs || 0,
    githubStars: githubProfile?.total_stars_earned || 0,
    networkDistance,
    yearsExperience: calculateYearsOfExperience(person),
    recentActivity: isRecentlyActive(person, githubProfile)
  };

  // Score components (out of 100)
  const emailScore = factors.hasEmail ? 30 : 0;
  
  const githubScore = factors.hasGitHub ? 15 : 0;
  
  const contributionScore = Math.min(
    30,
    (factors.mergedPRs * 0.5) + (factors.githubStars * 0.1)
  );
  
  const networkScore = factors.networkDistance
    ? Math.max(0, 15 - (factors.networkDistance * 5))
    : 0;
  
  const experienceScore = factors.yearsExperience
    ? Math.min(10, factors.yearsExperience * 2)
    : 5;

  const totalScore = Math.min(
    100,
    emailScore + githubScore + contributionScore + networkScore + experienceScore
  );

  // Determine tier and styling
  let tier: MatchScoreBreakdown['tier'];
  let color: string;
  let badge: string;

  if (totalScore >= 80) {
    tier = 'excellent';
    color = '#10B981'; // emerald-500
    badge = '🎯 Excellent Match';
  } else if (totalScore >= 60) {
    tier = 'good';
    color = '#06B6D4'; // cyan-500
    badge = '✓ Good Match';
  } else if (totalScore >= 40) {
    tier = 'average';
    color = '#F59E0B'; // amber-500
    badge = '~ Average Match';
  } else {
    tier = 'low';
    color = '#6B7280'; // gray-500
    badge = '• Low Match';
  }

  return {
    totalScore: Math.round(totalScore),
    factors: {
      email: {
        score: emailScore,
        weight: 30,
        label: factors.hasEmail ? 'Verified Email' : 'No Email'
      },
      github: {
        score: githubScore,
        weight: 15,
        label: factors.hasGitHub ? 'GitHub Profile' : 'No GitHub'
      },
      contributions: {
        score: Math.round(contributionScore),
        weight: 30,
        label: `${factors.mergedPRs} PRs, ${factors.githubStars} stars`
      },
      network: {
        score: Math.round(networkScore),
        weight: 15,
        label: factors.networkDistance
          ? `${factors.networkDistance}° connection`
          : 'Not in network'
      },
      experience: {
        score: Math.round(experienceScore),
        weight: 10,
        label: factors.yearsExperience
          ? `${factors.yearsExperience} years exp`
          : 'Unknown experience'
      }
    },
    tier,
    color,
    badge
  };
}

/**
 * Calculate years of experience from person data
 * (Simplified - in production would parse employment history)
 */
function calculateYearsOfExperience(_person: Person): number | undefined {
  // TODO: Parse employment history to calculate actual experience
  // For now, return undefined
  return undefined;
}

/**
 * Check if candidate has recent activity
 */
function isRecentlyActive(person: Person, githubProfile?: GitHubProfile): boolean {
  if (githubProfile?.enriched_at) {
    const enrichedDate = new Date(githubProfile.enriched_at);
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    return enrichedDate > ninetyDaysAgo;
  }
  
  if (person.refreshed_at) {
    const refreshedDate = new Date(person.refreshed_at);
    const ninetyDaysAgo = new Date();
    ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);
    return refreshedDate > ninetyDaysAgo;
  }
  
  return false;
}

/**
 * Get color class for match score
 */
export function getMatchScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  if (score >= 60) return 'text-cyan-600 bg-cyan-50 border-cyan-200';
  if (score >= 40) return 'text-amber-600 bg-amber-50 border-amber-200';
  return 'text-gray-600 bg-gray-50 border-gray-200';
}

/**
 * Get badge variant for match score
 */
export function getMatchScoreBadgeVariant(score: number): 'success' | 'info' | 'warning' | 'default' {
  if (score >= 80) return 'success';
  if (score >= 60) return 'info';
  if (score >= 40) return 'warning';
  return 'default';
}

/**
 * Format match score for display
 */
export function formatMatchScore(score: number): string {
  return `${Math.round(score)}%`;
}

/**
 * Get explanation for match score
 */
export function getMatchScoreExplanation(breakdown: MatchScoreBreakdown): string {
  const { factors } = breakdown;
  const parts: string[] = [];

  if (factors.email.score > 0) {
    parts.push('✓ Verified email available');
  }
  if (factors.github.score > 0) {
    parts.push('✓ Active GitHub profile');
  }
  if (factors.contributions.score >= 20) {
    parts.push('✓ Strong contribution history');
  }
  if (factors.network.score >= 10) {
    parts.push('✓ Close network connection');
  }

  return parts.length > 0
    ? parts.join('\n')
    : 'Limited information available';
}

