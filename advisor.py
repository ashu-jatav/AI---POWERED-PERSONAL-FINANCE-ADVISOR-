import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import os

MODEL_PATH = "model.pkl"
LE_CAT_PATH = "le_category.pkl"
LE_LOC_PATH = "le_location.pkl"

def load_model():
    try:
        model = joblib.load(MODEL_PATH)
        le_cat = joblib.load(LE_CAT_PATH)
        le_loc = joblib.load(LE_LOC_PATH)
        return model, le_cat, le_loc
    except Exception as e:
        print(f"Model load error: {e}")
        return None, None, None

def predict_expense(df: pd.DataFrame, model, le_cat, le_loc) -> dict:
    if df.empty or model is None:
        return {"prediction": 0, "confidence": "low", "breakdown": {}}
    
    expense_df = df[df["type"].str.lower() == "expense"].copy()
    if expense_df.empty:
        return {"prediction": 0, "confidence": "low", "breakdown": {}}
    
    # Predict next month total expense based on recent pattern
    expense_df["date"] = pd.to_datetime(expense_df["date"], errors="coerce")
    expense_df = expense_df.dropna(subset=["date"])
    
    if expense_df.empty:
        return {"prediction": 0, "confidence": "low", "breakdown": {}}
    
    # Get user's top categories and locations
    latest_date = expense_df["date"].max()
    next_month = latest_date + pd.DateOffset(months=1)
    
    cat_counts = expense_df["category"].value_counts().head(5)
    loc_counts = expense_df["location"].value_counts().head(3)
    
    predictions = []
    breakdown = {}
    
    feature_names = ["Category_enc", "Location_enc", "Year", "Month", "Day", "DayOfWeek"]
    for cat in cat_counts.index:
        for loc in loc_counts.index:
            try:
                cat_enc = le_cat.transform([cat])[0] if cat in le_cat.classes_ else 0
                loc_enc = le_loc.transform([loc])[0] if loc in le_loc.classes_ else 0
                input_df = pd.DataFrame([[cat_enc, loc_enc, next_month.year, next_month.month, 15, 2]], columns=feature_names)
                pred = model.predict(input_df)[0]
                predictions.append(pred)
                breakdown[cat] = breakdown.get(cat, 0) + pred / len(loc_counts)
            except Exception:
                continue
    
    if not predictions:
        avg_expense = expense_df["amount"].mean()
        return {"prediction": avg_expense * 30, "confidence": "medium", "breakdown": {"Average": avg_expense * 30}}
    
    total_pred = sum(predictions) / len(predictions) * len(cat_counts)
    confidence = "high" if len(expense_df) > 20 else "medium"
    
    return {"prediction": round(total_pred, 2), "confidence": confidence, "breakdown": {k: round(v, 2) for k, v in breakdown.items()}}

def generate_insights(df: pd.DataFrame, model=None, le_cat=None, le_loc=None) -> list:
    insights = []
    
    if df.empty:
        return ["⚠ No transaction data available. Add transactions to get insights."]
    
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    
    income_df = df[df["type"].str.lower() == "income"]
    expense_df = df[df["type"].str.lower() == "expense"]
    
    total_income = income_df["amount"].sum()
    total_expense = expense_df["amount"].sum()
    savings = total_income - total_expense
    
    # Basic financial health
    if savings < 0:
        insights.append(f"🚨 You're spending ₹{abs(savings):,.0f} more than you earn. Consider cutting expenses.")
    elif savings > 0:
        insights.append(f"💰 Great! You're saving ₹{savings:,.0f}. Keep it up!")
    else:
        insights.append("⚖️ Your income equals expenses. Try to create a savings buffer.")
    
    # Category insights
    if not expense_df.empty:
        cat_spending = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        total = cat_spending.sum()
        
        for cat, amt in cat_spending.head(3).items():
            pct = (amt / total) * 100 if total > 0 else 0
            if pct > 30:
                insights.append(f"⚠️ High spending on {cat}: ₹{amt:,.0f} ({pct:.1f}% of total)")
            elif pct > 15:
                insights.append(f"📊 Significant spending on {cat}: ₹{amt:,.0f} ({pct:.1f}%)")
        
        # Anomaly detection
        mean_exp = expense_df["amount"].mean()
        std_exp = expense_df["amount"].std()
        if std_exp > 0:
            anomalies = expense_df[expense_df["amount"] > mean_exp + 2.5 * std_exp]
            if not anomalies.empty:
                insights.append(f"🔍 Found {len(anomalies)} unusually high expense(s). Review large transactions.")
    
    # Savings rate
    if total_income > 0:
        savings_rate = (savings / total_income) * 100
        if savings_rate < 10:
            insights.append(f"📉 Savings rate is {savings_rate:.1f}%. Aim for at least 20%.")
        elif savings_rate >= 20:
            insights.append(f"🌟 Excellent! Your savings rate is {savings_rate:.1f}%.")
        else:
            insights.append(f"👍 Savings rate is {savings_rate:.1f}%. Try to push toward 20%.")
    
    # ML prediction insight
    if model is not None and le_cat is not None and le_loc is not None:
        pred_data = predict_expense(df, model, le_cat, le_loc)
        if pred_data["prediction"] > 0:
            insights.append(f"🤖 AI Prediction: Expected next month expense ~ ₹{pred_data['prediction']:,.0f} (confidence: {pred_data['confidence']})")
    
    return insights

