# BugSense AI 🐞
### An AI-Powered Bug Management and Resolution Support System for Web Applications

BugSense AI is an intelligent, explainable bug tracking system that augments the standard software development issue-tracking workflow with machine learning and NLP.

---

## 🌟 Key Capabilities & Features

1. **Role-Based Authentication & Workflows**
   - **QA Testers**: File detailed bug reports with environment details, reproduction steps, expected/actual outputs, and stacktraces.
   - **Developers**: Inspect triage details, review AI similarity suggestions, update ticket statuses, add discussion comments, and record verified resolutions.
   - **Engineering Leads / Admins**: Monitor developer workload balancing, audit trails, and defect distribution analytics.

2. **Real-time Explainable AI Triage Assist**
   - **Duplicate Bug Detection**: Uses TF-IDF N-gram feature representation + Cosine Similarity against historical bugs to calculate a similarity percentage and flag duplicate risks before filing.
   - **Historical Resolution Retrieval**: Instantly surfaces past matching bugs with their verified root causes and resolution fixes to accelerate troubleshooting.
   - **Severity & Defect Category Classification**: Hybrid pipeline combining statistical Multinomial Naive Bayes classifiers with transparent keyword heuristics for safety-critical cues (e.g. data loss, double charges, SQL injection, credential leaks).
   - **Intelligent Team & Engineer Routing**: Scores engineers based on module expertise alignment, active ticket balancing, and domain proficiency.

3. **Analytics Dashboard**
   - Live KPI metrics (Total Bugs, Untriaged, In Progress, Resolved, Critical defects).
   - Interactive Plotly visualizations for Module Distribution, Severity Breakdown, Defect Categories, and the Bug Lifecycle Pipeline.
   - Chronological audit logging of all system actions.

4. **Academic & Viva Evaluation Center**
   - Built-in evaluation dashboard displaying train-test split accuracy, confusion matrices, TF-IDF vocabulary size, and mathematical explanations of all formulas for viva defense.

---

## 🏗️ Architecture & Technology Stack

- **Frontend & UI**: Streamlit with custom CSS and Plotly interactive data visualizations
- **Backend**: Python 3
- **Database**: SQLite with foreign key constraints, indexes, and audit logging
- **Machine Learning & NLP**: `scikit-learn` (TF-IDF Vectorizer, Cosine Similarity, Multinomial Naive Bayes)
- **Data Layer**: Pandas, NumPy
- **Security**: PBKDF2-HMAC-SHA256 salted password hashing

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
cd "C:\Users\Indhu sri\.gemini\antigravity\scratch\bugsense-ai"
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
streamlit run app.py
```

The application will open automatically in your browser (default: `http://localhost:8501`).

---

## 🔐 Default Demo Accounts

The database comes pre-seeded with test accounts and 50+ curated e-commerce bugs across Cart, Checkout, Payment, Auth, Orders, Catalog, and Profile modules:

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **QA Tester** | `tester1` | `password123` | Report bugs & view QA telemetry |
| **Senior Dev** | `dev1` | `password123` | Triage, solve tickets, view assignments |
| **Team Lead** | `lead1` | `password123` | Assign developers, review workload & logs |
| **Admin** | `admin` | `admin123` | Full administrative oversight |

*(Note: You can also use the **"⚡ Quick Demo Access"** buttons on the login screen to sign in with one click).*

---

## 🎓 Viva & Project Presentation Highlights

When demonstrating to evaluators:

1. **Demonstrate Explainability**:
   - Go to **Report a Bug (AI Assist)** and pick **"Scenario A: Duplicate Bug"**.
   - Show how the system flags a **high duplicate score (~85-90%)** and displays the exact past bug with its **Root Cause** and **Resolution Applied**.
   - Explain that TF-IDF + Cosine Similarity provides mathematical transparency (evaluators can inspect vocabulary and token weights) unlike opaque third-party black boxes.

2. **Demonstrate Automated Routing**:
   - Notice how Payment bugs are automatically scored and routed to **Alex Chen (Payment/Checkout squad)** while balancing against active workload.

3. **Demonstrate the Evaluation Suite**:
   - Navigate to **"AI Model & Viva Evaluation Center"** to review the confusion matrices, classification metrics, and dataset distributions.
