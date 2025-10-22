// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State
let statsData = null;
let qualityData = null;

// Initialize dashboard
async function init() {
    await checkAPIHealth();
    await loadStats();
    await loadQuality();
    createCharts();
}

// Check API health
async function checkAPIHealth() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            statusDot.classList.add('connected');
            statusText.textContent = 'API Connected';
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        statusDot.classList.add('error');
        statusText.textContent = 'API Connection Error';
        console.error('API health check failed:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats/overview`);
        statsData = await response.json();
        
        // Update stat cards
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach(card => card.classList.remove('loading'));
        
        const values = document.querySelectorAll('.stat-value');
        values[0].textContent = formatNumber(statsData.totals.people);
        values[1].textContent = formatNumber(statsData.totals.companies);
        values[2].textContent = formatNumber(statsData.totals.employment_records);
        values[3].textContent = formatNumber(statsData.totals.emails);
        values[4].textContent = formatNumber(statsData.totals.github_profiles);
        
        // Calculate avg jobs per person
        const avgJobs = (statsData.totals.employment_records / statsData.totals.people).toFixed(1);
        values[5].textContent = avgJobs;
        
    } catch (error) {
        console.error('Error loading stats:', error);
        showError('Failed to load statistics');
    }
}

// Load quality metrics
async function loadQuality() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats/quality`);
        qualityData = await response.json();
    } catch (error) {
        console.error('Error loading quality metrics:', error);
    }
}

// Create charts
function createCharts() {
    if (!statsData || !qualityData) return;
    
    // Completeness Chart
    const completenessCtx = document.getElementById('completenessChart').getContext('2d');
    new Chart(completenessCtx, {
        type: 'bar',
        data: {
            labels: ['LinkedIn', 'Email', 'GitHub', 'Location', 'Headline'],
            datasets: [{
                label: 'Data Completeness (%)',
                data: [
                    qualityData.completeness.linkedin.percentage,
                    qualityData.completeness.email.percentage,
                    qualityData.completeness.github.percentage,
                    qualityData.completeness.location.percentage,
                    qualityData.completeness.headline.percentage
                ],
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(237, 100, 166, 0.8)',
                    'rgba(255, 154, 158, 0.8)',
                    'rgba(250, 208, 132, 0.8)'
                ],
                borderColor: [
                    'rgba(102, 126, 234, 1)',
                    'rgba(118, 75, 162, 1)',
                    'rgba(237, 100, 166, 1)',
                    'rgba(255, 154, 158, 1)',
                    'rgba(250, 208, 132, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    
    // Overview Pie Chart
    const overviewCtx = document.getElementById('overviewChart').getContext('2d');
    new Chart(overviewCtx, {
        type: 'doughnut',
        data: {
            labels: ['People', 'Companies', 'Employment Records', 'GitHub Profiles'],
            datasets: [{
                data: [
                    statsData.totals.people,
                    statsData.totals.companies,
                    statsData.totals.employment_records,
                    statsData.totals.github_profiles
                ],
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(237, 100, 166, 0.8)',
                    'rgba(255, 154, 158, 0.8)'
                ],
                borderColor: [
                    'rgba(102, 126, 234, 1)',
                    'rgba(118, 75, 162, 1)',
                    'rgba(237, 100, 166, 1)',
                    'rgba(255, 154, 158, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += formatNumber(context.parsed);
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Quick query presets
async function quickQuery(type) {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading-spinner">🔍 Searching...</div>';
    
    let params = new URLSearchParams();
    params.append('limit', '20');
    
    switch(type) {
        case 'sf-engineers':
            params.append('location', 'San Francisco');
            params.append('headline_keyword', 'Engineer');
            params.append('has_github', 'true');
            break;
        case 'google-emails':
            params.append('company', 'Google');
            params.append('has_email', 'true');
            break;
        case 'blockchain':
            params.append('headline_keyword', 'blockchain');
            break;
        case 'ex-coinbase':
            params.append('company', 'Coinbase');
            break;
        case 'remote-github':
            params.append('location', 'Remote');
            params.append('has_github', 'true');
            break;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/query/search?${params.toString()}`);
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error with quick query:', error);
        resultsDiv.innerHTML = '<p class="error-message">Error performing search. Please try again.</p>';
    }
}

