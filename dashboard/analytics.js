// ABOUTME: Analytics dashboard JavaScript
// ABOUTME: Fetches analytics data and renders charts

const API_BASE_URL = 'http://localhost:8000/api';

let currentCompanyId = null;
let charts = {};

// Initialize dashboard
async function init() {
    console.log('[ANALYTICS] Initializing analytics dashboard...');
    
    try {
        // Load company list for filter
        await loadCompanies();
        
        // Load initial analytics data
        await loadAnalytics();
        
        console.log('[ANALYTICS] ✓ Dashboard initialized');
    } catch (error) {
        console.error('[ANALYTICS] ✗ Initialization error:', error);
        showError();
    }
}

// Load companies for filter dropdown
async function loadCompanies() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/companies?limit=100`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error('Failed to load companies');
        }
        
        const select = document.getElementById('companyFilter');
        result.data.forEach(company => {
            const option = document.createElement('option');
            option.value = company.company_id;
            option.textContent = `${company.company_name} (${company.employee_count} employees)`;
            select.appendChild(option);
        });
        
        console.log('[ANALYTICS] ✓ Loaded', result.data.length, 'companies');
    } catch (error) {
        console.error('[ANALYTICS] ✗ Error loading companies:', error);
    }
}

// Load all analytics data
async function loadAnalytics() {
    const companyParam = currentCompanyId ? `company_id=${currentCompanyId}` : '';
    
    try {
        // Show loading state
        document.getElementById('loadingMessage').style.display = 'block';
        document.getElementById('analyticsContent').style.display = 'none';
        document.getElementById('errorMessage').style.display = 'none';
        
        // Build URLs with proper query string formatting
        const summaryUrl = `${API_BASE_URL}/analytics/developer-activity-summary${companyParam ? '?' + companyParam : ''}`;
        const reposUrl = `${API_BASE_URL}/analytics/top-repositories?${companyParam ? companyParam + '&' : ''}limit=20`;
        const contributorsUrl = `${API_BASE_URL}/analytics/top-contributors?${companyParam ? companyParam + '&' : ''}limit=20`;
        const techUrl = `${API_BASE_URL}/analytics/technology-distribution${companyParam ? '?' + companyParam : ''}`;
        
        // Fetch all analytics data in parallel
        const [summaryRes, reposRes, contributorsRes, techRes] = await Promise.all([
            fetch(summaryUrl),
            fetch(reposUrl),
            fetch(contributorsUrl),
            fetch(techUrl)
        ]);
        
        const summary = await summaryRes.json();
        const repos = await reposRes.json();
        const contributors = await contributorsRes.json();
        const tech = await techRes.json();
        
        // Update metrics
        updateMetrics(summary.data);
        
        // Render charts
        renderTopRepositoriesChart(repos.data);
        renderTopContributorsChart(contributors.data);
        renderTechnologyDistributionChart(tech.data);
        
        // Show content
        document.getElementById('loadingMessage').style.display = 'none';
        document.getElementById('analyticsContent').style.display = 'block';
        
        console.log('[ANALYTICS] ✓ Analytics data loaded and rendered');
    } catch (error) {
        console.error('[ANALYTICS] ✗ Error loading analytics:', error);
        showError();
    }
}

// Update metric cards
function updateMetrics(summary) {
    document.getElementById('metricDevelopers').textContent = formatNumber(summary.active_developers || 0);
    document.getElementById('metricRepos').textContent = formatNumber(summary.active_repositories || 0);
    document.getElementById('metricContributions').textContent = formatNumber(summary.total_contributions || 0);
}

// Render Top Repositories Chart
function renderTopRepositoriesChart(data) {
    const ctx = document.getElementById('topReposChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.topRepos) {
        charts.topRepos.destroy();
    }
    
    // Limit to top 15 for readability
    const topData = data.slice(0, 15);
    
    charts.topRepos = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(r => truncate(r.repo_name, 30)),
            datasets: [{
                label: 'Total Contributions',
                data: topData.map(r => r.total_contributions || 0),
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const repo = topData[context.dataIndex];
                            return [
                                `Contributors: ${repo.contributor_count || 0}`,
                                `Stars: ${repo.stars || 0}`,
                                `Language: ${repo.language || 'N/A'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Contributions'
                    }
                }
            }
        }
    });
}

// Render Top Contributors Chart
function renderTopContributorsChart(data) {
    const ctx = document.getElementById('topContributorsChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.topContributors) {
        charts.topContributors.destroy();
    }
    
    // Limit to top 15 for readability
    const topData = data.slice(0, 15);
    
    charts.topContributors = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topData.map(c => truncate(c.full_name || c.github_username || 'Unknown', 25)),
            datasets: [{
                label: 'Total Contributions',
                data: topData.map(c => c.total_contributions || 0),
                backgroundColor: 'rgba(118, 75, 162, 0.8)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const contributor = topData[context.dataIndex];
                            return [
                                `Repositories: ${contributor.repo_count || 0}`,
                                `Username: @${contributor.github_username || 'N/A'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Contributions'
                    }
                }
            }
        }
    });
}

// Render Technology Distribution Chart
function renderTechnologyDistributionChart(data) {
    const ctx = document.getElementById('techDistributionChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.techDist) {
        charts.techDist.destroy();
    }
    
    // Limit to top 10 for donut chart clarity
    const topData = data.slice(0, 10);
    
    // Generate colors
    const colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(237, 100, 166, 0.8)',
        'rgba(255, 154, 158, 0.8)',
        'rgba(250, 208, 132, 0.8)',
        'rgba(52, 211, 153, 0.8)',
        'rgba(96, 165, 250, 0.8)',
        'rgba(251, 146, 60, 0.8)',
        'rgba(168, 85, 247, 0.8)',
        'rgba(236, 72, 153, 0.8)'
    ];
    
    charts.techDist = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: topData.map(t => t.language),
            datasets: [{
                data: topData.map(t => t.repo_count),
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const tech = topData[context.dataIndex];
                            return [
                                `${tech.language}: ${tech.repo_count} repos (${tech.percentage}%)`,
                                `Stars: ${formatNumber(tech.total_stars || 0)}`,
                                `Forks: ${formatNumber(tech.total_forks || 0)}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// Apply filters
function applyFilters() {
    const companySelect = document.getElementById('companyFilter');
    currentCompanyId = companySelect.value || null;
    
    const companyName = companySelect.options[companySelect.selectedIndex].text;
    console.log('[ANALYTICS] Applying filters:', currentCompanyId ? companyName : 'All Companies');
    
    loadAnalytics();
}

// Reset filters
function resetFilters() {
    document.getElementById('companyFilter').value = '';
    currentCompanyId = null;
    
    console.log('[ANALYTICS] Filters reset');
    loadAnalytics();
}

// Show error state
function showError() {
    document.getElementById('loadingMessage').style.display = 'none';
    document.getElementById('analyticsContent').style.display = 'none';
    document.getElementById('errorMessage').style.display = 'block';
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
}

function truncate(str, maxLen) {
    if (!str) return 'N/A';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    init();
});

console.log('[ANALYTICS] ✓ analytics.js loaded');

