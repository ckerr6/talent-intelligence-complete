// ABOUTME: Person profile page JavaScript - Full profile with employment, emails, and GitHub data
// ABOUTME: Complete person profile display

const API_BASE_URL = 'http://localhost:8000/api';

// Get person ID from URL
const urlParams = new URLSearchParams(window.location.search);
const personId = urlParams.get('id');

if (!personId) {
    showError('No person ID provided');
} else {
    loadProfile(personId);
}

async function loadProfile(personId) {
    console.log('[PROFILE] Loading profile for:', personId);
    
    try {
        const response = await fetch(`${API_BASE_URL}/people/${personId}/full`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Person not found');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        const person = result.data;
        
        console.log('[PROFILE] ✓ Loaded profile:', person);
        
        renderProfile(person);
        
    } catch (error) {
        console.error('[PROFILE] ✗ Error loading profile:', error);
        showError(error.message === 'Person not found' 
            ? 'We couldn\'t find this person. They may not exist in our database.' 
            : 'Connection issue. Check your network and try refreshing the page.');
    }
}

function renderProfile(person) {
    const container = document.getElementById('profileContainer');
    
    // Hide skeleton loading
    const skeleton = document.getElementById('skeletonLoading');
    if (skeleton) {
        skeleton.style.display = 'none';
    }
    
    // Build profile header
    let html = `
        <div class="profile-header">
            <h1>${escapeHtml(person.full_name)}</h1>
            ${person.headline ? `<div class="headline">${escapeHtml(person.headline)}</div>` : ''}
            <div class="meta">
                ${person.location ? `<div class="meta-item">📍 ${escapeHtml(person.location)}</div>` : ''}
                ${person.followers_count ? `<div class="meta-item">👥 ${person.followers_count.toLocaleString()} LinkedIn followers</div>` : ''}
            </div>
        </div>
    `;
    
    // Contact Information Section
    html += renderContactSection(person);
    
    // Employment History Section
    html += renderEmploymentSection(person.employment || []);
    
    // GitHub Profile Section
    if (person.github_profile) {
        html += renderGitHubSection(person.github_profile);
    }
    
    // GitHub Contributions Section
    if (person.github_contributions && person.github_contributions.length > 0) {
        html += renderContributionsSection(person.github_contributions);
    }
    
    container.innerHTML = html;
}

function renderContactSection(person) {
    let html = `<div class="profile-section">
        <h2>📧 Contact Information</h2>
        <div class="contact-info">`;
    
    // LinkedIn
    if (person.linkedin_url) {
        html += `
            <div class="contact-item">
                <span>🔗</span>
                <a href="${escapeHtml(person.linkedin_url)}" target="_blank">LinkedIn Profile</a>
            </div>`;
    }
    
    // GitHub
    if (person.github_profile && person.github_profile.github_username) {
        html += `
            <div class="contact-item">
                <span>💻</span>
                <a href="https://github.com/${escapeHtml(person.github_profile.github_username)}" target="_blank">GitHub: @${escapeHtml(person.github_profile.github_username)}</a>
            </div>`;
    }
    
    // Emails
    if (person.emails && person.emails.length > 0) {
        person.emails.forEach(emailObj => {
            const isPrimary = emailObj.is_primary;
            html += `
                <div class="contact-item">
                    <span>📧</span>
                    <span>
                        ${escapeHtml(emailObj.email)}
                        ${isPrimary ? '<span style="color: #667eea; font-weight: 600; margin-left: 8px;">(Primary)</span>' : ''}
                        ${emailObj.email_type && emailObj.email_type !== 'unknown' ? `<span style="color: #999; font-size: 12px; margin-left: 8px;">(${emailObj.email_type})</span>` : ''}
                    </span>
                </div>`;
        });
    } else {
        html += `
            <div class="contact-item" style="color: #999;">
                <span>ℹ️</span>
                No email addresses on file
            </div>`;
    }
    
    html += `</div></div>`;
    return html;
}

function renderEmploymentSection(employment) {
    let html = `<div class="profile-section">
        <h2>💼 Employment History</h2>`;
    
    if (employment.length === 0) {
        html += `<p style="color: #999;">No employment history available</p>`;
    } else {
        html += '<div class="employment-timeline">';
        employment.forEach(job => {
            const startDate = job.start_date ? formatDate(job.start_date) : 'Unknown';
            const endDate = job.is_current ? 'Present' : (job.end_date ? formatDate(job.end_date) : 'Unknown');
            const duration = calculateDuration(job.start_date, job.end_date);
            
            html += `
                <div class="employment-item ${job.is_current ? 'current' : ''}">
                    <div class="employment-header">
                        <h3>${escapeHtml(job.title || 'Position not specified')}</h3>
                        ${job.is_current ? '<span class="current-badge">Current</span>' : ''}
                    </div>
                    <div class="company">${escapeHtml(job.company_name || 'Company not specified')}</div>
                    <div class="dates">
                        ${startDate} - ${endDate}
                        ${duration ? `<span style="color: #999;"> • ${duration}</span>` : ''}
                    </div>
                </div>`;
        });
        html += '</div>';
    }
    
    html += `</div>`;
    return html;
}

function renderGitHubSection(github) {
    let html = `<div class="profile-section">
        <h2>💻 GitHub Profile</h2>
        <div style="margin-bottom: 20px;">
            ${github.bio ? `<p style="color: #666; margin-bottom: 15px;">${escapeHtml(github.bio)}</p>` : ''}
        </div>
        <div class="github-stats">`;
    
    html += `
        <div class="stat-box">
            <div class="value">${github.followers || 0}</div>
            <div class="label">Followers</div>
        </div>
        <div class="stat-box">
            <div class="value">${github.following || 0}</div>
            <div class="label">Following</div>
        </div>
        <div class="stat-box">
            <div class="value">${github.public_repos || 0}</div>
            <div class="label">Public Repos</div>
        </div>
        <div class="stat-box">
            <div class="value">${github.public_gists || 0}</div>
            <div class="label">Gists</div>
        </div>
    `;
    
    html += `</div></div>`;
    return html;
}

function renderContributionsSection(contributions) {
    let html = `<div class="profile-section">
        <h2>🔨 GitHub Contributions</h2>
        <p style="color: #666; margin-bottom: 20px;">Repositories this person has contributed to (top 50 by contribution count)</p>
        <div class="contributions-list">`;
    
    contributions.forEach(contrib => {
        html += `
            <div class="repo-item">
                <h4>
                    <a href="https://github.com/${escapeHtml(contrib.repo_full_name)}" target="_blank" style="color: #667eea; text-decoration: none;">
                        ${escapeHtml(contrib.repo_name)}
                    </a>
                </h4>
                ${contrib.description ? `<p style="color: #666; font-size: 13px; margin: 5px 0;">${escapeHtml(contrib.description)}</p>` : ''}
                <div class="repo-meta">
                    ${contrib.language ? `<span class="language-tag">${escapeHtml(contrib.language)}</span>` : ''}
                    <span>⭐ ${contrib.stars || 0} stars</span>
                    <span>🍴 ${contrib.forks || 0} forks</span>
                    <span style="font-weight: 600; color: #667eea;">✍️ ${contrib.contribution_count} contributions</span>
                    ${contrib.owner_company_name ? `<span style="color: #764ba2;">🏢 ${escapeHtml(contrib.owner_company_name)}</span>` : ''}
                </div>
            </div>`;
    });
    
    html += `</div></div>`;
    return html;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}

function calculateDuration(startDate, endDate) {
    if (!startDate) return '';
    
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    
    let months = (end.getFullYear() - start.getFullYear()) * 12;
    months -= start.getMonth();
    months += end.getMonth();
    
    if (months < 0) months = 0;
    
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    
    if (years > 0 && remainingMonths > 0) {
        return `${years} yr ${remainingMonths} mo`;
    } else if (years > 0) {
        return `${years} yr`;
    } else if (remainingMonths > 0) {
        return `${remainingMonths} mo`;
    }
    
    return '';
}

function showError(message) {
    const container = document.getElementById('profileContainer');
    
    // Hide skeleton loading
    const skeleton = document.getElementById('skeletonLoading');
    if (skeleton) {
        skeleton.style.display = 'none';
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.innerHTML = `
        <div class="error" style="padding: 40px; text-align: center;">
            <h2>❌ Error</h2>
            <p style="color: #666; margin-bottom: 20px;">${escapeHtml(message)}</p>
            <button onclick="location.reload()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; margin-right: 10px;">
                🔄 Try Again
            </button>
            <a href="people.html" style="padding: 10px 20px; background: #f0f0f0; color: #333; border-radius: 6px; text-decoration: none; display: inline-block;">
                ← Back to People
            </a>
        </div>`;
    
    container.appendChild(errorDiv);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

console.log('[PROFILE] ✓ profile.js loaded');