// Advanced search with all filters
async function advancedSearch() {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading-spinner">🔍 Searching...</div>';
    
    const params = new URLSearchParams();
    params.append('limit', '10'); // Reduced for performance
    
    const company = document.getElementById('filterCompany').value.trim();
    const location = document.getElementById('filterLocation').value.trim();
    const headline = document.getElementById('filterHeadline').value.trim();
    const hasEmail = document.getElementById('filterEmail').checked;
    const hasGithub = document.getElementById('filterGithub').checked;
    
    if (company) params.append('company', company);
    if (location) params.append('location', location);
    if (headline) params.append('headline_keyword', headline);
    if (hasEmail) params.append('has_email', 'true');
    if (hasGithub) params.append('has_github', 'true');
    
    // Check if any filters are set
    if (params.toString() === 'limit=20') {
        resultsDiv.innerHTML = '<p class="error-message">Please select at least one filter</p>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/query/search?${params.toString()}`);
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error searching:', error);
        resultsDiv.innerHTML = '<p class="error-message">Error performing search. Please try again.</p>';
    }
}

// Display results with enhanced formatting
function displayResults(data) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (data.data.length === 0) {
        resultsDiv.innerHTML = '<p class="error-message">No results found with these filters</p>';
        return;
    }
    
    const activeFilters = [];
    if (data.filters.company) activeFilters.push(`Company: ${data.filters.company}`);
    if (data.filters.location) activeFilters.push(`Location: ${data.filters.location}`);
    if (data.filters.headline_keyword) activeFilters.push(`Keyword: ${data.filters.headline_keyword}`);
    if (data.filters.has_email) activeFilters.push('Has Email');
    if (data.filters.has_github) activeFilters.push('Has GitHub');
    
    let html = `
        <div class="results-summary">
            Found ${data.pagination.total} results
            ${activeFilters.length > 0 ? ' | Filters: ' + activeFilters.join(', ') : ''}
        </div>
    `;
    
    html += data.data.map(person => {
        const badges = [];
        // Note: We don't have email/github info in the response, so we use the filters
        if (data.filters.has_email) badges.push('<span class="badge badge-email">📧 Email</span>');
        if (data.filters.has_github) badges.push('<span class="badge badge-github">💻 GitHub</span>');
        
        return `
            <div class="result-card">
                <h3>${escapeHtml(person.full_name)}</h3>
                <p><strong>Headline:</strong> ${escapeHtml(person.headline || 'N/A')}</p>
                <p class="location">📍 ${escapeHtml(person.location || 'Location not specified')}</p>
                <p><small>👥 ${person.followers_count || 0} LinkedIn followers</small></p>
                ${badges.length > 0 ? '<div class="badges">' + badges.join('') + '</div>' : ''}
            </div>
        `;
    }).join('');
    
    resultsDiv.innerHTML = html;
}

// Clear all filters
function clearFilters() {
    document.getElementById('filterCompany').value = '';
    document.getElementById('filterLocation').value = '';
    document.getElementById('filterHeadline').value = '';
    document.getElementById('filterEmail').checked = false;
    document.getElementById('filterGithub').checked = false;
    document.getElementById('searchResults').innerHTML = '';
}

// Allow Enter key to trigger search in any filter field
document.addEventListener('DOMContentLoaded', function() {
    const filterInputs = ['filterCompany', 'filterLocation', 'filterHeadline'];
    filterInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    advancedSearch();
                }
            });
        }
    });
});

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const statsGrid = document.getElementById('statsGrid');
    statsGrid.insertAdjacentHTML('beforebegin', `
        <div class="error-message">${message}</div>
    `);
}

