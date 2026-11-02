import sqlite3
import bcrypt
import pandas as pd
import random
from datetime import datetime, timedelta

DB_PATH = "finance_advisor.db"
DATASET_PATH = "DATASET/dataset1.csv"


def _normalize_date(date_val) -> str:
    """Convert any date input to YYYY-MM-DD string for consistent SQLite storage."""
    if date_val is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.strftime("%Y-%m-%d")
    if hasattr(date_val, "year") and hasattr(date_val, "month") and hasattr(date_val, "day"):
        # datetime.date object
        return f"{date_val.year:04d}-{date_val.month:02d}-{date_val.day:02d}"
    s = str(date_val).strip()
    if not s:
        return datetime.now().strftime("%Y-%m-%d")
    # Try parsing common formats
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback to pandas parser
    try:
        parsed = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass
    return s  # return as-is if nothing works

def _db_date_to_iso(date_str: str) -> str:
    """Convert a date string from DB (could be DD-MM-YYYY or YYYY-MM-DD) to ISO YYYY-MM-DD."""
    if not date_str:
        return date_str
    s = str(date_str).strip()
    # Already ISO format
    if len(s) == 10 and s[4] == '-' and s[7] == '-':
        return s
    # Try DD-MM-YYYY
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback: let pandas try with dayfirst (handles ambiguous old data)
    try:
        parsed = pd.to_datetime(s, dayfirst=True, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%Y-%m-%d")
    except Exception:
        pass
    return s

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            dark_mode INTEGER DEFAULT 0,
            notifications INTEGER DEFAULT 1,
            language TEXT DEFAULT 'en',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            location TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Migrate: add language column if missing
    try:
        c.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]

def validate_registration(name: str, email: str, password: str) -> tuple[bool, str]:
    if not name or not name.strip():
        return False, "Name is required."
    if not email or not email.strip():
        return False, "Email is required."
    if not validate_email(email):
        return False, "Invalid email format."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""

def validate_transaction(date, description, category, amount, tx_type) -> tuple[bool, str]:
    if not date:
        return False, "Date is required."
    if not description or not str(description).strip():
        return False, "Description is required."
    if not category or not str(category).strip():
        return False, "Category is required."
    try:
        amt = float(amount)
        if amt <= 0:
            return False, "Amount must be greater than 0."
    except (ValueError, TypeError):
        return False, "Amount must be a valid number greater than 0."
    if not tx_type or tx_type not in ["Income", "Expense"]:
        return False, "Type must be Income or Expense."
    return True, ""

def register_user(name: str, email: str, password: str, language: str = "en") -> tuple[bool, str, int]:
    try:
        valid, msg = validate_registration(name, email, password)
        if not valid:
            return False, msg, 0
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email.strip(),))
        if c.fetchone():
            conn.close()
            return False, "Email already registered.", 0
        
        pw_hash = hash_password(password)
        c.execute(
            "INSERT INTO users (name, email, password_hash, language) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), pw_hash, language)
        )
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return True, "Registration successful.", user_id
    except Exception as e:
        return False, f"Registration error: {str(e)}", 0

def login_user(email: str, password: str) -> tuple[bool, str, dict]:
    try:
        if not email or not password:
            return False, "Email and password are required.", {}
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return False, "Invalid email or password.", {}
        
        user = dict(row)
        if not check_password(password, user["password_hash"]):
            return False, "Invalid email or password.", {}
        
        return True, "Login successful.", user
    except Exception as e:
        return False, f"Login error: {str(e)}", {}

def get_user_by_id(user_id: int) -> dict:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_user_settings(user_id: int, dark_mode: int = None, notifications: int = None, language: str = None):
    conn = get_db_connection()
    c = conn.cursor()
    if dark_mode is not None:
        c.execute("UPDATE users SET dark_mode = ? WHERE id = ?", (dark_mode, user_id))
    if notifications is not None:
        c.execute("UPDATE users SET notifications = ? WHERE id = ?", (notifications, user_id))
    if language is not None:
        c.execute("UPDATE users SET language = ? WHERE id = ?", (language, user_id))
    conn.commit()
    conn.close()

