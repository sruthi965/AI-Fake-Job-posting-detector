CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(120) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS job_analysis (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    job_title         VARCHAR(255) NOT NULL,
    company_name      VARCHAR(255),
    description       TEXT NOT NULL,
    requirements      TEXT,
    employment_type   VARCHAR(50),
    salary_range      VARCHAR(100),
    prediction        VARCHAR(50) NOT NULL,
    fraud_probability DECIMAL(5,2) NOT NULL,
    risk_indicators   TEXT,
    explanation       TEXT,
    model_used        VARCHAR(50),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id           INT NULL,
    INDEX idx_job_analysis_user (user_id, id),
    CONSTRAINT fk_job_analysis_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
