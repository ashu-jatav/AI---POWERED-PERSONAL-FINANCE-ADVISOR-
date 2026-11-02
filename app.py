import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from advisor import generate_insights, load_model, predict_expense
from utils import (
    init_db, register_user, login_user, get_user_by_id,
    get_user_transactions, add_transaction, update_transaction,
    delete_transaction, assign_sample_data, update_user_settings,
    validate_transaction, get_last_transaction_date, get_missing_days, get_streak
)

# =========================
# TRANSLATIONS
# =========================
LANG = {
    "en": {
        "login": "Login",
        "register": "Register",
        "full_name": "Full Name",
        "email": "Email",
        "password": "Password",
        "no_account": "Don't have an account?",
        "go_register": "Go to Register",
        "have_account": "Already have an account?",
        "go_login": "Go to Login",
        "reg_success": "Registration successful! Sample data added.",
        "welcome": "Welcome",
        "dashboard": "Dashboard",
        "transactions": "Transactions",
        "analytics": "Analytics",
        "ai_insights": "AI Insights",
        "alerts": "Alerts",
        "settings": "Settings",
        "logout": "Logout",
        "reminder": "Reminder: Don't forget to log today's transactions to keep your finances on track!",
        "balance": "Balance",
        "income": "Income",
        "expense": "Expense",
        "savings": "Savings",
        "expense_by_category": "Expense by Category",
        "monthly_trend": "Monthly Trend",
        "category_breakdown": "Category Breakdown (Bar)",
        "no_expense_data": "No expense data yet. Add transactions to see charts.",
        "recent_transactions": "Recent Transactions",
        "ai_prediction": "AI Expense Prediction",
        "predicted_next": "Predicted Next Month Expense",
        "confidence": "Confidence",
        "view_breakdown": "View Breakdown",
        "more_expenses_needed": "Add more expense transactions for AI prediction.",
        "model_not_loaded": "AI model not loaded. Run train.py first.",
        "edit_transaction": "Edit Transaction",
        "add_transaction": "Add Transaction",
        "date": "Date",
        "description": "Description",
        "category": "Category",
        "amount": "Amount",
        "type": "Type",
        "location": "Location",
        "update": "Update",
        "save": "Save",
        "cancel_edit": "Cancel Edit",
        "your_transactions": "Your Transactions",
        "no_transactions": "No transactions yet.",
        "no_data_analytics": "No data to analyze. Add transactions first.",
        "income_vs_expense": "Income vs Expense",
        "daily_spending": "Daily Spending Pattern",
        "cumulative_balance": "Cumulative Balance Over Time",
        "financial_health": "Financial Health Insights",
        "ai_forecast": "AI Expense Forecast",
        "predicted_expense": "Predicted Expense",
        "your_avg_expense": "Your Avg Expense",
        "category_wise_prediction": "Category-wise Prediction",
        "model_not_available": "AI model not available. Run train.py to generate model.pkl",
        "appearance": "Appearance",
        "dark_mode": "Dark Mode",
        "notifications": "Notifications",
        "enable_notifications": "Enable Notifications",
        "account_info": "Account Info",
        "name": "Name",
        "language": "Language",
        "english": "English",
        "hindi": "Hindi",
        "alerts_reminders": "Alerts & Reminders",
        "notif_off": "Notifications are turned off. Enable them in Settings to see alerts.",
        "current_streak": "Current Streak",
        "streak_days": "You have logged transactions for **{} consecutive day(s)**! Keep it up!",
        "no_streak": "No streak yet. Start logging today!",
        "missing_days": "Missing Transaction Days",
        "great_job": "Great job! You've logged transactions for all recent days.",
        "today_missing": "Today ({}) — No transaction logged yet!",
        "days_ago_missing": "{} day(s) ago — Missing",
        "last_transaction": "Last Transaction Info",
        "last_tx_on": "Your last transaction was on **{}**.",
        "no_transactions_found": "No transactions found. Add your first transaction now!",
        "add_tx_now": "Add Transaction Now",
    },
    "hi": {
        "login": "लॉग इन",
        "register": "पंजीकरण",
        "full_name": "पूरा नाम",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "no_account": "खाता नहीं है?",
        "go_register": "पंजीकरण करें",
        "have_account": "पहले से खाता है?",
        "go_login": "लॉग इन करें",
        "reg_success": "पंजीकरण सफल! नमूना डेटा जोड़ा गया।",
        "welcome": "स्वागत है",
        "dashboard": "डैशबोर्ड",
        "transactions": "लेनदेन",
        "analytics": "विश्लेषण",
        "ai_insights": "AI अंतर्दृष्टि",
        "alerts": "अलर्ट",
        "settings": "सेटिंग्स",
        "logout": "लॉग आउट",
        "reminder": "🔔 अनुस्मारक: अपने वित्त को ट्रैक पर रखने के लिए आज के लेनदेन लॉग करना न भूलें!",
        "balance": "बैलेंस",
        "income": "आय",
        "expense": "खर्च",
        "savings": "बचत",
        "expense_by_category": "श्रेणी के अनुसार खर्च",
        "monthly_trend": "मासिक रुझान",
        "category_breakdown": "श्रेणी विश्लेषण (बार)",
        "no_expense_data": "अभी तक कोई खर्च डेटा नहीं। चार्ट देखने के लिए लेनदेन जोड़ें।",
        "recent_transactions": "हाल के लेनदेन",
        "ai_prediction": "AI खर्च भविष्यवाणी",
        "predicted_next": "अगले महीने का अनुमानित खर्च",
        "confidence": "विश्वास",
        "view_breakdown": "विश्लेषण देखें",
        "more_expenses_needed": "AI भविष्यवाणी के लिए और खर्च लेनदेन जोड़ें।",
        "model_not_loaded": "AI मॉडल लोड नहीं हुआ। पहले train.py चलाएं।",
        "edit_transaction": "लेनदेन संपादित करें",
        "add_transaction": "लेनदेन जोड़ें",
        "date": "तारीख",
        "description": "विवरण",
        "category": "श्रेणी",
        "amount": "राशि",
        "type": "प्रकार",
        "location": "स्थान",
        "update": "अपडेट",
        "save": "सहेजें",
        "cancel_edit": "संपादन रद्द करें",
        "your_transactions": "आपके लेनदेन",
        "no_transactions": "अभी तक कोई लेनदेन नहीं।",
        "no_data_analytics": "विश्लेषण के लिए कोई डेटा नहीं। पहले लेनदेन जोड़ें।",
        "income_vs_expense": "आय बनाम खर्च",
        "daily_spending": "दैनिक खर्च पैटर्न",
        "cumulative_balance": "समय के साथ संचयी बैलेंस",
        "financial_health": "वित्तीय स्वास्थ्य अंतर्दृष्टि",
        "ai_forecast": "AI खर्च पूर्वानुमान",
        "predicted_expense": "अनुमानित खर्च",
        "your_avg_expense": "आपका औसत खर्च",
        "category_wise_prediction": "श्रेणी-वार भविष्यवाणी",
        "model_not_available": "AI मॉडल उपलब्ध नहीं। model.pkl बनाने के लिए train.py चलाएं",
        "appearance": "उपस्थिति",
        "dark_mode": "डार्क मोड",
        "notifications": "सूचनाएं",
        "enable_notifications": "सूचनाएं सक्षम करें",
        "account_info": "खाता जानकारी",
        "name": "नाम",
        "language": "भाषा",
        "english": "अंग्रेजी",
        "hindi": "हिंदी",
        "alerts_reminders": "अलर्ट और अनुस्मारक",
        "notif_off": "सूचनाएं बंद हैं। अलर्ट देखने के लिए उन्हें सेटिंग्स में सक्षम करें।",
        "current_streak": "वर्तमान स्ट्रीक",
        "streak_days": "आपने **{} लगातार दिनों** के लिए लेनदेन लॉग किए हैं! इसे जारी रखें!",
        "no_streak": "अभी तक कोई स्ट्रीक नहीं। आज से शुरुआत करें!",
        "missing_days": "लेनदेन के गायब दिन",
        "great_job": "बहुत बढ़िया! आपने हाल के सभी दिनों के लिए लेनदेन लॉग किए हैं।",
        "today_missing": "🚨 आज ({}) — अभी तक कोई लेनदेन लॉग नहीं हुआ!",
        "days_ago_missing": "⚠️ {} — {} दिन पहले — गायब",
        "last_transaction": "अंतिम लेनदेन जानकारी",
        "last_tx_on": "आपका अंतिम लेनदेन **{}** को था।",
        "no_transactions_found": "कोई लेनदेन नहीं मिला। अपना पहला लेनदेन अभी जोड़ें!",
        "add_tx_now": "अभी लेनदेन जोड़ें",
    }
}


