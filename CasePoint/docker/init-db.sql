-- KanoonPK Database Initialization
-- This script sets up the initial database structure and sample data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create legal_documents table
CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    citation VARCHAR(255),
    jurisdiction VARCHAR(100),
    court_level VARCHAR(100),
    date_decided DATE,
    legal_area VARCHAR(100),
    document_type VARCHAR(50) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    extracted_text TEXT,
    ocr_confidence DECIMAL(5,2),
    keywords TEXT[],
    citations_found TEXT[],
    is_processed BOOLEAN DEFAULT FALSE,
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create search_logs table
CREATE TABLE IF NOT EXISTS search_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    search_type VARCHAR(50) NOT NULL,
    filters JSONB,
    results_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_legal_documents_citation ON legal_documents(citation);
CREATE INDEX IF NOT EXISTS idx_legal_documents_jurisdiction ON legal_documents(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_legal_documents_legal_area ON legal_documents(legal_area);
CREATE INDEX IF NOT EXISTS idx_legal_documents_date_decided ON legal_documents(date_decided);
CREATE INDEX IF NOT EXISTS idx_legal_documents_file_hash ON legal_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_legal_documents_keywords ON legal_documents USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_legal_documents_text_search ON legal_documents USING GIN(to_tsvector('english', extracted_text));
CREATE INDEX IF NOT EXISTS idx_search_logs_user_id ON search_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs(created_at);

-- Insert sample legal documents
INSERT INTO legal_documents (
    title, citation, jurisdiction, court_level, date_decided, legal_area, 
    document_type, original_filename, file_path, file_size, file_hash,
    extracted_text, ocr_confidence, keywords, citations_found, is_processed
) VALUES 
(
    'Constitution Petition regarding Fundamental Rights',
    '2024 SCMR 1234',
    'Supreme Court of Pakistan',
    'Supreme Court',
    '2024-01-15',
    'Constitutional Law',
    'pdf',
    'constitutional_petition_2024.pdf',
    '/documents/constitutional_petition_2024.pdf',
    524288,
    'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
    'This petition concerns the fundamental rights enshrined in Articles 8-28 of the Constitution of Pakistan. The petitioner challenges the validity of certain administrative actions...',
    95.5,
    ARRAY['constitutional law', 'fundamental rights', 'petition', 'supreme court'],
    ARRAY['Constitution of Pakistan 1973', 'Article 8', 'Article 25'],
    true
),
(
    'Contract Dispute Commercial Law Case',
    '2024 PLD 567',
    'Lahore High Court',
    'High Court',
    '2024-02-20',
    'Contract Law',
    'pdf',
    'contract_dispute_2024.pdf',
    '/documents/contract_dispute_2024.pdf',
    387456,
    'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1',
    'The present case involves a commercial contract dispute between two parties regarding the breach of contract terms and conditions stipulated in the agreement...',
    92.3,
    ARRAY['contract law', 'commercial dispute', 'breach of contract', 'damages'],
    ARRAY['Contract Act 1872', 'Section 73'],
    true
),
(
    'Criminal Appeal Murder Case',
    '2024 CLR 890',
    'Karachi High Court', 
    'High Court',
    '2024-03-10',
    'Criminal Law',
    'jpeg',
    'criminal_appeal_scan.jpeg',
    '/documents/criminal_appeal_scan.jpeg',
    156789,
    'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a1b2',
    'Criminal Appeal against conviction under Section 302 PPC. The appellant challenges the judgment passed by learned Sessions Judge convicting him for murder...',
    88.7,
    ARRAY['criminal law', 'murder', 'appeal', 'section 302 ppc'],
    ARRAY['Pakistan Penal Code', 'Section 302', 'Qanun-e-Shahadat'],
    true
);

-- Create admin user
INSERT INTO users (email, password_hash, full_name, subscription_tier, is_verified) VALUES 
('admin@kanoonpk.com', '$2b$12$LQv3c1yqBwrf2g0L8x0XHOqxG9t1VaHGdtJZA0W8mVFW8QBjNGX7i', 'KanoonPK Admin', 'admin', true);

-- Sample search logs
INSERT INTO search_logs (user_id, query, search_type, filters, results_count, execution_time_ms) VALUES 
((SELECT id FROM users WHERE email = 'admin@kanoonpk.com'), 'constitutional rights', 'basic', '{}', 5, 245),
((SELECT id FROM users WHERE email = 'admin@kanoonpk.com'), 'contract breach damages', 'advanced', '{"jurisdiction": "Lahore High Court", "legal_area": "Contract Law"}', 12, 156),
((SELECT id FROM users WHERE email = 'admin@kanoonpk.com'), 'murder appeal conviction', 'ai_advanced', '{"date_range": "2024"}', 8, 1234);