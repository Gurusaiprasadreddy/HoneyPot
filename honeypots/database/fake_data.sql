CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    password_hash VARCHAR(255),
    credit_card VARCHAR(20),
    ssn VARCHAR(11)
);

INSERT INTO users (username, email, password_hash, credit_card, ssn) VALUES
('john.smith',   'john@corp.com',  '$2b$12$fakeABCDEF1234567890ab', '4532-1234-5678-9012', '123-45-6789'),
('sarah.jones',  'sarah@corp.com', '$2b$12$fakeXYZ9876543210uvwx',  '5425-2334-3010-9903', '987-65-4321'),
('admin',        'admin@corp.com', '$2b$12$fakeROOTadmin000000001', '4111-1111-1111-1111', '000-00-0001');

CREATE TABLE IF NOT EXISTS financial_records (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(20),
    balance DECIMAL(12,2),
    account_holder VARCHAR(100)
);

INSERT INTO financial_records VALUES
(1, 'ACC-00234511', 1250000.00, 'Acme Corporation'),
(2, 'ACC-00891234',  750000.50, 'John Smith');

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_value VARCHAR(64),
    service VARCHAR(50),
    owner VARCHAR(50)
);

INSERT INTO api_keys VALUES
(1, 'sk-prod-xK9mN2pL7qR4vT8wY3zA6bC1dE5fG0hJ', 'OpenAI',    'admin'),
(2, 'ghp_fakeGitHubToken1234567890abcdef12',        'GitHub',    'jenkins'),
(3, 'AKIAIOSFODNN7EXAMPLE',                         'AWS',       'devops');