// ABOUTME: People spreadsheet view JavaScript
// ABOUTME: DataTables implementation with server-side filtering

const API_BASE_URL = 'http://localhost:8000/api';

let peopleTable;
let currentFilters = {};

// Initialize DataTable on page load
$(document).ready(function() {
    console.log('[PEOPLE] Initializing people spreadsheet view...');
    
    peopleTable = $('#peopleTable').DataTable({
        processing: true,
        serverSide: false, // We'll load data on demand, not true server-side
        pageLength: 20,
        order: [[0, 'asc']], // Sort by name
        columns: [
            { 
                data: 'full_name', 
                name: 'full_name',
                render: function(data, type, row) {
                    return `<a href="profile.html?id=${row.person_id}" target="_blank" style="color: #667eea; font-weight: 600; text-decoration: none;">${data}</a>`;
                }
            },
            { 
                data: 'location', 
                name: 'location',
                render: function(data) {
                    return data || '<span style="color: #999;">Not specified</span>';
                }
            },
            { 
                data: 'company_name', 
                name: 'company_name',
                render: function(data) {
                    return data || '<span style="color: #999;">N/A</span>';
                }
            },
            { 
                data: 'headline', 
                name: 'headline',
                render: function(data) {
                    if (!data) return '<span style="color: #999;">N/A</span>';
                    // Truncate long headlines
                    return data.length > 60 ? data.substring(0, 60) + '...' : data;
                }
            },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    // We'll check if person has email by trying to infer from data
                    // For now, show N/A since we don't have this in the response
                    return '<span class="badge badge-no">N/A</span>';
                }
            },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    // Same for GitHub
                    return '<span class="badge badge-no">N/A</span>';
                }
            },
            {
                data: 'person_id',
                orderable: false,
                render: function(data) {
                    return `<span style="font-size: 11px; color: #999;">${data.substring(0,8)}...</span>`;
                }
            }
        ],
        language: {
            emptyTable: "No people found. Try adjusting your filters.",
            zeroRecords: "No matching people found.",
            processing: "Loading people..."
        }
    });
    
    console.log('[PEOPLE] ✓ DataTable initialized');
    
    // Pre-load demo data for Ava Labs and Uniswap
    loadDemoData();
    
    // Add Enter key support for filters
    $('.filters input').on('keypress', function(e) {
        if (e.which === 13) {
            applyFilters();
        }
    });
});

// Load people data from API
async function loadPeople(filters = {}) {
    console.log('[PEOPLE] Loading people with filters:', filters);
    
    // Show processing state
    peopleTable.clear();
    peopleTable.processing(true);
    
    try {
        // Build query parameters
        const params = new URLSearchParams();
        params.append('limit', '50'); // Reduced for demo performance
        
        if (filters.company) params.append('company', filters.company);
        if (filters.location) params.append('location', filters.location);
        if (filters.headline_keyword) params.append('headline_keyword', filters.headline_keyword);
        if (filters.has_email) params.append('has_email', filters.has_email);
        if (filters.has_github) params.append('has_github', filters.has_github);
        
        const url = `${API_BASE_URL}/query/search?${params.toString()}`;
        console.log('[PEOPLE] Fetching:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('[PEOPLE] ✓ Loaded', data.data.length, 'people');
        
        // Add data to table
        peopleTable.rows.add(data.data);
        peopleTable.draw();
        peopleTable.processing(false);
        
        // Show results count
        showNotification(`Found ${data.pagination.total} people (showing ${data.data.length})`);
        
    } catch (error) {
        console.error('[PEOPLE] ✗ Error loading people:', error);
        peopleTable.processing(false);
        showNotification('Error loading people. Please try again.', 'error');
    }
}

// Apply filters
function applyFilters() {
    console.log('[PEOPLE] Applying filters...');
    
    const filters = {};
    
    const company = $('#filterCompany').val().trim();
    const location = $('#filterLocation').val().trim();
    const headline = $('#filterHeadline').val().trim();
    const email = $('#filterEmail').val();
    const github = $('#filterGithub').val();
    
    if (company) filters.company = company;
    if (location) filters.location = location;
    if (headline) filters.headline_keyword = headline;
    if (email) filters.has_email = email === 'true';
    if (github) filters.has_github = github === 'true';
    
    // Check if any filters are set
    if (Object.keys(filters).length === 0) {
        showNotification('Please select at least one filter', 'warning');
        return;
    }
    
    currentFilters = filters;
    loadPeople(filters);
}

// Clear all filters
function clearFilters() {
    console.log('[PEOPLE] Clearing filters...');
    
    $('#filterCompany').val('');
    $('#filterLocation').val('');
    $('#filterHeadline').val('');
    $('#filterEmail').val('');
    $('#filterGithub').val('');
    
    currentFilters = {};
    peopleTable.clear().draw();
    
    showNotification('Filters cleared. Click Search to load data.');
}

// View person profile
function viewProfile(personId) {
    console.log('[PEOPLE] Viewing profile:', personId);
    window.location.href = `profile.html?id=${personId}`;
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced with a proper notification library
    const color = type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#28a745';
    
    const notification = $(`
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${color};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
        ">
            ${message}
        </div>
    `);
    
    $('body').append(notification);
    
    setTimeout(() => {
        notification.fadeOut(300, function() {
            $(this).remove();
        });
    }, 3000);
}

// Load demo data for Ava Labs and Uniswap
async function loadDemoData() {
    console.log('[PEOPLE] Loading demo data...');
    
    try {
        // Load Ava Labs people
        const avaResponse = await fetch(`${API_BASE_URL}/query/search?company=ava%20labs&limit=25`);
        const avaData = await avaResponse.json();
        
        // Load Uniswap people
        const uniResponse = await fetch(`${API_BASE_URL}/query/search?company=uniswap&limit=25`);
        const uniData = await uniResponse.json();
        
        // Combine results
        const combined = [...avaData.data, ...uniData.data];
        
        console.log('[PEOPLE] ✓ Loaded', combined.length, 'demo people');
        
        // Add to table
        peopleTable.rows.add(combined);
        peopleTable.draw();
        
        showNotification(`Showing ${combined.length} people from Ava Labs & Uniswap`, 'info');
        
    } catch (error) {
        console.error('[PEOPLE] ✗ Error loading demo data:', error);
        showNotification('Use search filters to load people', 'info');
    }
}

console.log('[PEOPLE] ✓ people.js loaded');

