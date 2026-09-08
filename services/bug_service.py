from datetime import datetime
from database.db import get_db

def create_bug(
    title: str,
    description: str,
    steps_to_reproduce: str = "",
    expected_result: str = "",
    actual_result: str = "",
    module: str = "General",
    environment: str = "QA",
    error_logs: str = "",
    severity: str = "Medium",
    category: str = "Functional",
    reporter_id: int = None,
    predicted_severity: str = None,
    predicted_category: str = None,
    similarity_flag: str = None,
    recommended_dev_id: int = None
) -> int:
    """Create a new bug report in the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bugs (
                title, description, steps_to_reproduce, expected_result, actual_result,
                module, environment, error_logs, severity, category, status,
                reporter_id, predicted_severity, predicted_category,
                similarity_flag, recommended_dev_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                title.strip(), description.strip(), steps_to_reproduce.strip(),
                expected_result.strip(), actual_result.strip(), module, environment,
                error_logs.strip(), severity, category, reporter_id,
                predicted_severity, predicted_category, similarity_flag, recommended_dev_id
            )
        )
        bug_id = cursor.lastrowid

        # Log audit entry
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (reporter_id, "BUG_CREATED", f"Bug #{bug_id} filed: '{title}' [{severity}/{module}]")
        )

        return bug_id

def get_all_bugs(
    search: str = None,
    status: str = None,
    severity: str = None,
    module: str = None,
    category: str = None,
    limit: int = 200,
    offset: int = 0
) -> list[dict]:
    """Retrieve list of bugs with filtering and optional full text search."""
    query = """
        SELECT 
            b.*,
            u.username as reporter_username,
            u.full_name as reporter_name,
            d.name as assigned_dev_name,
            d.id as assigned_dev_id,
            rec_d.name as recommended_dev_name,
            res.root_cause,
            res.resolution_text
        FROM bugs b
        LEFT JOIN users u ON b.reporter_id = u.id
        LEFT JOIN (
            SELECT ba.bug_id, ba.developer_id, MAX(ba.assigned_at)
            FROM bug_assignments ba
            GROUP BY ba.bug_id
        ) latest_assign ON b.id = latest_assign.bug_id
        LEFT JOIN developers d ON latest_assign.developer_id = d.id
        LEFT JOIN developers rec_d ON b.recommended_dev_id = rec_d.id
        LEFT JOIN bug_resolutions res ON b.id = res.bug_id
        WHERE 1=1
    """
    params = []

    if search:
        search_term = f"%{search.strip()}%"
        query += " AND (b.title LIKE ? OR b.description LIKE ? OR b.error_logs LIKE ?)"
        params.extend([search_term, search_term, search_term])

    if status and status != "All":
        query += " AND b.status = ?"
        params.append(status)

    if severity and severity != "All":
        query += " AND b.severity = ?"
        params.append(severity)

    if module and module != "All":
        query += " AND b.module = ?"
        params.append(module)

    if category and category != "All":
        query += " AND b.category = ?"
        params.append(category)

    query += " ORDER BY b.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_bug_by_id(bug_id: int) -> dict:
    """Retrieve complete single bug details."""
    query = """
        SELECT 
            b.*,
            u.username as reporter_username,
            u.full_name as reporter_name,
            d.name as assigned_dev_name,
            d.id as assigned_dev_id,
            rec_d.name as recommended_dev_name,
            res.root_cause,
            res.resolution_text,
            res.resolved_at,
            res_u.full_name as resolved_by_name
        FROM bugs b
        LEFT JOIN users u ON b.reporter_id = u.id
        LEFT JOIN (
            SELECT ba.bug_id, ba.developer_id, MAX(ba.assigned_at)
            FROM bug_assignments ba
            GROUP BY ba.bug_id
        ) latest_assign ON b.id = latest_assign.bug_id
        LEFT JOIN developers d ON latest_assign.developer_id = d.id
        LEFT JOIN developers rec_d ON b.recommended_dev_id = rec_d.id
        LEFT JOIN bug_resolutions res ON b.id = res.bug_id
        LEFT JOIN users res_u ON res.resolved_by = res_u.id
        WHERE b.id = ?
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (bug_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_bug_status(bug_id: int, new_status: str, user_id: int = None, notes: str = "") -> bool:
    """Update status of a bug and record audit log."""
    valid_statuses = ('New', 'Triaged', 'In Progress', 'Resolved', 'Closed')
    if new_status not in valid_statuses:
        return False

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE bugs 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, bug_id)
        )
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, "STATUS_UPDATED", f"Bug #{bug_id} status changed to '{new_status}'. Notes: {notes}")
        )
        return True

