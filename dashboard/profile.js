// ABOUTME: Person profile page JavaScript - DEMO VERSION
// ABOUTME: Displays basic profile data for demonstration

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
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        const person = result.data;
        
        console.log('[PROFILE] ✓ Loaded profile:', person);
        
        renderProfile(person);
        
    } catch (error) {
        console.error('[PROFILE] ✗ Error loading profile:', error);
        showError('Failed to load profile. The person may not exist or the API is unavailable.');
    }
}

function renderProfile(person) {
    const container = document.getElementById('profileContainer');
    
    // Build profile header
    let html = `
        <div class="profile-header">
            <h1>${escapeHtml(person.full_name)}</h1>
            ${person.headline ? `<div class="headline">${escapeHtml(person.headline)}</div>` : '<div class="headline" style="color: #999;">No headline</div>'}
            <div class="meta">
                ${person.location ? `<div class="meta-item">📍 ${escapeHtml(person.location)}</div>` : '<div class="meta-item">📍 Location not specified</div>'}
                ${person.followers_count ? `<div class="meta-item">👥 ${person.followers_count.toLocaleString()} LinkedIn followers</div>` : ''}
            </div>
        </div>
    `;
    
    // Contact Information
    html += `<div class="profile-section">
        <h2>📧 Contact Information</h2>
        <div class="contact-info">`;
    
    if (person.linkedin_url) {
        html += `
            <div class="contact-item">
                <span>🔗</span>
                <a href="${escapeHtml(person.linkedin_url)}" target="_blank" style="color: #667eea; text-decoration: none;">LinkedIn Profile →</a>
            </div>`;
    }
    
    html += `
        <div class="contact-item" style="color: #999;">
            <span>ℹ️</span>
            Additional contact data available in full database
        </div>
    `;
    
    html += `</div></div>`;
    
    // Data Collection Note
    html += `<div class="profile-section" style="background: #f7fafc; padding: 20px; border-radius: 8px; margin-top: 20px;">
        <h2>📊 Data Breadth</h2>
        <p style="color: #666;">This profile demonstrates our data collection capabilities. The full system includes:</p>
        <ul style="color: #666; margin-left: 20px;">
            <li>✅ Employment history across companies</li>
            <li>✅ Email addresses (multiple per person)</li>
            <li>✅ GitHub profiles and contributions</li>
            <li>✅ Repository activity and commit history</li>
            <li>✅ Professional relationships (co-employment graph)</li>
        </ul>
        <p style="color: #667eea; font-weight: 600; margin-top: 15px;">Demo version shows basic info only for performance</p>
    </div>`;
    
    container.innerHTML = html;
}

function showError(message) {
    const container = document.getElementById('profileContainer');
    container.innerHTML = `
        <div class="error" style="padding: 40px; text-align: center;">
            <h2>❌ Error</h2>
            <p style="color: #666;">${escapeHtml(message)}</p>
            <p style="margin-top: 20px;"><a href="people.html" style="color: #667eea;">← Back to People</a></p>
        </div>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

console.log('[PROFILE] ✓ profile.js loaded');