// Search for companies (using people search to find company IDs)
async function searchCompanies() {
    const input = document.getElementById('companyNameSearch');
    const resultsDiv = document.getElementById('companyResults');
    const contributorsDiv = document.getElementById('contributorsResults');
    const companyName = input.value.trim();
    
    if (!companyName) {
        resultsDiv.innerHTML = '<p class="error-message">Please enter a company name</p>';
        return;
    }
    
    resultsDiv.innerHTML = '<div class="loading-spinner">🔍 Searching for companies...</div>';
    contributorsDiv.innerHTML = '';
    
    try {
        // Search for people at this company to get company info
        const response = await fetch(`${API_BASE_URL}/query/search?company=${encodeURIComponent(companyName)}&limit=50`);
        const data = await response.json();
        
        if (data.data.length === 0) {
            resultsDiv.innerHTML = '<p class="error-message">No companies found matching "' + escapeHtml(companyName) + '"</p>';
            return;
        }
        
        // Get unique companies from the results
        const companiesMap = new Map();
        data.data.forEach(person => {
            if (person.company_name && person.company_id) {
                if (!companiesMap.has(person.company_id)) {
                    companiesMap.set(person.company_id, {
                        company_id: person.company_id,
                        company_name: person.company_name,
                        employee_count: 0
                    });
                }
                companiesMap.get(person.company_id).employee_count++;
            }
        });
        
        const companies = Array.from(companiesMap.values());
        
        resultsDiv.innerHTML = `
            <div class="results-summary">Found ${companies.length} companies matching "${escapeHtml(companyName)}"</div>
            ${companies.map(company => `
                <div class="company-card" onclick="selectCompany('${company.company_id}', '${escapeHtml(company.company_name)}')">
                    <div class="company-info">
                        <h3>${escapeHtml(company.company_name)}</h3>
                        <p>👥 ${company.employee_count} employees in search results</p>
                    </div>
                    <div class="company-actions">
                        <button>Find Contributors →</button>
                    </div>
                </div>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error searching companies:', error);
        resultsDiv.innerHTML = '<p class="error-message">Error searching companies. Please try again.</p>';
    }
}

// Select a company and fetch its external contributors
async function selectCompany(companyId, companyName) {
    const contributorsDiv = document.getElementById('contributorsResults');
    contributorsDiv.innerHTML = '<div class="loading-spinner">🔍 Finding external GitHub contributors...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/companies/${companyId}/github/contributors?limit=10`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error('API request failed');
        }
        
        if (data.data.length === 0) {
            contributorsDiv.innerHTML = `
                <div class="results-summary">
                    No external GitHub contributors found for ${escapeHtml(companyName)}
                </div>
                <p class="error-message">This could mean:</p>
                <ul style="color: #666; margin-left: 20px;">
                    <li>The company doesn't have public GitHub repositories in our database</li>
                    <li>All contributors are employees</li>
                    <li>GitHub data hasn't been enriched yet for this company</li>
                </ul>
            `;
            return;
        }
        
        contributorsDiv.innerHTML = `
            <div class="results-summary">
                Found ${data.pagination.total} external contributors to ${escapeHtml(companyName)}'s repositories
                <br><small>These are developers who contribute but are NOT employees - potential recruitment targets!</small>
            </div>
            ${data.data.map(contributor => `
                <div class="contributor-card">
                    <div class="contributor-header">
                        <div>
                            <div class="contributor-name">${escapeHtml(contributor.github_name || contributor.github_username)}</div>
                            <div class="contributor-username">@${escapeHtml(contributor.github_username)}</div>
                        </div>
                    </div>
                    
                    ${contributor.bio ? '<p><strong>Bio:</strong> ' + escapeHtml(contributor.bio) + '</p>' : ''}
                    ${contributor.location ? '<p>📍 ' + escapeHtml(contributor.location) + '</p>' : ''}
                    ${contributor.github_email ? '<p>📧 ' + escapeHtml(contributor.github_email) + '</p>' : ''}
                    
                    <div class="contributor-stats">
                        <div class="stat-item">
                            <div class="stat-value">${contributor.total_contributions || 0}</div>
                            <div class="stat-label">Total Contributions</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${contributor.repo_count || 0}</div>
                            <div class="stat-label">Repos Contributed To</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${contributor.followers || 0}</div>
                            <div class="stat-label">GitHub Followers</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${contributor.public_repos || 0}</div>
                            <div class="stat-label">Public Repos</div>
                        </div>
                    </div>
                </div>
            `).join('')}
        `;
    } catch (error) {
        console.error('Error fetching contributors:', error);
        contributorsDiv.innerHTML = '<p class="error-message">Error fetching contributors. This company may not have GitHub data yet.</p>';
    }
}

// Allow Enter key in company search
document.addEventListener('DOMContentLoaded', function() {
    const companyInput = document.getElementById('companyNameSearch');
    if (companyInput) {
        companyInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchCompanies();
            }
        });
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    init();
});

