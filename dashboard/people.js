// ABOUTME: People spreadsheet view JavaScript with server-side pagination
// ABOUTME: Full database access with smart defaults

const API_BASE_URL = 'http://localhost:8000/api';

let peopleTable;
let currentFilters = {};

// Initialize DataTable on page load
$(document).ready(function() {
    console.log('[PEOPLE] Initializing people view with server-side pagination...');
    
    peopleTable = $('#peopleTable').DataTable({
        processing: true,
        serverSide: true,
        pageLength: 50,
        order: [[0, 'asc']], // Sort by name
        ajax: function(data, callback, settings) {
            // Build API parameters from DataTables request
            const offset = data.start || 0;
            const limit = data.length || 50;
            
            // Fetch data from API
            fetchPeople(offset, limit, currentFilters)
                .then(result => {
                    callback({
                        draw: data.draw,
                        recordsTotal: result.total,
                        recordsFiltered: result.total,
                        data: result.people
                    });
                })
                .catch(error => {
                    console.error('[PEOPLE] Error loading data:', error);
                    showNotification('Error loading people. Please try again.', 'error');
                    callback({
                        draw: data.draw,
                        recordsTotal: 0,
                        recordsFiltered: 0,
                        data: []
                    });
                });
        },
        columns: [
            { 
                data: 'full_name', 
                name: 'full_name',
                render: function(data, type, row) {
                    return `<a href="profile.html?id=${row.person_id}" target="_blank" style="color: #667eea; font-weight: 600; text-decoration: none;">${escapeHtml(data)}</a>`;
                }
            },
            { 
                data: 'location', 
                name: 'location',
                render: function(data) {
                    return data ? escapeHtml(data) : '<span style="color: #999;">Not specified</span>';
                }
            },
            { 
                data: 'company_name', 
                name: 'company_name',
                render: function(data) {
                    return data ? escapeHtml(data) : '<span style="color: #999;">N/A</span>';
                }
            },
            { 
                data: 'headline', 
                name: 'headline',
                render: function(data) {
                    if (!data) return '<span style="color: #999;">N/A</span>';
                    // Truncate long headlines
                    const text = escapeHtml(data);
                    return text.length > 60 ? text.substring(0, 60) + '...' : text;
                }
            },
            {
                data: 'has_email',
                orderable: false,
                render: function(data, type, row) {
                    return data ? '<span class="badge badge-yes">Yes</span>' : '<span class="badge badge-no">No</span>';
                }
            },
            {
                data: 'has_github',
                orderable: false,
                render: function(data, type, row) {
                    return data ? '<span class="badge badge-yes">Yes</span>' : '<span class="badge badge-no">No</span>';
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
            processing: "Loading people...",
            info: "Showing _START_ to _END_ of _TOTAL_ people",
            infoEmpty: "No people available",
            infoFiltered: "(filtered from _MAX_ total people)"
        }
    });
    
    console.log('[PEOPLE] ✓ DataTable initialized with server-side pagination');
    
    // Add Enter key support for filters
    $('.filters input').on('keypress', function(e) {
        if (e.which === 13) {
            applyFilters();
        }
    });
});

// Fetch people from API
async function fetchPeople(offset, limit, filters) {
    const params = new URLSearchParams();
    params.append('offset', offset);
    params.append('limit', limit);
    
    if (filters.company) params.append('company', filters.company);
    if (filters.location) params.append('location', filters.location);
    if (filters.headline) params.append('headline', filters.headline);
    if (filters.has_email !== undefined) params.append('has_email', filters.has_email);
    if (filters.has_github !== undefined) params.append('has_github', filters.has_github);
    
    const url = `${API_BASE_URL}/people/?${params.toString()}`;  // Added trailing slash
    console.log('[PEOPLE] Fetching:', url);
    
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Enhance data with has_email and has_github flags (we need to add these to the backend)
    // For now, we'll check if the filter was applied
    const enhancedPeople = data.data.map(person => ({
        ...person,
        has_email: filters.has_email === true,
        has_github: filters.has_github === true
    }));
    
    return {
        people: enhancedPeople,
        total: data.pagination.total
    };
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
    if (headline) filters.headline = headline;
    if (email === 'true') filters.has_email = true;
    else if (email === 'false') filters.has_email = false;
    if (github === 'true') filters.has_github = true;
    else if (github === 'false') filters.has_github = false;
    
    currentFilters = filters;
    
    // Reload table data
    peopleTable.ajax.reload();
    
    // Show notification
    const filterCount = Object.keys(filters).length;
    if (filterCount > 0) {
        showNotification(`Applied ${filterCount} filter(s)`, 'info');
    }
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
    
    // Reload table data
    peopleTable.ajax.reload();
    
    showNotification('Filters cleared', 'info');
}

// Show notification
function showNotification(message, type = 'info') {
    const colors = {
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#28a745',
        'success': '#28a745'
    };
    
    const color = colors[type] || colors.info;
    
    const notification = $(`
        <div class="notification" style="
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
            animation: slideIn 0.3s ease-out;
        ">
            ${escapeHtml(message)}
        </div>
    `);
    
    $('body').append(notification);
    
    setTimeout(() => {
        notification.fadeOut(300, function() {
            $(this).remove();
        });
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

console.log('[PEOPLE] ✓ people.js loaded with server-side pagination');