def t(key: str) -> str:
    """Return translated text for the current session language."""
    lang = st.session_state.get("language", "en")
    return LANG.get(lang, LANG["en"]).get(key, key)


st.set_page_config(page_title="AI Finance Pro", layout="wide", initial_sidebar_state="expanded")

# =========================
# INIT DB
# =========================
init_db()

# =========================
# SESSION STATE
# =========================
def ensure_session():
    defaults = {
        "authenticated": False,
        "user_id": 0,
        "user_name": "",
        "user_email": "",
        "dark_mode": False,
        "notifications": True,
        "language": "en",
        "page": "Dashboard",
        "edit_tx_id": None,
        "edit_tx_data": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

ensure_session()

# =========================
# LOAD MODEL
# =========================
model, le_cat, le_loc = load_model()

# =========================
# STYLES
# =========================
def apply_styles():
    is_dark = st.session_state.dark_mode
    bg = "#0f172a" if is_dark else "#f8fafc"
    card_bg = "rgba(255,255,255,0.05)" if is_dark else "rgba(0,0,0,0.03)"
    text_color = "#ffffff" if is_dark else "#1e293b"
    sidebar_bg = "#020617" if is_dark else "#ffffff"
    metric_bg = "linear-gradient(135deg,#1e293b,#0f172a)" if is_dark else "linear-gradient(135deg,#e2e8f0,#f1f5f9)"
    
    st.markdown(f"""
    <style>
    .main {{ background: {bg}; color: {text_color}; }}
    [data-testid="stSidebar"] {{ background: {sidebar_bg}; }}
    .stButton>button {{
        background: linear-gradient(90deg,#7c3aed,#06b6d4);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(124,58,237,0.4);
    }}
    .card {{
        background: {card_bg};
        padding: 20px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.05)'};
        margin-bottom: 1rem;
    }}
    .metric-card {{
        background: {metric_bg};
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid {'rgba(255,255,255,0.1)' if is_dark else 'rgba(0,0,0,0.05)'};
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {'#ffffff' if is_dark else '#0f172a'};
    }}
    .metric-label {{
        font-size: 0.9rem;
        color: {'#94a3b8' if is_dark else '#64748b'};
        margin-top: 5px;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
    }}
    .stDataFrame {{
        background: transparent !important;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# =========================
# AUTH PAGES
# =========================
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>🔐 Login</h2>", unsafe_allow_html=True)
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button(t("login")):
            success, msg, user = login_user(email, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["name"]
                st.session_state.user_email = user["email"]
                st.session_state.dark_mode = bool(user.get("dark_mode", 0))
                st.session_state.notifications = bool(user.get("notifications", 1))
                st.session_state.language = user.get("language", "en")
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='card' style='text-align:center;'>{t('no_account')}</div>", unsafe_allow_html=True)
        if st.button(t("go_register")): 
            st.session_state.page = "Register"
            st.rerun()

def register_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center;'>📝 {t('register')}</h2>", unsafe_allow_html=True)
        
        name = st.text_input(t("full_name"), key="reg_name")
        email = st.text_input(t("email"), key="reg_email")
        password = st.text_input(t("password"), type="password", key="reg_password")
        
        if st.button(t("register")):
            success, msg, user_id = register_user(name, email, password, language=st.session_state.get("language", "en"))
            if success:
                assign_sample_data(user_id, count=8)
                # Auto login
                success2, msg2, user = login_user(email, password)
                if success2:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_email = user["email"]
                    st.session_state.dark_mode = bool(user.get("dark_mode", 0))
                    st.session_state.notifications = bool(user.get("notifications", 1))
                    st.session_state.language = user.get("language", "en")
                    st.success(t("reg_success"))
                    st.rerun()
            else:
                st.error(msg)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='card' style='text-align:center;'>{t('have_account')}</div>", unsafe_allow_html=True)
        if st.button(t("go_login")):

            st.session_state.page = "Login"
            st.rerun()

# =========================
# SIDEBAR NAV
# =========================
def sidebar_nav():
    with st.sidebar:
        st.markdown(f"""
        <div style='padding: 1rem 0; text-align: center;'>
            <h3>🚀 AI Finance Pro</h3>
            <p style='color: #94a3b8; font-size: 0.85rem;'>{t('welcome')}, <b>{st.session_state.user_name}</b></p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        menu_items = [
            (t("dashboard"), "📊"),
            (t("transactions"), "💸"),
            (t("analytics"), "📈"),
            (t("ai_insights"), "🤖"),
            (t("alerts"), "🔔"),
            (t("settings"), "⚙️"),
        ]

        for item, icon in menu_items:
            if st.button(f"{icon} {item}", key=f"nav_{item}"):
                st.session_state.page = item
                st.rerun()

        st.divider()

        if st.button(f"🚪 {t('logout')}"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# =========================
# DASHBOARD
# =========================
def dashboard_page():
    st.title(f"👋 {t('welcome')}, {st.session_state.user_name}")
    
    # Notification banner for missing today's transaction
    if st.session_state.notifications:
        last_tx = get_last_transaction_date(st.session_state.user_id)
        today = datetime.now().date()
        if last_tx is None or last_tx.date() < today:
            st.markdown(f"""
            <div style='background: linear-gradient(90deg,#ef4444,#f97316); padding: 12px 20px; border-radius: 10px; margin-bottom: 1rem; color: white; font-weight: 600;'>
                🔔 {t('reminder')}
            </div>
            """, unsafe_allow_html=True)
    
    df = get_user_transactions(st.session_state.user_id)
    
    # Metrics
    income = df[df["type"].str.lower() == "income"]["amount"].sum()
    expense = df[df["type"].str.lower() == "expense"]["amount"].sum()
    balance = income - expense
    savings = balance if balance > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, f"💰 {t('balance')}", balance, "#7c3aed"),
        (c2, f"📈 {t('income')}", income, "#10b981"),
        (c3, f"📉 {t('expense')}", expense, "#ef4444"),
        (c4, f"💾 {t('savings')}", savings, "#06b6d4"),
    ]
    
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value' style='color: {color};'>₹ {value:,.0f}</div>
                <div class='metric-label'>{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    exp_df = df[df["type"].str.lower() == "expense"]
    
    if not exp_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader(f"📊 {t('expense_by_category')}")
            pie = px.pie(exp_df, names="category", values="amount", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Plasma)
            pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="white" if st.session_state.dark_mode else "#1e293b",
                              margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(pie, width="stretch", key="pie_chart")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader(f"📈 {t('monthly_trend')}")
            chart_df = df.copy()
            chart_df["date"] = pd.to_datetime(chart_df["date"], errors="coerce")
            chart_df["month"] = chart_df["date"].dt.to_period("M").astype(str)
            monthly = chart_df.groupby(["month", "type"])["amount"].sum().reset_index()
            line = px.line(monthly, x="month", y="amount", color="type",
                           color_discrete_map={"Income": "#10b981", "Expense": "#ef4444"},
                           markers=True)
            line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="white" if st.session_state.dark_mode else "#1e293b",
                               margin=dict(t=30, b=30, l=30, r=30))
            st.plotly_chart(line, width="stretch", key="line_chart")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Bar chart
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader(f"📊 {t('category_breakdown')}")
        bar = px.bar(exp_df.groupby("category")["amount"].sum().reset_index(),
                     x="category", y="amount", color="category",
                     color_discrete_sequence=px.colors.sequential.Viridis)
        bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white" if st.session_state.dark_mode else "#1e293b",
                          margin=dict(t=30, b=30, l=30, r=30), showlegend=False)
        st.plotly_chart(bar, width="stretch", key="bar_chart")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(t("no_expense_data"))
    
    # Recent transactions
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"📋 {t('recent_transactions')}")
    st.dataframe(df.head(10).drop(columns=["id"]), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # AI Prediction card
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"🤖 {t('ai_prediction')}")
    if model is not None:
        pred = predict_expense(df, model, le_cat, le_loc)
        if pred["prediction"] > 0:
            st.metric(t("predicted_next"), f"₹ {pred['prediction']:,.0f}")
            st.caption(f"{t('confidence')}: {pred['confidence'].upper()}")
            if pred["breakdown"]:
                with st.expander(t("view_breakdown")):
                    for cat, val in pred["breakdown"].items():
                        st.write(f"- {cat}: ₹{val:,.0f}")
        else:
            st.info(t("more_expenses_needed"))
    else:
        st.warning(t("model_not_loaded"))
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# TRANSACTIONS
# =========================
def transactions_page():
    st.title(f"💸 {t('transactions')}")
    
    df = get_user_transactions(st.session_state.user_id)
    
    # Add / Edit form
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    is_edit = st.session_state.edit_tx_id is not None
    st.subheader(f"✏️ {t('edit_transaction')}" if is_edit else f"➕ {t('add_transaction')}")
    
    with st.form("tx_form"):
        default_date = datetime.now().date()
        default_desc = ""
        default_cat = ""
        default_amt = 0.0
        default_type = "Expense"
        default_loc = ""
        
        if is_edit and st.session_state.edit_tx_data:
            d = st.session_state.edit_tx_data
            try:
                parsed = pd.to_datetime(d["date"], errors="coerce")
                if pd.isna(parsed):
                    default_date = datetime.now().date()
                else:
                    default_date = parsed.date()
            except Exception:
                default_date = datetime.now().date()
            default_desc = d.get("description", "")
            default_cat = d.get("category", "")
            default_amt = float(d.get("amount", 0))
            default_type = d.get("type", "Expense")
            default_loc = d.get("location", "")
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input(t("date"), value=default_date)
            desc = st.text_input(t("description"), value=default_desc)
            cat = st.text_input(t("category"), value=default_cat)
        with col2:
            amt = st.number_input(t("amount"), min_value=0.0, value=default_amt, step=10.0)
            tx_type = st.selectbox(t("type"), ["Income", "Expense"], index=0 if default_type == "Income" else 1)
            loc = st.text_input(t("location"), value=default_loc)
        
        submitted = st.form_submit_button(t("update") if is_edit else t("save"))
        
        if submitted:
            valid, msg = validate_transaction(date, desc, cat, amt, tx_type)
            if not valid:
                st.error(msg)
            else:
                if is_edit:
                    success, msg = update_transaction(st.session_state.edit_tx_id, st.session_state.user_id,
                                                      date, desc, cat, amt, tx_type, loc)
                    if success:
                        st.session_state.edit_tx_id = None
                        st.session_state.edit_tx_data = None
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    success, msg = add_transaction(st.session_state.user_id, date, desc, cat, amt, tx_type, loc)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    if is_edit:
        if st.button(t("cancel_edit")):
            st.session_state.edit_tx_id = None
            st.session_state.edit_tx_data = None
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Transaction list
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader(f"📋 {t('your_transactions')}")
    
    if df.empty:
        st.info(t("no_transactions"))
    else:
        for _, row in df.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    date_str = str(row['date'])[:10] if pd.notna(row['date']) else ''
                    st.write(f"**{row['description']}** | {row['category']} | {date_str}")
                with c2:
                    color = "#10b981" if str(row['type']).lower() == "income" else "#ef4444"
                    st.markdown(f"<span style='color:{color};font-weight:700;'>₹ {row['amount']:,.0f}</span>", unsafe_allow_html=True)
                with c3:
                    if st.button(t("update"), key=f"edit_{row['id']}"):
                        st.session_state.edit_tx_id = row["id"]
                        st.session_state.edit_tx_data = row.to_dict()
                        st.rerun()
                with c4:
                    if st.button("Delete", key=f"del_{row['id']}"):
                        success, msg = delete_transaction(row["id"], st.session_state.user_id)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                st.divider()
    
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# ANALYTICS
# =========================
def analytics_page():
    st.title("📈 Analytics")
    
    df = get_user_transactions(st.session_state.user_id)
    
    if df.empty:
        st.info("No data to analyze. Add transactions first.")
        return
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📊 Income vs Expense")
        summary = df.groupby("type")["amount"].sum().reset_index()
        fig = go.Figure(data=[
            go.Bar(name="Amount", x=summary["type"], y=summary["amount"],
                   marker_color=["#10b981", "#ef4444"])
        ])
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white" if st.session_state.dark_mode else "#1e293b")
        st.plotly_chart(fig, width="stretch", key="analytics_bar")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📅 Daily Spending Pattern")
        df["day_name"] = df["date"].dt.day_name()
        daily = df[df["type"].str.lower() == "expense"].groupby("day_name")["amount"].sum().reindex(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ).fillna(0)
        fig2 = px.bar(x=daily.index, y=daily.values, labels={"x": "Day", "y": "Amount"},
                      color=daily.values, color_continuous_scale="Plasma")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white" if st.session_state.dark_mode else "#1e293b",
                           showlegend=False)
        st.plotly_chart(fig2, width="stretch", key="daily_bar")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📈 Cumulative Balance Over Time")
    df_sorted = df.sort_values("date")
    df_sorted["net"] = df_sorted.apply(lambda x: x["amount"] if str(x["type"]).lower() == "income" else -x["amount"], axis=1)
    df_sorted["cumulative"] = df_sorted["net"].cumsum()
    fig3 = px.area(df_sorted, x="date", y="cumulative",
                   color_discrete_sequence=["#7c3aed"])
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font_color="white" if st.session_state.dark_mode else "#1e293b")
    st.plotly_chart(fig3, width="stretch", key="cum_chart")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# AI INSIGHTS
