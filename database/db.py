import os
import sqlite3
from contextlib import contextmanager

# Define database path within project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "bugsense.db")

def ensure_dirs():
    """Ensure data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "raw"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)

@contextmanager
def get_db():
    """Context manager for SQLite database connection with row factory."""
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize SQLite database tables and indexes."""
    ensure_dirs()
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('tester', 'developer', 'lead', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Developers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS developers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                expertise_modules TEXT NOT NULL, -- Comma-separated or JSON list e.g. "Payment, Checkout"
                current_workload INTEGER DEFAULT 0
            );
        """)

        # 3. Categories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );
        """)

        # 3. Bugs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                steps_to_reproduce TEXT,
                expected_result TEXT,
                actual_result TEXT,
                module TEXT NOT NULL, -- e.g. Auth, Cart, Checkout, Payment, Orders, Catalog, Profile
                environment TEXT DEFAULT 'QA', -- Production, Staging, QA, Development
                error_logs TEXT,
                severity TEXT NOT NULL, -- Critical, High, Medium, Low
                category TEXT NOT NULL, -- Functional, UI/UX, Security, Performance, Integration
                status TEXT DEFAULT 'New' CHECK(status IN ('New', 'Triaged', 'In Progress', 'Resolved', 'Closed')),
                reporter_id INTEGER,
                predicted_severity TEXT,
                predicted_category TEXT,
                similarity_flag TEXT,
                recommended_dev_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reporter_id) REFERENCES users (id) ON DELETE SET NULL,
                FOREIGN KEY (recommended_dev_id) REFERENCES developers (id) ON DELETE SET NULL
            );
        """)

        # 4. Bug Assignments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_id INTEGER NOT NULL,
                developer_id INTEGER NOT NULL,
                assigned_by INTEGER,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (bug_id) REFERENCES bugs (id) ON DELETE CASCADE,
                FOREIGN KEY (developer_id) REFERENCES developers (id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_by) REFERENCES users (id) ON DELETE SET NULL
            );
        """)

        # 5. Bug Resolutions Table (Historical knowledge base for AI suggestions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_resolutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_id INTEGER UNIQUE NOT NULL,
                root_cause TEXT NOT NULL,
                resolution_text TEXT NOT NULL,
                resolved_by INTEGER,
                resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bug_id) REFERENCES bugs (id) ON DELETE CASCADE,
                FOREIGN KEY (resolved_by) REFERENCES users (id) ON DELETE SET NULL
            );
        """)

        # 6. Bug Comments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bug_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bug_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bug_id) REFERENCES bugs (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # 7. Audit Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            );
        """)

        # Indexes for fast search and filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bugs_status ON bugs(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bugs_module ON bugs(module);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bugs_severity ON bugs(severity);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bugs_category ON bugs(category);")

    return True

if __name__ == "__main__":
    init_db()
    print("BugSense AI Database initialized successfully at:", DB_PATH)