def assign_bug_to_developer(bug_id: int, developer_id: int, user_id: int = None, notes: str = "") -> bool:
    """Assign bug to a developer and increment developer workload."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bug_assignments (bug_id, developer_id, assigned_by, notes)
            VALUES (?, ?, ?, ?)
            """,
            (bug_id, developer_id, user_id, notes)
        )
        # Update developer current workload
        cursor.execute(
            "UPDATE developers SET current_workload = current_workload + 1 WHERE id = ?",
            (developer_id,)
        )
        # If bug is in 'New', auto-transition to 'In Progress' or 'Triaged'
        cursor.execute(
            """
            UPDATE bugs 
            SET status = CASE WHEN status = 'New' THEN 'Triaged' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (bug_id,)
        )
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, "BUG_ASSIGNED", f"Bug #{bug_id} assigned to Developer ID {developer_id}")
        )
        return True

def resolve_bug(bug_id: int, root_cause: str, resolution_text: str, user_id: int = None) -> bool:
    """Save bug resolution, mark status as Resolved, decrement dev workload."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bug_resolutions (bug_id, root_cause, resolution_text, resolved_by)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(bug_id) DO UPDATE SET
                root_cause = excluded.root_cause,
                resolution_text = excluded.resolution_text,
                resolved_by = excluded.resolved_by,
                resolved_at = CURRENT_TIMESTAMP
            """,
            (bug_id, root_cause.strip(), resolution_text.strip(), user_id)
        )
        # Transition status to Resolved
        cursor.execute(
            "UPDATE bugs SET status = 'Resolved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (bug_id,)
        )
        # Decrement assigned dev workload if applicable
        cursor.execute(
            """
            UPDATE developers 
            SET current_workload = MAX(0, current_workload - 1)
            WHERE id IN (
                SELECT developer_id FROM bug_assignments WHERE bug_id = ?
            )
            """,
            (bug_id,)
        )
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, "BUG_RESOLVED", f"Bug #{bug_id} resolved with root cause: '{root_cause[:40]}...'")
        )
        return True

def add_comment(bug_id: int, user_id: int, comment: str) -> bool:
    """Add a discussion comment to a bug."""
    if not comment.strip():
        return False
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bug_comments (bug_id, user_id, comment) VALUES (?, ?, ?)",
            (bug_id, user_id, comment.strip())
        )
        cursor.execute(
            "UPDATE bugs SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (bug_id,)
        )
        return True

def get_comments_for_bug(bug_id: int) -> list[dict]:
    """Get comments for a specific bug ordered chronologically."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, u.username, u.full_name, u.role
            FROM bug_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.bug_id = ?
            ORDER BY c.created_at ASC
            """,
            (bug_id,)
        )
        return [dict(r) for r in cursor.fetchall()]

def get_all_developers() -> list[dict]:
    """Retrieve all developers with their skills and workloads."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM developers ORDER BY current_workload ASC, name ASC")
        return [dict(r) for r in cursor.fetchall()]

def get_audit_logs(limit: int = 50) -> list[dict]:
    """Retrieve system audit logs."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.*, u.username, u.full_name, u.role
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.id DESC LIMIT ?
            """,
            (limit,)
        )
        return [dict(r) for r in cursor.fetchall()]

def get_kpi_stats() -> dict:
    """Calculate key dashboard performance and inventory metrics."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bugs")
        total_bugs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bugs WHERE status = 'New'")
        new_bugs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bugs WHERE status IN ('Triaged', 'In Progress')")
        in_progress_bugs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bugs WHERE status IN ('Resolved', 'Closed')")
        resolved_bugs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bugs WHERE severity = 'Critical'")
        critical_bugs = cursor.fetchone()[0]

        cursor.execute("SELECT module, COUNT(*) as count FROM bugs GROUP BY module ORDER BY count DESC")
        by_module = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT severity, COUNT(*) as count FROM bugs GROUP BY severity ORDER BY count DESC")
        by_severity = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT category, COUNT(*) as count FROM bugs GROUP BY category ORDER BY count DESC")
        by_category = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT status, COUNT(*) as count FROM bugs GROUP BY status ORDER BY count DESC")
        by_status = [dict(r) for r in cursor.fetchall()]

        resolution_rate = round((resolved_bugs / total_bugs * 100), 1) if total_bugs > 0 else 0.0

        return {
            "total_bugs": total_bugs,
            "new_bugs": new_bugs,
            "in_progress_bugs": in_progress_bugs,
            "resolved_bugs": resolved_bugs,
            "critical_bugs": critical_bugs,
            "resolution_rate": resolution_rate,
            "by_module": by_module,
            "by_severity": by_severity,
            "by_category": by_category,
            "by_status": by_status
        }