# =========================
def ai_insights_page():
    st.title("🤖 AI Insights")
    
    df = get_user_transactions(st.session_state.user_id)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🧠 Financial Health Insights")
    insights = generate_insights(df, model, le_cat, le_loc)
    for insight in insights:
        st.markdown(f"<p style='padding: 8px 0; border-bottom: 1px solid {'rgba(255,255,255,0.1)' if st.session_state.dark_mode else 'rgba(0,0,0,0.05)'};'>{insight}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if model is not None:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔮 AI Expense Forecast")
        pred = predict_expense(df, model, le_cat, le_loc)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Predicted Expense", f"₹ {pred['prediction']:,.0f}")
        with c2:
            st.metric("Confidence", pred['confidence'].upper())
        with c3:
            expense_df = df[df["type"].str.lower() == "expense"]
            avg_exp = expense_df["amount"].mean() if not expense_df.empty else 0
            st.metric("Your Avg Expense", f"₹ {avg_exp:,.0f}")
        
        if pred["breakdown"]:
            st.markdown("#### Category-wise Prediction")
            breakdown_df = pd.DataFrame([{"Category": k, "Predicted": v} for k, v in pred["breakdown"].items()])
            fig = px.bar(breakdown_df, x="Category", y="Predicted", color="Category",
                         color_discrete_sequence=px.colors.sequential.Plasma)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="white" if st.session_state.dark_mode else "#1e293b",
                              showlegend=False)
            st.plotly_chart(fig, width="stretch", key="pred_bar")
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("AI model not available. Run train.py to generate model.pkl")

