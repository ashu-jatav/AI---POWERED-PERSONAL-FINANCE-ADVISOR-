print("🔥 TRAIN START")

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# Load dataset
DATASET_PATH = "DATASET/dataset1.csv"
df = pd.read_csv(DATASET_PATH)

df.columns = df.columns.str.strip()

# Standardize column names
rename_map = {}
for col in df.columns:
    if col.lower() == "transaction description":
        rename_map[col] = "Description"
    elif col.lower() == "date":
        rename_map[col] = "Date"
    elif col.lower() == "category":
        rename_map[col] = "Category"
    elif col.lower() == "amount":
        rename_map[col] = "Amount"
    elif col.lower() == "type":
        rename_map[col] = "Type"
    elif col.lower() == "location":
        rename_map[col] = "Location"

df = df.rename(columns=rename_map)

# Drop rows with missing critical values
df = df.dropna(subset=["Date", "Category", "Amount", "Type"])

# Parse date
df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True, errors="coerce")
df = df.dropna(subset=["Date"])

# Ensure Amount is numeric
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

# Extract date features
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Day"] = df["Date"].dt.day
df["DayOfWeek"] = df["Date"].dt.dayofweek

# Filter to expenses for prediction target, but keep income as feature context
expense_df = df[df["Type"].str.lower() == "expense"].copy()

if expense_df.empty:
    print("❌ No expense data found!")
    exit(1)

# For prediction: predict Amount based on Category, Location, Year, Month, Day, DayOfWeek
features = ["Category", "Location", "Year", "Month", "Day", "DayOfWeek"]
target = "Amount"

# Encode categoricals
le_category = LabelEncoder()
le_location = LabelEncoder()

expense_df["Category_enc"] = le_category.fit_transform(expense_df["Category"].astype(str))
expense_df["Location_enc"] = le_location.fit_transform(expense_df["Location"].fillna("Unknown").astype(str))

X = expense_df[["Category_enc", "Location_enc", "Year", "Month", "Day", "DayOfWeek"]]
y = expense_df[target]

print(f"📊 Total Expense Transactions: {len(expense_df)}")
print(f"💰 Total Spending: {y.sum():,.2f}")
print(f"📈 Mean Expense: {y.mean():,.2f}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n✅ MODEL EVALUATION")
print(f"   MAE:  {mae:,.2f}")
print(f"   MSE:  {mse:,.2f}")
print(f"   R²:   {r2:.4f}")

# Save model and encoders
joblib.dump(model, "model.pkl")
joblib.dump(le_category, "le_category.pkl")
joblib.dump(le_location, "le_location.pkl")

print("\n💾 Model saved to model.pkl")
print("💾 Encoders saved to le_category.pkl and le_location.pkl")
print("🔥 TRAIN COMPLETE")

