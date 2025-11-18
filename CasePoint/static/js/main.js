// CasePoint - Main JavaScript Functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize advanced search toggle
    initializeAdvancedSearch();
    
    // Initialize filter interactions
    initializeFilters();
    
    // Initialize AI analysis
    initializeAIAnalysis();
});

// Search Functions
function initializeSearch() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    // Search tab switching
    const searchTabs = document.querySelectorAll('.search-tabs .nav-link');
    searchTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            switchSearchTab(this.getAttribute('data-category'));
        });
    });
}

function handleSearchSubmit(e) {
    e.preventDefault();
    
    const query = document.getElementById('searchQuery').value.trim();
    const category = document.querySelector('.search-tabs .nav-link.active').getAttribute('data-category') || 'all';
    
    if (!query) {
        showAlert('Please enter a search query', 'warning');
        return;
    }
    
    // Show loading state
    showSearchLoading();
    
    // Redirect to results page
    const searchParams = new URLSearchParams({
        q: query,
        category: category
    });
    
    window.location.href = `/search/results?${searchParams.toString()}`;
}

function switchSearchTab(category) {
    // Update active tab
    document.querySelectorAll('.search-tabs .nav-link').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelector(`.search-tabs .nav-link[data-category="${category}"]`).classList.add('active');
    
    // Update search placeholder
    const searchInput = document.getElementById('searchQuery');
    const placeholders = {
        'all': 'Search cases, statutes, rules, and more...',
        'cases': 'Search case law and judgments...',
        'statutes': 'Search statutes and acts...',
        'rules': 'Search rules and regulations...',
        'ai': 'Ask AI a legal question...'
    };
    
    if (searchInput && placeholders[category]) {
        searchInput.setAttribute('placeholder', placeholders[category]);
    }
}

// Advanced Search Functions
function initializeAdvancedSearch() {
    const toggleButton = document.getElementById('advancedSearchToggle');
    const panel = document.getElementById('advancedSearchPanel');
    
    if (toggleButton && panel) {
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            toggleAdvancedSearch();
        });
    }
}

function toggleAdvancedSearch() {
    const panel = document.getElementById('advancedSearchPanel');
    const toggle = document.getElementById('advancedSearchToggle');
    
    if (panel.style.display === 'none' || !panel.style.display) {
        panel.style.display = 'block';
        toggle.innerHTML = '<i class="fas fa-chevron-up me-2"></i>Hide Advanced Search';
    } else {
        panel.style.display = 'none';
        toggle.innerHTML = '<i class="fas fa-chevron-down me-2"></i>Advanced Search';
    }
}

// Filter Functions
function initializeFilters() {
    const filterCheckboxes = document.querySelectorAll('.filter-option input[type="checkbox"]');
    
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSearchFilters();
        });
    });
    
    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
}

function updateSearchFilters() {
    // Get current filters
    const activeFilters = [];
    document.querySelectorAll('.filter-option input[type="checkbox"]:checked').forEach(checkbox => {
        activeFilters.push({
            type: checkbox.getAttribute('data-filter-type'),
            value: checkbox.value
        });
    });
    
    // Update URL with filters
    updateUrlWithFilters(activeFilters);
    
    // Reload results (in a real app, this would be AJAX)
    // window.location.reload();
}

function clearAllFilters() {
    document.querySelectorAll('.filter-option input[type="checkbox"]:checked').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    updateSearchFilters();
}

function updateUrlWithFilters(filters) {
    const url = new URL(window.location);
    
    // Clear existing filter parameters
    url.searchParams.delete('courts');
    url.searchParams.delete('years');
    url.searchParams.delete('jurisdictions');
    
    // Add new filter parameters
    filters.forEach(filter => {
        const existing = url.searchParams.get(filter.type) || '';
        const values = existing ? existing.split(',') : [];
        if (!values.includes(filter.value)) {
            values.push(filter.value);
        }
        url.searchParams.set(filter.type, values.join(','));
    });
    
    // Update URL without reload
    window.history.pushState({}, '', url);
}

// AI Analysis Functions
function initializeAIAnalysis() {
    const aiForm = document.getElementById('aiAnalysisForm');
    if (aiForm) {
        aiForm.addEventListener('submit', handleAIAnalysis);
    }
}

async function handleAIAnalysis(e) {
    e.preventDefault();
    
    const query = document.getElementById('aiQuery').value.trim();
    const context = document.getElementById('aiContext').value.trim();
    const submitBtn = document.getElementById('aiSubmitBtn');
    const resultDiv = document.getElementById('aiResult');
    
    if (!query) {
        showAlert('Please enter a legal question', 'warning');
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    resultDiv.style.display = 'block';
    resultDiv.className = 'ai-result loading';
    resultDiv.innerHTML = '<i class="fas fa-robot fa-spin me-2"></i>AI is analyzing your legal question...';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                context: context
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resultDiv.className = 'ai-result';
            resultDiv.innerHTML = `
                <h5><i class="fas fa-robot me-2"></i>AI Legal Analysis</h5>
                <div class="mt-3">${data.answer.replace(/\n/g, '<br>')}</div>
            `;
        } else {
            resultDiv.className = 'ai-result alert alert-danger';
            resultDiv.innerHTML = `<h6>Error:</h6><div>${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.className = 'ai-result alert alert-danger';
        resultDiv.innerHTML = '<h6>Error:</h6><div>Failed to connect to AI service</div>';
    }
    
    // Reset button
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Analyze with AI';
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of main content
    const main = document.querySelector('main');
    const container = document.createElement('div');
    container.className = 'container mt-3';
    container.appendChild(alertDiv);
    main.insertBefore(container, main.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showSearchLoading() {
    const submitBtn = document.getElementById('searchSubmitBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
    }
}

// Search suggestions (placeholder for future enhancement)
function initializeSearchSuggestions() {
    // TODO: Implement autocomplete suggestions
}

// Mobile menu handling
function toggleMobileMenu() {
    const navbarCollapse = document.getElementById('navbarNav');
    const bsCollapse = new bootstrap.Collapse(navbarCollapse);
    bsCollapse.toggle();
}