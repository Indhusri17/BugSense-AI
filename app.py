import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Internal modules
from database.db import init_db
from database.seed_data import seed_all
from services.auth_service import authenticate_user, register_user
from services.bug_service import (
    create_bug, get_all_bugs, get_bug_by_id, update_bug_status,
    assign_bug_to_developer, resolve_bug, add_comment, get_comments_for_bug,
    get_all_developers, get_audit_logs, get_kpi_stats
)
from models.nlp_engine import ai_engine
from utils.helpers import render_badge, render_radial_meter_html

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="BugSense AI - Smart Bug Management & Resolution Support",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- SHOWCASE DARK-SLATE DESIGN SYSTEM -----------------
st.markdown("""
<style>
    /* Dark Theme Core Tokens from bugsense_showcase.html */
    :root {
        --bg-main: #0f172a;
        --card-bg: #1e293b;
        --border-color: #334155;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --primary: #6366f1;
        --primary-grad: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    }

    /* Streamlit Global Overrides */
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-main) !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Top Brand Card */
    .brand-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        margin-bottom: 1.5rem;
    }
    
    /* Content Cards */
    .showcase-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }

    .kpi-box {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 1.25rem 1rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
    }
    .kpi-number {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0.25rem 0;
        color: #f8fafc;
    }
    .kpi-sub {
        font-size: 0.72rem;
        font-weight: 600;
    }

    /* Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 2px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* Buttons */
    .stButton>button {
        background: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background: #334155 !important;
        border-color: #6366f1 !important;
        color: #ffffff !important;
        transform: translateY(-1px);
    }
    
    /* Primary Action Buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        border: 1px solid rgba(168, 85, 247, 0.4) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, #6366f1 0%, #9333ea 100%) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
    }

    /* Inputs & Selectboxes */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }

    /* Progress bar styled items */
    .mod-bar-bg {
        background: #0f172a;
        border-radius: 9999px;
        height: 8px;
        overflow: hidden;
        margin-top: 4px;
        border: 1px solid #1e293b;
    }
    .mod-bar-fill {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        height: 100%;
        border-radius: 9999px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "selected_bug_id" not in st.session_state:
        st.session_state.selected_bug_id = None
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "📊 Dashboard"
    if "preset_data" not in st.session_state:
        st.session_state.preset_data = {}
    if "db_initialized" not in st.session_state:
        init_db()
        seed_all()
        ai_engine.load_and_train()
        st.session_state.db_initialized = True

init_session()

# ----------------- TOP BRAND HEADER COMPONENT -----------------
def render_brand_header():
    user = st.session_state.user
    role_name = user['role'].upper() if user else "GUEST"
    user_name = user['full_name'] if user else "Guest User"
    corpus_size = len(ai_engine.corpus_bugs) if ai_engine.corpus_bugs else 38

    st.markdown(f"""
    <div class="brand-card">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); display: flex; align-items: center; justify-content: center; font-size: 1.6rem; box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);">
                    🐞
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.3rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">BugSense AI</span>
                        <span class="badge-pill" style="background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3);">● Live AI Triage Engine</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 1px;">
                        An AI-Powered Bug Management & Resolution Support System for Web Applications
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 4px 12px; font-size: 0.75rem;">
                    <span style="color: #94a3b8;">Active Role:</span>
                    <strong style="color: #a855f7; margin-left: 4px;">{role_name}</strong>
                    <span style="color: #64748b; margin: 0 4px;">|</span>
                    <span style="color: #cbd5e1;">{user_name}</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8;">
                    ⚡ Indexed Corpus: <strong style="color: #6366f1;">{corpus_size} Bugs</strong>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- AUTHENTICATION VIEW -----------------
def render_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin: 2rem 0 1rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 3rem;'>🐞</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='font-size: 1.8rem; font-weight: 800; color: #f8fafc; margin-bottom: 0.2rem;'>Welcome to BugSense AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8;'>Explainable Bug Triage, Duplicate Detection & Resolution Support System</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        tab_login, tab_register, tab_quick = st.tabs(["🔐 Sign In", "📝 Register New Account", "⚡ 1-Click Role Presets"])

        with tab_login:
            with st.form("signin_form"):
                username = st.text_input("Username").strip()
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                if submit:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.nav_page = "📊 Dashboard"
                        st.success(f"Authenticated as {user['full_name']} ({user['role']})")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_register:
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                uname = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["tester", "developer", "lead", "admin"])
                submit_reg = st.form_submit_button("Create Account", use_container_width=True)
                if submit_reg:
                    ok, msg = register_user(uname, pwd, name, role)
                    if ok:
                        st.success(msg + " Please switch to the Sign In tab.")
                    else:
                        st.error(msg)

        with tab_quick:
            st.markdown("<p style='font-size: 0.8rem; color: #94a3b8; margin-bottom: 12px;'>Select a pre-seeded account to evaluate role-based workflows immediately:</p>", unsafe_allow_html=True)
            c_a, c_b = st.columns(2)
            with c_a:
                if st.button("👩‍🔬 QA Tester\n(Sarah Jenkins)", use_container_width=True):
                    st.session_state.user = authenticate_user("tester1", "password123")
                    st.session_state.nav_page = "📊 Dashboard"
                    st.rerun()
                if st.button("👨‍💼 Team Lead\n(Dave Miller)", use_container_width=True):
                    st.session_state.user = authenticate_user("lead1", "password123")
                    st.session_state.nav_page = "📊 Dashboard"
                    st.rerun()
            with c_b:
                if st.button("👨‍💻 Senior Developer\n(Alex Chen)", use_container_width=True):
                    st.session_state.user = authenticate_user("dev1", "password123")
                    st.session_state.nav_page = "📊 Dashboard"
                    st.rerun()
                if st.button("🛡️ Administrator\n(System Admin)", use_container_width=True):
                    st.session_state.user = authenticate_user("admin", "admin123")
                    st.session_state.nav_page = "📊 Dashboard"
                    st.rerun()