def get_user_transactions(user_id: int) -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT id, date, description, category, amount, type, location FROM transactions WHERE user_id = ? ORDER BY date DESC",
        conn, params=(user_id,)
    )
    conn.close()
    if df.empty:
        df = pd.DataFrame(columns=["id", "date", "description", "category", "amount", "type", "location"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["date"] = df["date"].apply(_db_date_to_iso)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

def add_transaction(user_id: int, date, description, category, amount, tx_type, location="") -> tuple[bool, str]:
    valid, msg = validate_transaction(date, description, category, amount, tx_type)
    if not valid:
        return False, msg
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO transactions (user_id, date, description, category, amount, type, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, _normalize_date(date), str(description).strip(), str(category).strip(), float(amount), str(tx_type).strip(), str(location).strip() if location else "")
        )
        conn.commit()
        conn.close()
        return True, "Transaction added successfully."
    except Exception as e:
        return False, f"Error adding transaction: {str(e)}"

def update_transaction(tx_id: int, user_id: int, date, description, category, amount, tx_type, location="") -> tuple[bool, str]:
    valid, msg = validate_transaction(date, description, category, amount, tx_type)
    if not valid:
        return False, msg
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "UPDATE transactions SET date=?, description=?, category=?, amount=?, type=?, location=? WHERE id=? AND user_id=?",
            (_normalize_date(date), str(description).strip(), str(category).strip(), float(amount), str(tx_type).strip(), str(location).strip() if location else "", tx_id, user_id)
        )
        conn.commit()
        conn.close()
        return True, "Transaction updated successfully."
    except Exception as e:
        return False, f"Error updating transaction: {str(e)}"

def delete_transaction(tx_id: int, user_id: int) -> tuple[bool, str]:
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
        conn.commit()
        conn.close()
        return True, "Transaction deleted successfully."
    except Exception as e:
        return False, f"Error deleting transaction: {str(e)}"

def get_last_transaction_date(user_id: int) -> datetime:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT date FROM transactions WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    parsed_dates = []
    for r in rows:
        if r["date"]:
            iso_date = _db_date_to_iso(r["date"])
            d = pd.to_datetime(iso_date, errors="coerce")
            if pd.notna(d):
                parsed_dates.append(d)
    if not parsed_dates:
        return None
    return max(parsed_dates)

def get_transaction_dates(user_id: int, days: int = 7) -> set:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT date FROM transactions WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    since = datetime.now().date() - timedelta(days=days)
    dates = set()
    for r in rows:
        if r["date"]:
            iso_date = _db_date_to_iso(r["date"])
            d = pd.to_datetime(iso_date, errors="coerce")
            if pd.notna(d) and d.date() >= since:
                dates.add(d.date())
    return dates

def get_missing_days(user_id: int, days: int = 7) -> list:
    tx_dates = get_transaction_dates(user_id, days)
    today = datetime.now().date()
    missing = []
    for i in range(days):
        d = today - timedelta(days=i)
        if d not in tx_dates:
            missing.append(d)
    return sorted(missing, reverse=True)

def get_streak(user_id: int) -> int:
    tx_dates = get_transaction_dates(user_id, 365)
    today = datetime.now().date()
    streak = 0
    for i in range(365):
        d = today - timedelta(days=i)
        if d in tx_dates:
            streak += 1
        else:
            break
    return streak

def assign_sample_data(user_id: int, count: int = 8):
    try:
        df = pd.read_csv(DATASET_PATH)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=["Date", "Category", "Amount", "Type"])
        df = df.sample(n=min(count, len(df)), random_state=random.randint(1, 10000))
        
        conn = get_db_connection()
        c = conn.cursor()
        for _, row in df.iterrows():
            c.execute(
                "INSERT INTO transactions (user_id, date, description, category, amount, type, location) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, _normalize_date(row["Date"]), str(row.get("Transaction Description", row.get("Description", ""))), 
                 str(row["Category"]), float(row["Amount"]), str(row["Type"]), str(row.get("Location", "")))
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Sample data error: {e}")
        return False

