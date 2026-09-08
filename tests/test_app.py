"""
Basic unit and integration tests for BugSense AI core modules.
"""
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db import init_db, get_db
from database.seed_data import seed_all
from services.auth_service import authenticate_user, register_user, hash_password, verify_password
from services.bug_service import create_bug, get_all_bugs, get_bug_by_id, update_bug_status, get_kpi_stats
from models.nlp_engine import ai_engine

def test_full_pipeline():
    print("[1/5] Initializing Database & Seed Data...")
    init_db()
    seed_all()
    print("      -> DB & Seed data successful.")

    print("[2/5] Testing Authentication Service...")
    # Verify password hashing
    h, s = hash_password("test_pass")
    assert verify_password("test_pass", h, s) is True
    assert verify_password("wrong_pass", h, s) is False

    # Test login
    user = authenticate_user("tester1", "password123")
    assert user is not None
    assert user["role"] == "tester"
    print("      -> Authentication verified.")

    print("[3/5] Testing Bug Service CRUD & Lifecycle...")
    stats_before = get_kpi_stats()
    total_before = stats_before["total_bugs"]

    new_bug_id = create_bug(
        title="Unit Test Bug: Payment checkout timeout",
        description="Checkout times out when connecting to simulated gateway",
        steps_to_reproduce="1. Click pay",
        expected_result="Success",
        actual_result="Timeout",
        module="Payment",
        environment="QA",
        severity="High",
        category="Functional",
        reporter_id=user["id"]
    )
    assert new_bug_id > 0

    bug = get_bug_by_id(new_bug_id)
    assert bug["title"] == "Unit Test Bug: Payment checkout timeout"
    assert bug["status"] == "New"

    # Status update
    update_bug_status(new_bug_id, "In Progress", user["id"], "Under investigation")
    bug_updated = get_bug_by_id(new_bug_id)
    assert bug_updated["status"] == "In Progress"
    print("      -> Bug CRUD & lifecycle operations verified.")

    print("[4/5] Testing AI Engine (TF-IDF & Classification)...")
    ai_engine.load_and_train()
    assert ai_engine.is_trained is True

    # Test duplicate detection with seeded payment bug
    dup_res = ai_engine.detect_duplicates_and_retrieve(
        title="Payment successful on Stripe but order status stuck in PENDING_PAYMENT",
        description="Credit card was charged but order remains pending"
    )
    assert dup_res["highest_similarity"] > 50.0
    print(f"      -> Duplicate detection score for duplicate query: {dup_res['highest_similarity']}%")
    assert len(dup_res["similar_bugs"]) > 0

    # Test severity prediction for critical terms
    sev_res = ai_engine.predict_severity("Double charge occurs on checkout", "Customer was charged twice")
    assert sev_res["predicted_severity"] == "Critical"
    print(f"      -> Severity prediction for critical phrase: {sev_res['predicted_severity']}")

    # Test category prediction
    cat_res = ai_engine.predict_category("Stripe webhook verification error", "HMAC SHA256 mismatch")
    assert cat_res["predicted_category"] in ("Integration", "Security")
    print(f"      -> Category prediction for webhook query: {cat_res['predicted_category']}")

    # Test user's specific scenario
    diag = ai_engine.analyze_full_defect(
        title="After successful payment, the order is not displayed in My Orders",
        description="Customer completed checkout and payment succeeded, but order is missing from My Orders."
    )
    assert diag["severity"] == "Critical"
    assert diag["category"] == "Payment / Order"
    assert len(diag["suggested_resolution_steps"]) >= 4
    assert diag["squad_routing"]["recommended_dev"]["name"] == "Alex Chen"
    print(f"      -> Scenario triage: {diag['severity']} | {diag['category']} | Lead: {diag['squad_routing']['recommended_dev']['name']}")
    print(f"      -> Steps: {diag['suggested_resolution_steps'][0]}")

    print("[5/5] All Core Tests Passed Successfully! BugSense AI is fully operational.")

if __name__ == "__main__":
    test_full_pipeline()