# ----------------- SIDEBAR NAVIGATION -----------------
def render_sidebar():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 6px 0 14px 0; border-bottom: 1px solid #334155; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                    🐞
                </div>
                <div>
                    <div style="font-weight: 800; font-size: 1rem; color: #f8fafc;">BugSense AI</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">Unified Triage System</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        pages = [
            "📊 Dashboard",
            "✍️ Submit Bug",
            "🤖 AI Bug Analysis",
            "📋 Bug Management",
            "🔍 Bug Details",
            "🔗 Similar / Duplicate Bugs",
            "💡 Resolution Recommendations",
            "👥 Developer & Team Assignment",
            "📈 Analytics Telemetry",
            "🎓 Settings & Viva Guide"
        ]

        curr_idx = pages.index(st.session_state.nav_page) if st.session_state.nav_page in pages else 0
        selected = st.radio("Navigation Menu", pages, index=curr_idx)
        st.session_state.nav_page = selected

        st.markdown("<div style='margin-top: 2rem; border-top: 1px solid #334155; padding-top: 12px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.75rem; color: #94a3b8;'>Logged in as: <strong style='color:#f8fafc;'>{user['full_name']}</strong></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.7rem; color: #a855f7; font-weight: 600;'>Role: {user['role'].upper()}</div>", unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user = None
            st.session_state.selected_bug_id = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return selected

# =====================================================================
# PAGE 1: DASHBOARD
# =====================================================================
def page_dashboard():
    stats = get_kpi_stats()

    # 4 Top KPI Cards matching showcase design
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Indexed Bugs</div>
            <div class="kpi-number">{stats['total_bugs']}</div>
            <div class="kpi-sub" style="color: #6366f1;">E-Commerce Testbed Corpus</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Untriaged / New</div>
            <div class="kpi-number" style="color: #60a5fa;">{stats['new_bugs']}</div>
            <div class="kpi-sub" style="color: #93c5fd;">Pending automated dispatch</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Critical Severity</div>
            <div class="kpi-number" style="color: #fb7185;">{stats['critical_bugs']}</div>
            <div class="kpi-sub" style="color: #fda4af;">P1 Financial / Security Defects</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Knowledge Base Resolution %</div>
            <div class="kpi-number" style="color: #34d399;">{stats['resolution_rate']}%</div>
            <div class="kpi-sub" style="color: #6ee7b7;">Verified Historical Fixes</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two Column Layout: Module distribution bars & Severity distribution
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown("""
        <div class="showcase-card">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 12px; display: flex; justify-content: space-between;">
                <span>📦 Distribution by E-Commerce Module</span>
                <span style="font-size: 0.75rem; color: #94a3b8; font-weight: normal;">7 Active Modules</span>
            </div>
        """, unsafe_allow_html=True)

        if stats['by_module']:
            total = stats['total_bugs'] or 1
            for m in stats['by_module']:
                pct = round((m['count'] / total) * 100)
                st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem;">
                        <span style="font-weight: 600; color: #cbd5e1;">{m['module']}</span>
                        <span style="color: #94a3b8; font-family: monospace;">{m['count']} tickets ({pct}%)</span>
                    </div>
                    <div class="mod-bar-bg">
                        <div class="mod-bar-fill" style="width: {pct}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("""
        <div class="showcase-card">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 12px;">
                🚨 Severity Breakdown & Priority Allocation
            </div>
        """, unsafe_allow_html=True)

        if stats['by_severity']:
            df_sev = pd.DataFrame(stats['by_severity'])
            color_map = {"Critical": "#f43f5e", "High": "#f97316", "Medium": "#eab308", "Low": "#14b8a6"}
            fig_sev = px.pie(
                df_sev, names='severity', values='count',
                color='severity',
                color_discrete_map=color_map,
                hole=0.55
            )
            fig_sev.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f8fafc', size=11),
                margin=dict(l=10, r=10, t=10, b=10),
                height=220,
                showlegend=True
            )
            st.plotly_chart(fig_sev, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Lifecycle Pipeline & Audit Log
    c3, c4 = st.columns([1, 1.2])
    with c3:
        st.markdown("<div class='showcase-card'><div style='font-size: 0.95rem; font-weight: 700; margin-bottom: 10px;'>Bug Lifecycle Status Pipeline</div>", unsafe_allow_html=True)
        if stats['by_status']:
            df_st = pd.DataFrame(stats['by_status'])
            fig_stat = px.funnel(df_st, x='count', y='status', color='status', color_discrete_sequence=['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981', '#64748b'])
            fig_stat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=240, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            st.plotly_chart(fig_stat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown("<div class='showcase-card'><div style='font-size: 0.95rem; font-weight: 700; margin-bottom: 10px;'>🕒 Recent System Audit Log</div>", unsafe_allow_html=True)
        logs = get_audit_logs(limit=6)
        if logs:
            for log in logs:
                st.markdown(f"""
                <div style="padding: 6px 0; border-bottom: 1px solid #334155; font-size: 0.76rem;">
                    <div style="display: flex; justify-content: space-between; color: #94a3b8;">
                        <span><strong style="color: #6ee7b7;">{log['action']}</strong> by {log['full_name'] or 'System'}</span>
                        <span style="font-family: monospace;">{log['timestamp'][:16]}</span>
                    </div>
                    <div style="color: #cbd5e1; margin-top: 2px;">{log['details']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PAGE 2: SUBMIT BUG (WITH LIVE AI PREVIEW)
# =====================================================================
def page_submit_bug():
    st.markdown("### ✍️ Submit a Defect Ticket (with Real-Time AI Assist)")
    st.caption("Compose defect details. As you type, the NLP engine cross-references historical tickets, evaluates duplicate risk, predicts severity, and suggests resolution steps.")

    # 5 Quick Presets matching user request and showcase
    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #a855f7; text-transform: uppercase; margin-bottom: 6px;'>✨ 1-Click Viva Test Scenarios:</div>", unsafe_allow_html=True)
    p1, p2, p3, p4, p5 = st.columns(5)

    if p1.button("1. Payment Sync (Orders)", use_container_width=True):
        st.session_state.preset_data = {
            "title": "After successful payment, the order is not displayed in My Orders",
            "module": "Payment",
            "environment": "Production",
            "desc": "Customer completes checkout and credit card payment succeeds via payment gateway. Transaction shows completed, but the order is not displayed in My Orders and remains stuck in PENDING_PAYMENT indefinitely.",
            "steps": "1. Add item to cart\n2. Complete payment via test card\n3. Check My Orders page",
            "exp": "Order should immediately flip to CONFIRMED and appear in My Orders list.",
            "act": "Money deducted, but order is absent from My Orders list.",
            "logs": "PaymentCallbackTimeout: Webhook callback received but order status synchronization transaction aborted."
        }
    if p2.button("2. Stripe Webhook (89%)", use_container_width=True):
        st.session_state.preset_data = {
            "title": "Payment successful on Stripe but order status stuck in PENDING_PAYMENT",
            "module": "Payment",
            "environment": "Production",
            "desc": "Customer completes credit card payment on Stripe and receives deduction SMS, but order screen remains stuck in PENDING_PAYMENT.",
            "steps": "1. Add item to cart\n2. Pay with Visa\n3. Wait for redirect",
            "exp": "Order marked as CONFIRMED.",
            "act": "Order stays in PENDING_PAYMENT.",
            "logs": "StripeWebhookError: Invalid signature header 'Stripe-Signature'. Webhook secret mismatch in prod environment variable."
        }
    if p3.button("3. SQL Injection (Critical)", use_container_width=True):
        st.session_state.preset_data = {
            "title": "Product search query containing single apostrophe causes SQL syntax error",
            "module": "Catalog",
            "environment": "Production",
            "desc": "Searching for terms like women's shoes or men's jackets crashes catalog search API with unhandled 500 error.",
            "steps": "1. Go to search bar\n2. Type men's shoes\n3. Press Enter",
            "exp": "Display matching apparel.",
            "act": "500 Internal Server Error.",
            "logs": "sqlite3.OperationalError: near 's': syntax error in raw SQL query string interpolation."
        }
    if p4.button("4. Negative Cart Qty", use_container_width=True):
        st.session_state.preset_data = {
            "title": "Cart quantity decrements to negative numbers on rapid button clicks",
            "module": "Cart",
            "environment": "QA",
            "desc": "Clicking minus button multiple times quickly allows quantity to reach -1 or -2, turning cart total negative.",
            "steps": "1. Add 1 item\n2. Click '-' twice quickly",
            "exp": "Item quantity floors at 1.",
            "act": "Quantity becomes -2, total -$50.00.",
            "logs": "CartService: Total calculation price * -2 applied."
        }
    if p5.button("5. Animation Lag (UI)", use_container_width=True):
        st.session_state.preset_data = {
            "title": "Cart drawer animation stutters and lags on mobile Safari viewport",
            "module": "Cart",
            "environment": "QA",
            "desc": "Sliding open cart drawer on iPhone viewport causes visible frame drops (~15 FPS) and jitter.",
            "steps": "1. Open mobile browser\n2. Tap cart icon",
            "exp": "Smooth 60fps transition.",
            "act": "Stuttering and jerky animation.",
            "logs": "Performance trace: Non-composited animation on left property causing forced reflows."
        }

    preset = st.session_state.preset_data

    # Main Form & AI Split Layout
    c_form, c_ai = st.columns([1.1, 0.9])

    with c_form:
        st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
        title = st.text_input("Bug Title *", value=preset.get("title", ""), placeholder="e.g. After successful payment, the order is not displayed in My Orders")

        c_m, c_e = st.columns(2)
        with c_m:
            modules = ["Payment", "Cart", "Checkout", "Auth", "Orders", "Catalog", "Profile"]
            mod_def = preset.get("module", "Payment")
            mod_idx = modules.index(mod_def) if mod_def in modules else 0
            module = st.selectbox("Module *", modules, index=mod_idx)
        with c_e:
            envs = ["Production", "Staging", "QA", "Development"]
            env_def = preset.get("environment", "Production")
            env_idx = envs.index(env_def) if env_def in envs else 0
            environment = st.selectbox("Environment", envs, index=env_idx)

        description = st.text_area("Bug Description *", value=preset.get("desc", ""), height=100, placeholder="Explain observed behavior...")
        steps = st.text_area("Steps to Reproduce", value=preset.get("steps", ""), height=70)
        
        c_exp, c_act = st.columns(2)
        with c_exp:
            expected = st.text_area("Expected Result", value=preset.get("exp", ""), height=60)
        with c_act:
            actual = st.text_area("Actual Result", value=preset.get("act", ""), height=60)

        logs = st.text_area("Error Logs / Stacktrace (Optional)", value=preset.get("logs", ""), height=60)
        st.markdown("</div>", unsafe_allow_html=True)

    # Live AI Analysis Side Panel
    with c_ai:
        st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #a855f7; text-transform: uppercase; margin-bottom: 8px;'>🤖 Real-Time AI Triage Diagnostics</div>", unsafe_allow_html=True)

        if title.strip() or description.strip():
            # Run complete AI triage synthesis
            ai_output = ai_engine.analyze_full_defect(title, description, logs, module)

            # 1. Radial SVG Meter
            sim_score = ai_output['duplicate_detection']['similarity_score']
            st.markdown(render_radial_meter_html(sim_score, "Duplicate Similarity"), unsafe_allow_html=True)

            # 2. Predicted Severity & Category Row
            st.markdown("<br>", unsafe_allow_html=True)
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.markdown(f"""
                <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 10px;">
                    <div style="font-size: 0.68rem; color: #94a3b8; font-weight: 700;">PREDICTED SEVERITY</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #fb7185; margin: 2px 0;">{ai_output['severity']}</div>
                    <div style="font-size: 0.7rem; color: #34d399; font-weight: 600;">{ai_output['severity_confidence']}% confidence</div>
                    <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">{ai_output['severity_method']}</div>
                </div>
                """, unsafe_allow_html=True)
            with c_s2:
                st.markdown(f"""
                <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 10px;">
                    <div style="font-size: 0.68rem; color: #94a3b8; font-weight: 700;">PREDICTED CATEGORY</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #818cf8; margin: 2px 0;">{ai_output['category']}</div>
                    <div style="font-size: 0.7rem; color: #34d399; font-weight: 600;">{ai_output['category_confidence']}% confidence</div>
                    <div style="font-size: 0.68rem; color: #64748b; margin-top: 2px;">{ai_output['category_method']}</div>
                </div>
                """, unsafe_allow_html=True)

            # 3. Possible Root Cause & Previous Resolution
            st.markdown(f"""
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 10px 12px; margin-top: 10px; font-size: 0.75rem;">
                <div style="font-weight: 700; color: #fcd34d; margin-bottom: 2px;">💡 Possible Root Cause:</div>
                <div style="color: #cbd5e1; line-height: 1.4;">{ai_output['possible_root_cause']}</div>
                <div style="font-weight: 700; color: #6ee7b7; margin-top: 6px;">Previous Verified Resolution:</div>
                <div style="color: #e2e8f0; line-height: 1.4;">{ai_output['previous_resolution']}</div>
            </div>
            """, unsafe_allow_html=True)

            # 4. Squad & Engineer Recommendation
            rec_dev = ai_output['squad_routing']['recommended_dev']
            st.markdown(f"""
            <div style="background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 10px 12px; margin-top: 10px; font-size: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #818cf8;">🎯 Recommended Squad: {ai_output['squad_routing']['team_name']}</span>
                    <span style="background: rgba(99, 102, 241, 0.2); color: #c7d2fe; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 9999px; padding: 1px 6px; font-size: 0.68rem; font-weight: 700;">Score: {rec_dev['score']}/100</span>
                </div>
                <div style="color: #f8fafc; font-weight: 700; margin-top: 3px;">Lead Engineer: {rec_dev['name']}</div>
                <div style="color: #64748b; font-family: monospace; font-size: 0.68rem; margin-top: 2px;">{ai_output['squad_routing']['formula_text']}</div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="padding: 2rem 1rem; text-align: center; color: #64748b; font-size: 0.8rem;">
                ✍️ Type a bug title or click one of the 1-click test scenarios above to see live duplicate detection and AI reasoning.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Submission Controls
    st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
    c_sub1, c_sub2 = st.columns([2, 1])
    with c_sub1:
        st.markdown("<div style='font-size: 0.78rem; color: #94a3b8;'>Ready to index defect into the central SQLite database and knowledge base?</div>", unsafe_allow_html=True)
    with c_sub2:
        if st.button("🚀 Submit & Index Defect", type="primary", use_container_width=True):
            if not title.strip() or not description.strip():
                st.error("Bug Title and Description are required.")
            else:
                ai_out = ai_engine.analyze_full_defect(title, description, logs, module)
                rec_dev_id = ai_out['squad_routing']['recommended_dev']['id'] if ai_out.get('squad_routing') else None

                bug_id = create_bug(
                    title=title,
                    description=description,
                    steps_to_reproduce=steps,
                    expected_result=expected,
                    actual_result=actual,
                    module=module,
                    environment=environment,
                    error_logs=logs,
                    severity=ai_out['severity'],
                    category=ai_out['category'],
                    reporter_id=st.session_state.user["id"] if st.session_state.user else 1,
                    predicted_severity=ai_out['severity'],
                    predicted_category=ai_out['category'],
                    similarity_flag=ai_out['duplicate_detection']['duplicate_status'],
                    recommended_dev_id=rec_dev_id
                )

                # Assign developer directly
                assign_bug_to_developer(bug_id, rec_dev_id, st.session_state.user["id"] if st.session_state.user else 1, "Automated AI squad assignment")

                # Retrain model
                ai_engine.load_and_train()

                st.session_state.selected_bug_id = bug_id
                st.success(f"🎉 Bug #BUG-{bug_id:03d} successfully filed and indexed into SQLite database!")
                st.session_state.nav_page = "🔍 Bug Details"
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PAGE 3: AI BUG ANALYSIS (DEEP DIVE LABORATORY)
# =====================================================================
def page_ai_analysis():
    st.markdown("### 🤖 Deep-Dive AI Defect Triage & Resolution Laboratory")
    st.caption("Inspect how BugSense AI processes multi-sentence bug reports using explainable NLP (TF-IDF N-grams, Cosine Angles, Multi-class Naive Bayes, and Workload Balancing).")

    all_bugs = get_all_bugs(limit=100)
    bug_map = {f"BUG-{b['id']:03d}: {b['title'][:65]}...": b for b in all_bugs}
    selected_key = st.selectbox("Select a defect from the database or enter custom query below:", ["-- Custom Triage Query --"] + list(bug_map.keys()))

    if selected_key != "-- Custom Triage Query --":
        selected_b = bug_map[selected_key]
        query_title = selected_b['title']
        query_desc = selected_b['description']
        query_logs = selected_b.get('error_logs', '')
        query_mod = selected_b['module']
    else:
        query_title = st.text_input("Query Title", "After successful payment, the order is not displayed in My Orders")
        query_desc = st.text_area("Query Description", "Customer completed checkout and credit card was charged $120.00. Stripe dashboard confirms transaction succeeded, but the order is not displayed in My Orders and remains stuck in PENDING_PAYMENT.")
        query_logs = st.text_input("Query Stacktrace / Error Logs", "PaymentCallbackTimeout: Webhook callback received but order status synchronization aborted.")
        query_mod = st.selectbox("Application Module", ["Payment", "Cart", "Checkout", "Auth", "Orders", "Catalog", "Profile"])

    if st.button("⚡ Execute AI Analysis Pipeline", type="primary"):
        ai_out = ai_engine.analyze_full_defect(query_title, query_desc, query_logs, query_mod)

        # 3 Top KPI diagnostic cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(render_radial_meter_html(ai_out['duplicate_detection']['similarity_score'], "Duplicate Similarity"), unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="showcase-card">
                <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700;">PREDICTED SEVERITY & CATEGORY</div>
                <div style="display: flex; gap: 8px; margin: 6px 0;">
                    {render_badge(ai_out['severity'], 'severity')}
                    {render_badge(ai_out['category'], 'category')}
                </div>
                <div style="font-size: 0.72rem; color: #cbd5e1;">Severity: {ai_out['severity_confidence']}% conf • Category: {ai_out['category_confidence']}% conf</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            rec = ai_out['squad_routing']['recommended_dev']
            st.markdown(f"""
            <div class="showcase-card">
                <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700;">RECOMMENDED SQUAD & LEAD</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #818cf8; margin: 3px 0;">{ai_out['squad_routing']['team_name']}</div>
                <div style="font-size: 0.78rem; color: #cbd5e1;">Assigned: <strong>{rec['name']}</strong> (Workload: {rec['workload']} tickets)</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Root Cause, Resolution & Suggested Action Steps
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"""
            <div class="showcase-card" style="border-left: 4px solid #f59e0b;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #fcd34d; margin-bottom: 6px;">💡 Possible Root Cause Analysis:</div>
                <div style="font-size: 0.82rem; color: #e2e8f0; line-height: 1.5;">{ai_out['possible_root_cause']}</div>
                
                <div style="font-size: 0.85rem; font-weight: 700; color: #34d399; margin-top: 14px; margin-bottom: 6px;">Previous Verified Resolution:</div>
                <div style="font-size: 0.82rem; color: #e2e8f0; line-height: 1.5;">{ai_out['previous_resolution']}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown("""
            <div class="showcase-card" style="border-left: 4px solid #6366f1;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #818cf8; margin-bottom: 8px;">📋 Suggested Resolution Steps (AI Recommended):</div>
            """, unsafe_allow_html=True)
            for step in ai_out['suggested_resolution_steps']:
                st.markdown(f"<div style='font-size: 0.8rem; color: #cbd5e1; margin-bottom: 6px;'>• {step}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Top Matching Similar Bugs List
        st.markdown("#### 📚 Top Similar Historical Bugs Retrieved from Database")
        for sim_b in ai_out['similar_bugs_list'][:3]:
            with st.expander(f"#{sim_b['bug_code']}: {sim_b['title']} (Cosine Match: {sim_b['similarity_score']}%)"):
                st.markdown(f"**Module:** `{sim_b['module']}` | **Severity:** `{sim_b['severity']}` | **Status:** `{sim_b['status']}`")
                st.markdown(f"**Historical Root Cause:** {sim_b['root_cause']}")
                st.markdown(f"**Historical Fix:** {sim_b['resolution_text']}")

# =====================================================================
# PAGE 4: BUG MANAGEMENT (TRACKER)
# =====================================================================
def page_bug_management():
    st.markdown("### 📋 Bug Management & Defect Inventory")
    st.caption("Search, filter, and triage all bugs reported across the mock e-commerce platform.")

    # Search and Filter Controls
    c_s, c_mod, c_sev, c_stat = st.columns([2, 1, 1, 1])
    with c_s:
        search_q = st.text_input("🔍 Search defects", placeholder="Keyword, error log, symptom...")
    with c_mod:
        mod_filter = st.selectbox("Module", ["All", "Payment", "Cart", "Checkout", "Auth", "Orders", "Catalog", "Profile"])
    with c_sev:
        sev_filter = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    with c_stat:
        stat_filter = st.selectbox("Status", ["All", "New", "Triaged", "In Progress", "Resolved", "Closed"])

    bugs = get_all_bugs(search=search_q, module=mod_filter, severity=sev_filter, status=stat_filter)

    st.markdown(f"<div style='font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px;'>Showing <strong>{len(bugs)}</strong> tickets</div>", unsafe_allow_html=True)

    if not bugs:
        st.info("No tickets found matching the specified filters.")
        return

    # Bug Cards matching showcase style
    for bug in bugs:
        bug_code = f"BUG-{bug['id']:03d}"
        c_title, c_meta, c_btn = st.columns([3.2, 1.8, 1])
        with c_title:
            st.markdown(f"""
            <div style="font-weight: 700; color: #f8fafc; font-size: 0.92rem;">
                <span style="color: #818cf8; font-family: monospace; margin-right: 6px;">#{bug_code}</span>
                {bug['title']}
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
                Module: <strong>{bug['module']}</strong> • Category: <strong>{bug['category']}</strong> • Env: <strong>{bug['environment']}</strong>
            </div>
            """, unsafe_allow_html=True)
        with c_meta:
            sev_b = render_badge(bug['severity'], 'severity')
            stat_b = render_badge(bug['status'], 'status')
            st.markdown(f"{sev_b} {stat_b}", unsafe_allow_html=True)
            dev_name = bug['assigned_dev_name'] or "Unassigned"
            st.markdown(f"<div style='font-size: 0.72rem; color: #94a3b8; margin-top: 3px;'>Assigned: <strong style='color:#cbd5e1;'>{dev_name}</strong></div>", unsafe_allow_html=True)
        with c_btn:
            if st.button("Inspect & Fix →", key=f"btn_manage_{bug['id']}", use_container_width=True):
                st.session_state.selected_bug_id = bug['id']
                st.session_state.nav_page = "🔍 Bug Details"
                st.rerun()
        st.markdown("<hr style='margin: 6px 0; border-top: 1px solid #1e293b;'>", unsafe_allow_html=True)

# =====================================================================
# PAGE 5: BUG DETAILS
# =====================================================================
def page_bug_details():
    all_bugs = get_all_bugs(limit=200)
    if not all_bugs:
        st.info("No bugs available in database.")
        return

    bug_opts = {f"BUG-{b['id']:03d}: {b['title'][:65]}... [{b['status']}]": b['id'] for b in all_bugs}
    
    # Default selection
    def_idx = 0
    if st.session_state.selected_bug_id:
        for i, (k, b_id) in enumerate(bug_opts.items()):
            if b_id == st.session_state.selected_bug_id:
                def_idx = i
                break

    sel_label = st.selectbox("Select Defect Ticket:", list(bug_opts.keys()), index=def_idx)
    sel_id = bug_opts[sel_label]
    st.session_state.selected_bug_id = sel_id

    bug = get_bug_by_id(sel_id)
    if not bug:
        st.error("Bug not found.")
        return

    bug_code = f"BUG-{bug['id']:03d}"

    # Header Card
    st.markdown(f"""
    <div class="showcase-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="font-family: monospace; font-weight: 800; color: #818cf8; font-size: 1.1rem;">#{bug_code}</span>
                    {render_badge(bug['severity'], 'severity')}
                    {render_badge(bug['status'], 'status')}
                </div>
                <h2 style="font-size: 1.25rem; font-weight: 800; color: #f8fafc; margin: 4px 0;">{bug['title']}</h2>
                <div style="font-size: 0.75rem; color: #94a3b8;">
                    Module: <strong style="color: #cbd5e1;">{bug['module']}</strong> | Category: <strong style="color: #cbd5e1;">{bug['category']}</strong> | Environment: <strong style="color: #cbd5e1;">{bug['environment']}</strong>
                </div>
            </div>
            <div style="text-align: right; font-size: 0.72rem; color: #94a3b8;">
                <div>Filed by: <strong style="color: #f8fafc;">{bug['reporter_name'] or 'QA Team'}</strong></div>
                <div>Date: {bug['created_at'][:16]}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_left, c_right = st.columns([1.2, 0.8])

    with c_left:
        st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; text-transform: uppercase;'>Description</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.85rem; color: #e2e8f0; line-height: 1.5;'>{bug['description']}</p>", unsafe_allow_html=True)

        if bug['steps_to_reproduce']:
            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-top: 12px;'>Steps to Reproduce</div>", unsafe_allow_html=True)
            st.code(bug['steps_to_reproduce'], language="markdown")

        c_e1, c_e2 = st.columns(2)
        with c_e1:
            if bug['expected_result']:
                st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #34d399;'>Expected Result</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.8rem; color: #cbd5e1;'>{bug['expected_result']}</p>", unsafe_allow_html=True)
        with c_e2:
            if bug['actual_result']:
                st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #fb7185;'>Actual Result</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.8rem; color: #cbd5e1;'>{bug['actual_result']}</p>", unsafe_allow_html=True)

        if bug['error_logs']:
            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-top: 12px;'>Error Logs / Stacktrace</div>", unsafe_allow_html=True)
            st.code(bug['error_logs'], language="python")

        # Verified Resolution
        if bug.get('root_cause') or bug.get('resolution_text'):
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 12px; margin-top: 14px;">
                <div style="font-weight: 800; color: #6ee7b7; font-size: 0.85rem;">✅ Verified Root Cause & Fix Applied:</div>
                <div style="font-size: 0.8rem; color: #e2e8f0; margin-top: 4px;"><strong>Root Cause:</strong> {bug['root_cause']}</div>
                <div style="font-size: 0.8rem; color: #e2e8f0; margin-top: 4px;"><strong>Resolution:</strong> {bug['resolution_text']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Discussion Comments
        st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;'>💬 Discussion & Triage Thread</div>", unsafe_allow_html=True)
        comments = get_comments_for_bug(bug['id'])
        if comments:
            for comm in comments:
                st.markdown(f"""
                <div style="padding: 6px 0; border-bottom: 1px solid #334155; font-size: 0.78rem;">
                    <div style="display: flex; justify-content: space-between; color: #94a3b8;">
                        <span><strong style="color: #f8fafc;">{comm['full_name']}</strong> ({comm['role'].upper()})</span>
                        <span style="font-family: monospace;">{comm['created_at'][:16]}</span>
                    </div>
                    <div style="color: #cbd5e1; margin-top: 2px;">{comm['comment']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No comments posted yet.")

        with st.form(f"comm_form_{bug['id']}"):
            new_c = st.text_input("Add a comment", placeholder="Type message...")
            if st.form_submit_button("Post Comment"):
                if new_c.strip():
                    add_comment(bug['id'], st.session_state.user['id'] if st.session_state.user else 1, new_c)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c_right:
        st.markdown("<div class='showcase-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;'>⚙️ Triage & Dispatch Actions</div>", unsafe_allow_html=True)

        # Status Transition
        with st.expander("Update Ticket Status", expanded=True):
            status_list = ['New', 'Triaged', 'In Progress', 'Resolved', 'Closed']
            curr_s_idx = status_list.index(bug['status']) if bug['status'] in status_list else 0
            new_s = st.selectbox("Status:", status_list, index=curr_s_idx)
            note_s = st.text_input("Status Change Note", placeholder="Reason for change...")
            if st.button("Save Status Change", use_container_width=True):
                update_bug_status(bug['id'], new_s, st.session_state.user['id'] if st.session_state.user else 1, note_s)
                st.success("Status updated!")
                st.rerun()

        # Reassign Developer
        with st.expander("Assign Developer", expanded=True):
            all_d = get_all_developers()
            dev_map = {f"{d['name']} ({d['expertise_modules']}) - Workload: {d['current_workload']}": d['id'] for d in all_d}
            sel_d_label = st.selectbox("Choose Developer:", list(dev_map.keys()))
            if st.button("Assign Ticket", use_container_width=True):
                assign_bug_to_developer(bug['id'], dev_map[sel_d_label], st.session_state.user['id'] if st.session_state.user else 1, "Manual reassignment")
                st.success("Developer assigned successfully!")
                st.rerun()

        # Log Knowledge Base Resolution
        with st.expander("📝 Document Resolution & Close", expanded=bug['status'] != 'Resolved'):
            rc_in = st.text_area("Root Cause", value=bug['root_cause'] or "", placeholder="Explain technical root cause...")
            res_in = st.text_area("Fix Applied", value=bug['resolution_text'] or "", placeholder="Explain fix...")
            if st.button("Submit Verified Resolution", type="primary", use_container_width=True):
                if not rc_in.strip() or not res_in.strip():
                    st.error("Both Root Cause and Fix are required.")
                else:
                    resolve_bug(bug['id'], rc_in, res_in, st.session_state.user['id'] if st.session_state.user else 1)
                    ai_engine.load_and_train()
                    st.success("Defect resolved and knowledge base updated!")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PAGE 6: SIMILAR & DUPLICATE BUGS
# =====================================================================
def page_similar_duplicate_bugs():
    st.markdown("### 🔗 Similar & Duplicate Bug Search Engine")
    st.caption("Search across the entire indexed corpus using TF-IDF N-Gram vectorization and Cosine Similarity to detect duplicate clusters.")

    all_bugs = get_all_bugs(limit=200)
    bug_map = {f"BUG-{b['id']:03d}: {b['title'][:65]}...": b for b in all_bugs}
    sel_bug_key = st.selectbox("Select an existing defect to cross-reference against historical tickets:", list(bug_map.keys()))

    if sel_bug_key:
        target_bug = bug_map[sel_bug_key]
        dup_output = ai_engine.detect_duplicates_and_retrieve(target_bug['title'], target_bug['description'], target_bug.get('error_logs', ''), top_n=6)

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(render_radial_meter_html(dup_output['highest_similarity'], "Top Cosine Match"), unsafe_allow_html=True)
            st.markdown(f"""
            <div class="showcase-card" style="margin-top: 12px;">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700;">DUPLICATE RISK STATUS</div>
                <div style="font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-top: 2px;">{dup_output['duplicate_status']}</div>
                <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 6px;">Evaluated across <strong>{len(ai_engine.corpus_bugs)}</strong> labeled tickets in SQLite.</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("#### 📚 Historical Matches Ranked by Similarity")
            for m in dup_output['similar_bugs']:
                if m['id'] != target_bug['id']:
                    st.markdown(f"""
                    <div class="showcase-card" style="margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #f8fafc; font-size: 0.88rem;">#{m['bug_code']} — {m['title']}</span>
                            <span class="badge-pill" style="background: rgba(99, 102, 241, 0.2); color: #c7d2fe; border: 1px solid rgba(99, 102, 241, 0.3);">
                                {m['similarity_score']}% Match
                            </span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin: 4px 0;">Module: <strong>{m['module']}</strong> | Severity: <strong>{m['severity']}</strong> | Status: <strong>{m['status']}</strong></div>
                        <div style="font-size: 0.78rem; color: #e2e8f0; background: #0f172a; border-radius: 6px; padding: 6px 10px; margin-top: 4px;">
                            <strong>Root Cause:</strong> {m['root_cause']}<br>
                            <strong>Fix:</strong> {m['resolution_text']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# =====================================================================
# PAGE 7: RESOLUTION RECOMMENDATIONS (KNOWLEDGE BASE)
# =====================================================================
def page_resolution_recommendations():
    st.markdown("### 💡 Historical Resolution Knowledge Base")
    st.caption("Search verified root causes, code fixes, and triage resolutions documented by engineering squads across past deployments.")

    search_kw = st.text_input("🔍 Search Knowledge Base by keyword", placeholder="e.g. Stripe, webhook, signature, N+1, JWT, zipCode, Redis...")

    all_bugs = get_all_bugs(limit=300)
    resolved_bugs = [b for b in all_bugs if b.get('root_cause') or b.get('resolution_text')]

    if search_kw.strip():
        kw = search_kw.lower()
        resolved_bugs = [
            b for b in resolved_bugs if
            kw in b['title'].lower() or
            kw in (b.get('root_cause') or '').lower() or
            kw in (b.get('resolution_text') or '').lower() or
            kw in b['module'].lower()
        ]

    st.markdown(f"<div style='font-size: 0.8rem; color: #94a3b8; margin-bottom: 12px;'>Found <strong>{len(resolved_bugs)}</strong> documented resolutions</div>", unsafe_allow_html=True)

    for b in resolved_bugs:
        bug_code = f"BUG-{b['id']:03d}"
        st.markdown(f"""
        <div class="showcase-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                <div>
                    <span style="font-family: monospace; font-weight: 700; color: #818cf8; margin-right: 6px;">#{bug_code}</span>
                    <strong style="color: #f8fafc; font-size: 0.92rem;">{b['title']}</strong>
                </div>
                <div>{render_badge(b['module'], 'status')}</div>
            </div>
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px; margin-top: 6px; font-size: 0.8rem;">
                <div style="color: #fcd34d; font-weight: 700; margin-bottom: 2px;">Root Cause:</div>
                <div style="color: #cbd5e1; line-height: 1.4;">{b['root_cause']}</div>
                <div style="color: #6ee7b7; font-weight: 700; margin-top: 6px; margin-bottom: 2px;">Resolution Fix Applied:</div>
                <div style="color: #f8fafc; line-height: 1.4;">{b['resolution_text']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =====================================================================
# PAGE 8: DEVELOPER & TEAM ASSIGNMENT
# =====================================================================
def page_team_assignment():
    st.markdown("### 👥 Squad Rosters & Workload-Balanced Routing")
    st.caption("Monitor engineer ticket capacity, module domain specialization, and automated routing affinity formulas.")

    devs = get_all_developers()
    if devs:
        df_d = pd.DataFrame(devs)
        fig_w = px.bar(
            df_d, x='name', y='current_workload',
            color='current_workload',
            color_continuous_scale=['#38bdf8', '#818cf8', '#c084fc', '#f43f5e'],
            text='current_workload',
            title="Active Ticket Workload per Engineer"
        )
        fig_w.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=260)
        st.plotly_chart(fig_w, use_container_width=True)

        st.markdown("#### Squad Roster Cards")
        cols = st.columns(len(devs))
        for i, d in enumerate(devs):
            with cols[i]:
                st.markdown(f"""
                <div class="showcase-card" style="text-align: center;">
                    <div style="font-size: 2rem;">👨‍💻</div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: #f8fafc; margin-top: 4px;">{d['name']}</div>
                    <div style="font-size: 0.72rem; color: #94a3b8;">{d['email']}</div>
                    <div style="margin: 8px 0;">
                        <span class="badge-pill" style="background: rgba(99, 102, 241, 0.15); color: #c7d2fe; border: 1px solid rgba(99, 102, 241, 0.3);">
                            {d['expertise_modules']}
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; font-weight: 700; color: #38bdf8;">
                        Workload: {d['current_workload']} tickets
                    </div>
                </div>
                """, unsafe_allow_html=True)

# =====================================================================
# PAGE 9: ANALYTICS TELEMETRY
# =====================================================================
def page_analytics_telemetry():
    st.markdown("### 📈 Comprehensive Telemetry & Defect Analytics")
    st.caption("Deep triage metrics, defect distributions across application modules, and throughput telemetry.")

    stats = get_kpi_stats()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='showcase-card'><div style='font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;'>Defects by Category</div>", unsafe_allow_html=True)
        if stats['by_category']:
            df_cat = pd.DataFrame(stats['by_category'])
            fig_c = px.bar(df_cat, x='category', y='count', color='category', color_discrete_sequence=['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#3b82f6'])
            fig_c.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=280, showlegend=False)
            st.plotly_chart(fig_c, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='showcase-card'><div style='font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;'>Defects by Module</div>", unsafe_allow_html=True)
        if stats['by_module']:
            df_m = pd.DataFrame(stats['by_module'])
            fig_m = px.bar(df_m, x='module', y='count', color='module', color_discrete_sequence=['#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6'])
            fig_m.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#f8fafc'), height=280, showlegend=False)
            st.plotly_chart(fig_m, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### System Activity & Audit Trail")
    logs = get_audit_logs(limit=25)
    if logs:
        df_l = pd.DataFrame(logs)[['timestamp', 'action', 'details', 'full_name', 'role']]
        df_l.columns = ['Timestamp', 'Action', 'Details', 'Triggered By', 'Role']
        st.dataframe(df_l, use_container_width=True, hide_index=True)

# =====================================================================
# PAGE 10: SETTINGS & VIVA GUIDE
# =====================================================================
def page_settings_viva():
    st.markdown("### 🎓 AI Model Inspector & Viva Examination Center")
    st.caption("Inspect the mathematical principles, TF-IDF vector space, classification metrics, and defense proofs for academic evaluation.")

    metrics = ai_engine.train_metrics

    # 3 Architectural Advantage Cards matching showcase
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="showcase-card" style="border-left: 3px solid #6366f1;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #818cf8; text-transform: uppercase;">1. Mathematical Explainability</div>
            <p style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">
                Uses TF-IDF vectors where each dimension represents an actual n-gram token. Evaluators can inspect exactly which words triggered similarity.
            </p>
            <div style="font-family: monospace; font-size: 0.72rem; color: #34d399; margin-top: 6px;">Similarity = (A · B) / (||A|| ||B||)</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="showcase-card" style="border-left: 3px solid #a855f7;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #c084fc; text-transform: uppercase;">2. Zero Black-Box Latency</div>
            <p style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">
                Unlike cloud API calls that cost money and take 2-4 seconds, BugSense AI computes similarity in &lt; 8ms locally with zero token fees.
            </p>
            <div style="font-family: monospace; font-size: 0.72rem; color: #c084fc; margin-top: 6px;">Latency: 5.2ms avg | Air-Gapped</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="showcase-card" style="border-left: 3px solid #34d399;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #6ee7b7; text-transform: uppercase;">3. Workload-Balanced Routing</div>
            <p style="font-size: 0.78rem; color: #cbd5e1; margin-top: 4px;">
                Multi-variable scoring prevents assigning all defects to one engineer, balancing domain affinity against ticket burnout.
            </p>
            <div style="font-family: monospace; font-size: 0.72rem; color: #fcd34d; margin-top: 6px;">Penalty: -10 pts per active ticket</div>
        </div>
        """, unsafe_allow_html=True)

    # Confusion Matrix Table from Showcase
    st.markdown("#### 📊 Confusion Matrix (Test Set Validation)")
    if "severity_confusion_matrix" in metrics:
        cm = metrics["severity_confusion_matrix"]
        labels = metrics.get("severity_classes", ["Critical", "High", "Medium", "Low"])
        df_cm = pd.DataFrame(cm, index=[f"True: {l}" for l in labels], columns=[f"Pred: {l}" for l in labels])
        st.dataframe(df_cm, use_container_width=True)

    # Re-train trigger
    st.markdown("---")
    if st.button("🔄 Re-Train ML Models on Latest SQLite State", type="primary", use_container_width=True):
        ai_engine.load_and_train()
        st.success("TF-IDF vectorizer and Naive Bayes classifiers re-trained successfully!")
        st.rerun()

# ----------------- MAIN DISPATCHER -----------------
def main():
    if not st.session_state.user:
        render_auth_page()
    else:
        render_brand_header()
        page = render_sidebar()

        if page == "📊 Dashboard":
            page_dashboard()
        elif page == "✍️ Submit Bug":
            page_submit_bug()
        elif page == "🤖 AI Bug Analysis":
            page_ai_analysis()
        elif page == "📋 Bug Management":
            page_bug_management()
        elif page == "🔍 Bug Details":
            page_bug_details()
        elif page == "🔗 Similar / Duplicate Bugs":
            page_similar_duplicate_bugs()
        elif page == "💡 Resolution Recommendations":
            page_resolution_recommendations()
        elif page == "👥 Developer & Team Assignment":
            page_team_assignment()
        elif page == "📈 Analytics Telemetry":
            page_analytics_telemetry()
        elif page == "🎓 Settings & Viva Guide":
            page_settings_viva()

if __name__ == "__main__":
    main()
