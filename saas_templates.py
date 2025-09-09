"""
Template rendering functions for SaaS KanoonPK platform
"""
from flask import render_template_string

# =============================================================================
# AUTHENTICATION TEMPLATES
# =============================================================================

TENANT_REGISTRATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register Organization - KanoonPK SaaS</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .registration-hero {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 2rem 0;
        }
        .feature-card {
            border: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .feature-card:hover {
            transform: translateY(-2px);
        }
        .plan-badge {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-balance-scale me-2"></i>KanoonPK SaaS
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('auth.login') }}">
                    <i class="fas fa-sign-in-alt me-1"></i>Login
                </a>
            </div>
        </div>
    </nav>

    <div class="registration-hero">
        <div class="container text-center">
            <h1 class="display-4 mb-3">
                <i class="fas fa-building"></i>
                Start Your Legal Research Platform
            </h1>
            <p class="lead">Join Pakistan's premier AI-powered legal research platform</p>
        </div>
    </div>

    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <!-- Registration Form -->
                <div class="card shadow-lg">
                    <div class="card-header bg-primary text-white">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-user-plus me-2"></i>Register Your Organization
                        </h5>
                    </div>
                    <div class="card-body">
                        <form id="registrationForm">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Organization Name *</label>
                                    <input type="text" class="form-control" name="organization_name" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Subdomain *</label>
                                    <div class="input-group">
                                        <input type="text" class="form-control" name="subdomain" 
                                               pattern="[a-z0-9-]+" title="Only lowercase letters, numbers, and hyphens allowed" required>
                                        <span class="input-group-text">.kanoonpk.com</span>
                                    </div>
                                    <div class="form-text">This will be your organization's URL</div>
                                </div>
                            </div>

                            <hr class="my-4">
                            <h6 class="text-primary">Administrator Account</h6>

                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">First Name *</label>
                                    <input type="text" class="form-control" name="admin_first_name" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Last Name *</label>
                                    <input type="text" class="form-control" name="admin_last_name" required>
                                </div>
                            </div>

                            <div class="mb-3">
                                <label class="form-label">Email Address *</label>
                                <input type="email" class="form-control" name="admin_email" required>
                            </div>

                            <div class="mb-3">
                                <label class="form-label">Password *</label>
                                <input type="password" class="form-control" name="admin_password" 
                                       minlength="8" required>
                                <div class="form-text">Minimum 8 characters</div>
                            </div>

                            <div class="mb-4">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="terms" required>
                                    <label class="form-check-label" for="terms">
                                        I agree to the <a href="#" class="text-primary">Terms of Service</a> 
                                        and <a href="#" class="text-primary">Privacy Policy</a>
                                    </label>
                                </div>
                            </div>

                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-lg">
                                    <i class="fas fa-rocket me-2"></i>Create Organization
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Features Overview -->
                <div class="row mt-5">
                    <div class="col-md-4 mb-3">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-search fa-2x text-primary mb-3"></i>
                                <h6>Advanced Legal Search</h6>
                                <p class="text-muted small">AI-powered search through Pakistan legal database with citation analysis</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-users fa-2x text-success mb-3"></i>
                                <h6>Team Collaboration</h6>
                                <p class="text-muted small">Shared workspaces and collaborative legal research for your team</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card feature-card h-100">
                            <div class="card-body text-center">
                                <i class="fas fa-chart-line fa-2x text-warning mb-3"></i>
                                <h6>Usage Analytics</h6>
                                <p class="text-muted small">Track research patterns and optimize your legal workflow</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Pricing Info -->
                <div class="card mt-4">
                    <div class="card-body text-center">
                        <span class="plan-badge">Free Plan</span>
                        <h6 class="mt-2">Start with 100 free queries per month</h6>
                        <p class="text-muted small">Upgrade anytime to unlock advanced features and higher limits</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('registrationForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Creating...';
            
            try {
                const response = await fetch('{{ url_for("auth.register_tenant") }}', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Organization created successfully! Redirecting to dashboard...');
                    window.location.href = '/dashboard';
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Registration failed. Please try again.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });

        // Real-time subdomain validation
        document.querySelector('input[name="subdomain"]').addEventListener('input', function(e) {
            e.target.value = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
        });
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - KanoonPK SaaS</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .login-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        }
        .login-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="card login-card shadow-lg">
                        <div class="card-body p-5">
                            <div class="text-center mb-4">
                                <i class="fas fa-balance-scale fa-3x text-primary mb-3"></i>
                                <h4 class="text-white">KanoonPK SaaS</h4>
                                <p class="text-light">Legal Research Platform</p>
                            </div>

                            <form id="loginForm">
                                <div class="mb-3">
                                    <label class="form-label text-light">Email Address</label>
                                    <input type="email" class="form-control" name="email" required>
                                </div>

                                <div class="mb-4">
                                    <label class="form-label text-light">Password</label>
                                    <input type="password" class="form-control" name="password" required>
                                </div>

                                <div class="d-grid mb-3">
                                    <button type="submit" class="btn btn-primary btn-lg">
                                        <i class="fas fa-sign-in-alt me-2"></i>Login
                                    </button>
                                </div>
                            </form>

                            <div class="text-center">
                                <p class="text-light mb-0">Don't have an organization?</p>
                                <a href="{{ url_for('auth.register_tenant') }}" class="text-primary">
                                    Register your organization
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Logging in...';
            
            try {
                const response = await fetch('{{ url_for("auth.login") }}', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    localStorage.setItem('access_token', result.access_token);
                    window.location.href = '/dashboard';
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Login failed. Please try again.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    </script>
</body>
</html>
"""

# =============================================================================
# DASHBOARD TEMPLATE
# =============================================================================

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - {{ tenant.name }} | KanoonPK SaaS</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        }
        .chat-messages {
            height: 500px;
            overflow-y: auto;
            border: 1px solid var(--bs-border-color);
            border-radius: 8px;
            padding: 1rem;
        }
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 1rem;
            max-width: 80%;
            word-wrap: break-word;
            animation: fadeIn 0.3s ease-in;
        }
        .message.user {
            background-color: var(--bs-primary);
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .message.bot {
            background-color: var(--bs-secondary-bg);
            color: var(--bs-body-color);
            margin-right: auto;
        }
        .usage-progress {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav class="col-md-3 col-lg-2 d-md-block sidebar collapse">
                <div class="position-sticky pt-3">
                    <div class="text-center text-white mb-4">
                        <i class="fas fa-balance-scale fa-2x mb-2"></i>
                        <h6>{{ tenant.name }}</h6>
                        <small class="text-light">{{ tenant.plan|title }} Plan</small>
                    </div>

                    <!-- Navigation -->
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link text-white active" href="#dashboard" data-tab="dashboard">
                                <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="#research" data-tab="research">
                                <i class="fas fa-search me-2"></i>Legal Research
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="#documents" data-tab="documents">
                                <i class="fas fa-file-alt me-2"></i>Documents
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="#workspaces" data-tab="workspaces">
                                <i class="fas fa-users me-2"></i>Workspaces
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="#analytics" data-tab="analytics">
                                <i class="fas fa-chart-bar me-2"></i>Analytics
                            </a>
                        </li>
                    </ul>

                    <!-- User Info -->
                    <div class="position-absolute bottom-0 start-0 end-0 p-3">
                        <div class="dropdown">
                            <a href="#" class="d-flex align-items-center text-white text-decoration-none dropdown-toggle" 
                               data-bs-toggle="dropdown">
                                <i class="fas fa-user-circle me-2"></i>
                                <small>{% if user %}{{ user.get_full_name() }}{% endif %}</small>
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#"><i class="fas fa-cog me-2"></i>Settings</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">
                                    <i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </nav>

            <!-- Main content -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                <!-- Dashboard Tab -->
                <div id="dashboard-content" class="tab-content">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">Dashboard</h1>
                    </div>

                    <!-- Usage Overview -->
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6 class="text-muted">Queries This Month</h6>
                                            <h4>{{ query_usage|default(0) }}</h4>
                                        </div>
                                        <i class="fas fa-search fa-2x text-primary"></i>
                                    </div>
                                    <div class="progress mt-2" style="height: 5px;">
                                        <div class="progress-bar" role="progressbar" 
                                             style="width: {{ (query_usage / plan_limits.max_queries_per_month * 100) if plan_limits.max_queries_per_month > 0 else 0 }}%"></div>
                                    </div>
                                    <small class="text-muted">
                                        {% if plan_limits.max_queries_per_month > 0 %}
                                            {{ plan_limits.max_queries_per_month - query_usage|default(0) }} remaining
                                        {% else %}
                                            Unlimited
                                        {% endif %}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6 class="text-muted">Documents</h6>
                                            <h4>{{ doc_usage|default(0) }}</h4>
                                        </div>
                                        <i class="fas fa-file-alt fa-2x text-success"></i>
                                    </div>
                                    <div class="progress mt-2" style="height: 5px;">
                                        <div class="progress-bar bg-success" role="progressbar" 
                                             style="width: {{ (doc_usage / plan_limits.max_documents * 100) if plan_limits.max_documents > 0 else 0 }}%"></div>
                                    </div>
                                    <small class="text-muted">
                                        {% if plan_limits.max_documents > 0 %}
                                            {{ plan_limits.max_documents - doc_usage|default(0) }} remaining
                                        {% else %}
                                            Unlimited
                                        {% endif %}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6 class="text-muted">Plan</h6>
                                            <h4>{{ tenant.plan|title }}</h4>
                                        </div>
                                        <i class="fas fa-crown fa-2x text-warning"></i>
                                    </div>
                                    <small class="text-muted">
                                        <a href="#" class="text-primary">Upgrade Plan</a>
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="row">
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0">Recent Queries</h6>
                                </div>
                                <div class="card-body">
                                    {% if recent_queries %}
                                        {% for query in recent_queries %}
                                        <div class="d-flex justify-content-between align-items-start mb-3">
                                            <div>
                                                <strong>{{ query.question[:60] }}{% if query.question|length > 60 %}...{% endif %}</strong>
                                                <br><small class="text-muted">{{ query.created_at.strftime('%Y-%m-%d %H:%M') }}</small>
                                            </div>
                                            <span class="badge bg-primary">{{ query.confidence_score|round(2) if query.confidence_score else 'N/A' }}</span>
                                        </div>
                                        {% endfor %}
                                    {% else %}
                                        <p class="text-muted">No recent queries. Start your legal research!</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0">Recent Documents</h6>
                                </div>
                                <div class="card-body">
                                    {% if recent_docs %}
                                        {% for doc in recent_docs %}
                                        <div class="mb-3">
                                            <strong>{{ doc.original_filename }}</strong>
                                            <br><small class="text-muted">{{ doc.document_type|title }} • {{ doc.created_at.strftime('%Y-%m-%d') }}</small>
                                        </div>
                                        {% endfor %}
                                    {% else %}
                                        <p class="text-muted">No documents uploaded yet.</p>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Research Tab -->
                <div id="research-content" class="tab-content" style="display: none;">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">Legal Research</h1>
                    </div>

                    <!-- Search Filters -->
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="mb-0">Search Filters</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <label class="form-label">Jurisdiction</label>
                                    <select class="form-select" id="jurisdictionFilter" multiple>
                                        <option value="Supreme Court of Pakistan">Supreme Court of Pakistan</option>
                                        <option value="Lahore High Court">Lahore High Court</option>
                                        <option value="Karachi High Court (Sindh)">Karachi High Court (Sindh)</option>
                                        <option value="Peshawar High Court">Peshawar High Court</option>
                                        <option value="Quetta High Court (Balochistan)">Quetta High Court (Balochistan)</option>
                                        <option value="Islamabad High Court">Islamabad High Court</option>
                                    </select>
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Legal Area</label>
                                    <select class="form-select" id="legalAreaFilter" multiple>
                                        <option value="Constitutional Law">Constitutional Law</option>
                                        <option value="Criminal Law">Criminal Law</option>
                                        <option value="Civil Law">Civil Law</option>
                                        <option value="Commercial Law">Commercial Law</option>
                                        <option value="Islamic Law">Islamic Law</option>
                                        <option value="Family Law">Family Law</option>
                                        <option value="Property Law">Property Law</option>
                                    </select>
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Document Type</label>
                                    <select class="form-select" id="docTypeFilter" multiple>
                                        <option value="case_law">Case Law</option>
                                        <option value="statute">Statute</option>
                                        <option value="contract">Contract</option>
                                        <option value="pleading">Pleading</option>
                                        <option value="opinion">Opinion</option>
                                    </select>
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Court Level</label>
                                    <select class="form-select" id="courtLevelFilter" multiple>
                                        <option value="supreme">Supreme</option>
                                        <option value="high">High</option>
                                        <option value="district">District</option>
                                        <option value="session">Session</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Chat Interface -->
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <i class="fas fa-comments me-2"></i>Legal Research Chat
                            </h6>
                        </div>
                        <div class="card-body p-0">
                            <div id="chatMessages" class="chat-messages"></div>
                            <div class="border-top p-3">
                                <div class="row g-2">
                                    <div class="col">
                                        <input type="text" id="userInput" class="form-control" 
                                               placeholder="Ask about Pakistan law..." maxlength="500">
                                    </div>
                                    <div class="col-auto">
                                        <button id="sendBtn" class="btn btn-primary">
                                            <i class="fas fa-paper-plane"></i>
                                        </button>
                                    </div>
                                </div>
                                <div class="mt-2">
                                    <button id="exportPdfBtn" class="btn btn-outline-secondary btn-sm" disabled>
                                        <i class="fas fa-file-pdf me-1"></i>Export as PDF
                                    </button>
                                    <button id="clearChatBtn" class="btn btn-outline-secondary btn-sm ms-2">
                                        <i class="fas fa-trash me-1"></i>Clear Chat
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Documents Tab -->
                <div id="documents-content" class="tab-content" style="display: none;">
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">Document Management</h1>
                        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#uploadModal">
                            <i class="fas fa-upload me-2"></i>Upload Document
                        </button>
                    </div>

                    <div id="documentsTable">
                        <!-- Documents will be loaded here -->
                    </div>
                </div>

                <!-- Other tabs... -->
            </main>
        </div>
    </div>

    <!-- Upload Modal -->
    <div class="modal fade" id="uploadModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Upload Legal Document</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="uploadForm" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label">Select Document</label>
                            <input type="file" class="form-control" name="file" accept=".pdf,.docx,.txt" required>
                            <div class="form-text">Supported formats: PDF, DOCX, TXT (Max: 16MB)</div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" form="uploadForm" class="btn btn-primary">Upload</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Tab switching
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Update active tab
                document.querySelectorAll('[data-tab]').forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Show tab content
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.style.display = 'none';
                });
                document.getElementById(this.dataset.tab + '-content').style.display = 'block';
            });
        });

        // Chat functionality
        let lastAnswer = '';
        let lastCitations = [];

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            const filters = {
                jurisdiction: Array.from(document.getElementById('jurisdictionFilter').selectedOptions).map(o => o.value),
                legal_area: Array.from(document.getElementById('legalAreaFilter').selectedOptions).map(o => o.value),
                document_type: Array.from(document.getElementById('docTypeFilter').selectedOptions).map(o => o.value),
                court_level: Array.from(document.getElementById('courtLevelFilter').selectedOptions).map(o => o.value)
            };

            addMessage(message, 'user');
            input.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    },
                    body: JSON.stringify({ 
                        message: message,
                        filters: filters
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    addMessage(data.reply, 'bot', data.sources);
                    lastAnswer = data.reply;
                    lastCitations = data.sources;
                    document.getElementById('exportPdfBtn').disabled = false;
                } else {
                    addMessage('Error: ' + data.error, 'bot');
                }
            } catch (error) {
                addMessage('Error: Failed to get response', 'bot');
            }
        }

        function addMessage(content, type, sources = []) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            let sourcesHtml = '';
            if (sources && sources.length > 0) {
                sourcesHtml = `<div class="mt-2 small"><strong>Sources:</strong> ${sources.join(', ')}</div>`;
            }
            
            messageDiv.innerHTML = content + sourcesHtml;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        // Event listeners
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        document.getElementById('sendBtn').addEventListener('click', sendMessage);

        document.getElementById('clearChatBtn').addEventListener('click', function() {
            document.getElementById('chatMessages').innerHTML = '';
            document.getElementById('exportPdfBtn').disabled = true;
        });

        // Document upload
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/api/upload-document', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    },
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Document uploaded successfully!');
                    bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
                    this.reset();
                    loadDocuments(); // Refresh documents list
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Upload failed. Please try again.');
            }
        });

        // Load documents
        async function loadDocuments() {
            try {
                const response = await fetch('/api/documents', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });
                
                const data = await response.json();
                
                let html = '<div class="table-responsive"><table class="table"><thead><tr>';
                html += '<th>Document</th><th>Type</th><th>Legal Areas</th><th>Upload Date</th><th>Actions</th>';
                html += '</tr></thead><tbody>';
                
                data.documents.forEach(doc => {
                    html += `<tr>
                        <td>${doc.filename}</td>
                        <td><span class="badge bg-secondary">${doc.document_type}</span></td>
                        <td>${doc.legal_areas.join(', ')}</td>
                        <td>${new Date(doc.upload_date).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDocument(${doc.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>`;
                });
                
                html += '</tbody></table></div>';
                document.getElementById('documentsTable').innerHTML = html;
                
            } catch (error) {
                console.error('Failed to load documents:', error);
            }
        }

        // Load documents when documents tab is shown
        document.querySelector('[data-tab="documents"]').addEventListener('click', loadDocuments);
    </script>
</body>
</html>
"""

def render_template_content(template_name, **kwargs):
    """Render template content with variables"""
    templates = {
        'auth/register_tenant.html': TENANT_REGISTRATION_TEMPLATE,
        'auth/login.html': LOGIN_TEMPLATE,
        'saas/dashboard.html': DASHBOARD_TEMPLATE
    }
    
    template_content = templates.get(template_name, '')
    
    # Simple template variable replacement
    for key, value in kwargs.items():
        template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))
    
    return template_content