# =========================
# SETTINGS
# =========================
def settings_page():
    st.title("⚙️ Settings")
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🎨 Appearance")
    
    dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        update_user_settings(st.session_state.user_id, dark_mode=int(dark_mode))
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔔 Notifications")
    
    notifications = st.toggle("Enable Notifications", value=st.session_state.notifications)
    if notifications != st.session_state.notifications:
        st.session_state.notifications = notifications
        update_user_settings(st.session_state.user_id, notifications=int(notifications))
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("👤 Account Info")
    st.write(f"**Name:** {st.session_state.user_name}")
    st.write(f"**Email:** {st.session_state.user_email}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# ALERTS
# =========================
def alerts_page():
    st.title("🔔 Alerts & Reminders")
    
    if not st.session_state.notifications:
        st.info("Notifications are turned off. Enable them in Settings to see alerts.")
        return
    
    user_id = st.session_state.user_id
    
    # Streak card
    streak = get_streak(user_id)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🔥 Current Streak")
    if streak > 0:
        st.success(f"You have logged transactions for **{streak} consecutive day(s)**! Keep it up! 🎉")
    else:
        st.warning("No streak yet. Start logging today!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Missing days
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📅 Missing Transaction Days")
    missing = get_missing_days(user_id, days=7)
    today = datetime.now().date()
    
    if not missing or (len(missing) == 1 and missing[0] == today):
        st.success("Great job! You've logged transactions for all recent days. 🌟")
    else:
        for d in missing:
            if d == today:
                st.error(f"🚨 **Today ({d.strftime('%d %b, %Y')})** — No transaction logged yet!")
            else:
                days_ago = (today - d).days
                st.warning(f"⚠️ **{d.strftime('%d %b, %Y')}** — {days_ago} day(s) ago — Missing")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Last transaction
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🕐 Last Transaction Info")
    last_tx = get_last_transaction_date(user_id)
    if last_tx:
        st.info(f"Your last transaction was on **{last_tx.strftime('%d %B %Y')}**.")
    else:
        st.warning("No transactions found. Add your first transaction now!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quick add button
    if st.button("➕ Add Transaction Now"):
        st.session_state.page = "Transactions"
        st.rerun()

# =========================
# MAIN ROUTER
# =========================
if not st.session_state.authenticated:
    if st.session_state.page == "Register":
        register_page()
    else:
        login_page()
else:
    sidebar_nav()
    
    if st.session_state.page == "Dashboard":
        dashboard_page()
    elif st.session_state.page == "Transactions":
        transactions_page()
    elif st.session_state.page == "Analytics":
        analytics_page()
    elif st.session_state.page == "AI Insights":
        ai_insights_page()
    elif st.session_state.page == "Alerts":
        alerts_page()
    elif st.session_state.page == "Settings":
        settings_page()
    else:
        dashboard_page()

