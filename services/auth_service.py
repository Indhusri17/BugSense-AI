import hashlib
import secrets
from database.db import get_db

def generate_salt() -> str:
    """Generate a random 16-byte hex salt."""
    return secrets.token_hex(16)

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password using PBKDF2-HMAC-SHA256 with salt."""
    if not salt:
        salt = generate_salt()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100_000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify incoming plain password against stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)

def register_user(username: str, password: str, full_name: str, role: str) -> tuple[bool, str]:
    """Register a new user in the database."""
    username = username.strip().lower()
    if not username or not password or not full_name:
        return False, "Username, password, and full name are required."
    
    if role not in ('tester', 'developer', 'lead', 'admin'):
        return False, "Invalid role specified."

    pwd_hash, salt = hash_password(password)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, salt, full_name, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, pwd_hash, salt, full_name.strip(), role)
            )
            user_id = cursor.lastrowid
            
            # Log audit
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "USER_REGISTERED", f"User {username} registered with role {role}")
            )
            return True, "User registered successfully."
    except Exception as e:
        if "UNIQUE constraint failed: users.username" in str(e):
            return False, f"Username '{username}' already exists."
        return False, f"Registration failed: {str(e)}"

def authenticate_user(username: str, password: str):
    """Authenticate username & password. Returns user dict or None."""
    username = username.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, salt, full_name, role, created_at FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        user_dict = dict(row)
        if verify_password(password, user_dict["password_hash"], user_dict["salt"]):
            # Record audit log
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
                (user_dict["id"], "USER_LOGIN", f"User {username} logged in successfully")
            )
            # Remove hash and salt before returning user session payload
            del user_dict["password_hash"]
            del user_dict["salt"]
            return user_dict
        return None

def get_user_by_id(user_id: int):
    """Retrieve user profile by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, full_name, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_users():
    """Retrieve all users list."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, created_at FROM users ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]
