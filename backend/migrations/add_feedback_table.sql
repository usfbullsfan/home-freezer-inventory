-- Create feedback_submissions table
CREATE TABLE IF NOT EXISTS feedback_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('bug', 'enhancement')),
    description TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    github_issue_number INTEGER,
    github_issue_url TEXT,
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processed', 'failed')),
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback_submissions(status);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback_submissions(user_id);
