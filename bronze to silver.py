# Databricks notebook source
import os
import pandas as pd
import glob

print("--- Loading Bronze Data using Pandas (Python Mode) ---")

# المسار بتاعك
base = "/Volumes/depiworkspace/default/telecom_data"
print(f"Base exists: {os.path.exists(base)}")
if os.path.exists(base):
    print("\nFolders found inside base:")
    for item in os.listdir(base):
        print(f"  📁 {item}")

# دالة صغيرة لتقرأ أي ملف CSV جوه الفولدر بـ Pandas
def load_csv_pandas(file_name):
    path = os.path.join(base, file_name)
    if os.path.exists(path):
        print(f' reading: {file_name}')
        return pd.read_csv(path)
    else:
        print(f"Warning: No csv found:{file_name}")
        return None

# قراءة الـ 8 جداول في ثواني
pd_cust = load_csv_pandas("Customer.csv")
pd_pay = load_csv_pandas("Payments.csv")
pd_calls = load_csv_pandas("Calls.csv")
pd_cons = load_csv_pandas("Consumption.csv")
pd_cons_lkp = load_csv_pandas("Consumption_RG_LKP.csv")
pd_net = load_csv_pandas("Network_Elements.csv")
pd_loyalty = load_csv_pandas("Loyalty_Points_Configuration.csv")
pd_mobile = load_csv_pandas("Mobile_App.csv")



# COMMAND ----------

print("--- RUNNING GLOBAL EDA (PANDAS MODE) ---")

all_pandas_dfs = {
    "Customer": pd_cust, "Payments": pd_pay, "Calls": pd_calls, 
    "Consumption": pd_cons, "Consumption LKP": pd_cons_lkp,
    "Network": pd_net, "Loyalty": pd_loyalty, "Mobile App": pd_mobile
}

for name, df in all_pandas_dfs.items():
    if df is not None:
        print(f"\n========== {name} Table ==========")
        print(f"Total Rows (Before Cleaning): {len(df)}")
        print(f"Total Duplicates: {df.duplicated().sum()}")
        
        # Calculate missing values count and percentage per column
        null_counts = df.isnull().sum()
        null_cols = null_counts[null_counts > 0]
        if not null_cols.empty:
            print("Columns with NULLs:")
            for col_name, count in null_cols.items():
                print(f"  - {col_name}: {count} nulls ({ (count/len(df))*100 :.2f}%)")
        else:
            print("No NULL values found in this table.")

# COMMAND ----------

print("showing data types and info for all raw tables")

# Dictionary containing all your raw, untouched DataFrames
raw_dfs = {
    "Customer (Raw)": pd_cust, 
    "Payments (Raw)": pd_pay, 
    "Calls (Raw)": pd_calls,
    "Consumption (Raw)": pd_cons, 
    "Consumption LKP (Raw)": pd_cons_lkp,
    "Network Elements (Raw)": pd_net, 
    "Loyalty Configuration (Raw)": pd_loyalty, 
    "Mobile App (Raw)": pd_mobile
}

# Loop through each raw table and print its info structure
for name, df in raw_dfs.items():
    if df is not None:
        print("\n" + "="*40)
        print(f" RAW TABLE: {name} ")
        print("="*40)
        df.info()

# COMMAND ----------

print("--- CLEANING: CUSTOMER TABLE ---")

# Create an explicit copy to prevent SettingWithCopyWarning
pd_cust_clean = pd_cust.copy()

# 1. Handling Nulls (Executed before type casting)
if "BIRTHDATE" in pd_cust_clean.columns:
    pd_cust_clean = pd_cust_clean.dropna(subset=["BIRTHDATE"])

if "GROUP_ID#" in pd_cust_clean.columns:
    pd_cust_clean["GROUP_ID#"] = pd_cust_clean["GROUP_ID#"].fillna("Unknown")
    pd_cust_clean["GROUP_ID#"] = pd_cust_clean["GROUP_ID#"].replace(r'^\s*$', 'Unknown', regex=True)

# 2. Handling Duplicates
pd_cust_clean = pd_cust_clean.drop_duplicates()

# 3. Type Casting & Trimming
cust_object_cols = [
    "SUBSCRIBER_ID#", "ACCOUNT_ID#", "CUSTOMER_ID#", "GROUP_ID#", 
    "SUBSCRIPTION_PLAN_FAMILY_ID#", "SUBSCRIPTION_PLAN_ID#", 
    "SERVICE_NUMBER#", "PHONE_NUMBER", "ZIP_CODE", "POSTAL_CODE"
]
for c in cust_object_cols:
    if c in pd_cust_clean.columns:
        pd_cust_clean[c] = pd_cust_clean[c].astype(str).str.strip()

if "NAME" in pd_cust_clean.columns:
    pd_cust_clean["NAME"] = pd_cust_clean["NAME"].astype(str).str.strip()
if "SUBSCRIBER_STATUS" in pd_cust_clean.columns:
    pd_cust_clean["SUBSCRIBER_STATUS"] = pd_cust_clean["SUBSCRIBER_STATUS"].astype(str).str.strip().str.upper()
if "GENDER" in pd_cust_clean.columns:
    pd_cust_clean["GENDER"] = pd_cust_clean["GENDER"].astype(str).str.strip().str.upper()

# Convert date strings to datetime objects
for date_col in ["STATUS_DATE", "BIRTHDATE", "ACTIVATION_DATE"]:
    if date_col in pd_cust_clean.columns:
        pd_cust_clean[date_col] = pd.to_datetime(pd_cust_clean[date_col], errors='coerce')

print(f"DONE: Customer Cleaned. Final Rows: {len(pd_cust_clean)}")

# COMMAND ----------

print("--- CLEANING: PAYMENTS TABLE ---")

# Create an explicit copy to prevent SettingWithCopyWarning
pd_pay_clean = pd_pay.copy()

# 1. Handling Nulls
revenue_fields = ["RENT_REVENUE", "OUT_BUNDLE_REVENUE", "CREATION_FEES_REVENUE", "DEVICES_REVENUE", "IN_BUNDLE_REVENUE", "ADDON_REVENUE", "TAX_AMOUNT"]
for rf in revenue_fields:
    if rf in pd_pay_clean.columns:
        pd_pay_clean[rf] = pd_pay_clean[rf].fillna(0.0)

# 2. Handling Duplicates
pd_pay_clean = pd_pay_clean.drop_duplicates()

# 3. Type Casting & Trimming
pay_object_cols = ["Payment_ID", "SUBSCRIBER_ID#", "ACCOUNT_ID#", "CUSTOMER_ID#", "TRANSACTION_ID"]
for c in pay_object_cols:
    if c in pd_pay_clean.columns:
        pd_pay_clean[c] = pd_pay_clean[c].astype(str).str.strip()

for rf in revenue_fields:
    if rf in pd_pay_clean.columns:
        pd_pay_clean[rf] = pd_pay_clean[rf].astype(float)

if "CONNECT_DATE" in pd_pay_clean.columns:
    pd_pay_clean["CONNECT_DATE"] = pd.to_datetime(pd_pay_clean["CONNECT_DATE"], errors='coerce')

# 4. Outlier Handling using Interquartile Range (IQR)
if "RENT_REVENUE" in pd_pay_clean.columns:
    q1 = pd_pay_clean["RENT_REVENUE"].quantile(0.25)
    q3 = pd_pay_clean["RENT_REVENUE"].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)
    pd_pay_clean = pd_pay_clean[(pd_pay_clean["RENT_REVENUE"] >= lower_bound) & (pd_pay_clean["RENT_REVENUE"] <= upper_bound)].copy()

print(f"DONE: Payments Cleaned. Final Rows: {len(pd_pay_clean)}")

# COMMAND ----------

print("--- CLEANING: CALLS TABLE ---")

# Create an explicit copy to prevent SettingWithCopyWarning
pd_calls_clean = pd_calls.copy()

# 1. Handling Nulls
pd_calls_clean["ADMIN_STATUS"] = pd_calls_clean["ADMIN_STATUS"].fillna("UNKNOWN")
pd_calls_clean["OPERATION_STATUS"] = pd_calls_clean["OPERATION_STATUS"].fillna("UNKNOWN")
pd_calls_clean["CALLTYPE"] = pd_calls_clean["CALLTYPE"].fillna("UNKNOWN")
if "DURATION" in pd_calls_clean.columns:
    pd_calls_clean["DURATION"] = pd_calls_clean["DURATION"].fillna(0.0)

# 2. Handling Duplicates
pd_calls_clean = pd_calls_clean.drop_duplicates()

# 3. Type Casting & Trimming
calls_cols = ["CALL_ID", "SERVICE_NUMBER#", "ACCOUNT_ID#", "CUSTOMER_ID#", "DESTINATION_NUMBER", "DIALED_NUMBER", "CALL_KEY", "QUEUE", "ADMIN_STATUS", "OPERATION_STATUS", "Language_chosen", "CALLTYPE"]
for c in calls_cols:
    if c in pd_calls_clean.columns:
        pd_calls_clean[c] = pd_calls_clean[c].astype(str).str.strip()

if "DURATION" in pd_calls_clean.columns:
    pd_calls_clean["DURATION"] = pd_calls_clean["DURATION"].astype(float)

# 4. Date Transformations & Timestamp Constructing
month_map = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
if "C_MONTH" in pd_calls_clean.columns:
    pd_calls_clean["FINAL_MONTH"] = pd_calls_clean["C_MONTH"].map(month_map).fillna(pd_calls_clean["C_MONTH"])
    pd_calls_clean["FINAL_MONTH"] = pd_calls_clean["FINAL_MONTH"].astype(str).str.zfill(2)
    pd_calls_clean["C_DAY"] = pd_calls_clean["C_DAY"].astype(str).str.zfill(2)
    
    pd_calls_clean["CALL_TIMESTAMP"] = pd.to_datetime(
        pd_calls_clean["C_YEAR"].astype(str) + "-" + pd_calls_clean["FINAL_MONTH"] + "-" + pd_calls_clean["C_DAY"], 
        errors='coerce'
    )

# 5. Outliers Handling for Call Duration column
if "DURATION" in pd_calls_clean.columns:
    q1 = pd_calls_clean["DURATION"].quantile(0.25)
    q3 = pd_calls_clean["DURATION"].quantile(0.75)
    iqr = q3 - q1
    pd_calls_clean = pd_calls_clean[(pd_calls_clean["DURATION"] >= (q1 - 1.5 * iqr)) & (pd_calls_clean["DURATION"] <= (q3 + 1.5 * iqr))].copy()

print(f"DONE: Calls Cleaned. Final Rows: {len(pd_calls_clean)}")

# COMMAND ----------

print("--- CLEANING: CONSUMPTION & LOYALTY TABLES ---")

# 1. Consumption Table Processing
pd_cons_clean = pd_cons.copy()
pd_cons_clean["RATING_GROUP_ID#"] = pd_cons_clean["RATING_GROUP_ID#"].fillna("0")
pd_cons_clean = pd_cons_clean.drop_duplicates()
cons_object_cols = ["Consumption_ID", "CUSTOMER_ID#", "ACCOUNT_ID#", "SUBSCRIBER_ID#", "PRICE_PLAN_ID#", "RATING_GROUP_ID#", "SERVICE_NUMBER#"]
for key in cons_object_cols:
    if key in pd_cons_clean.columns:
        pd_cons_clean[key] = pd_cons_clean[key].astype(str).str.strip()

# 2. Consumption Lookup Table Processing
pd_cons_lkp_clean = pd_cons_lkp.copy().drop_duplicates()
if "RATING_GROUP_ID#" in pd_cons_lkp_clean.columns:
    pd_cons_lkp_clean["RATING_GROUP_ID#"] = pd_cons_lkp_clean["RATING_GROUP_ID#"].astype(str).str.strip()

# 3. Loyalty Points Table Processing
pd_loyalty_clean = pd_loyalty.copy().drop_duplicates()
loyalty_object_cols = ["SUBSCRIPTION_PLAN_ID#", "LOYALTY_RULE_ID", "CONFIG_ID"]
for c in loyalty_object_cols:
    if c in pd_loyalty_clean.columns:
        pd_loyalty_clean[c] = pd_loyalty_clean[c].astype(str).str.strip()

print("DONE: Consumption & Loyalty Cleaned successfully.")

# COMMAND ----------

print("--- CLEANING: NETWORK ELEMENTS TABLE ---")

# Create an explicit copy to prevent SettingWithCopyWarning
pd_net_clean = pd_net.copy()

# 1. Handling Nulls safely (Checking if column exists first)
if "ZIP_CODE" in pd_net_clean.columns:
    pd_net_clean["ZIP_CODE"] = pd_net_clean["ZIP_CODE"].fillna("00000")

if "CENTRAL_NAME" in pd_net_clean.columns:
    pd_net_clean["CENTRAL_NAME"] = pd_net_clean["CENTRAL_NAME"].fillna("UNKNOWN")

# 2. Handling Duplicates
pd_net_clean = pd_net_clean.drop_duplicates()

# 3. Type Casting & Trimming (Only on columns that actually exist)
possible_net_cols = ["SERVICE_NUMBER#", "ELEMENT_ID", "CABIN_ID", "EXCHANGE_ID", "CENTRAL_ID", "ZIP_CODE"]
for c in possible_net_cols:
    if c in pd_net_clean.columns:
        pd_net_clean[c] = pd_net_clean[c].astype(str).str.strip()

print(f"DONE: Network Elements Cleaned. Final Rows: {len(pd_net_clean)}")

# COMMAND ----------

print("--- CLEANING: MOBILE APP TABLE ---")

# Create an explicit copy to prevent SettingWithCopyWarning
pd_mobile_clean = pd_mobile.copy()

# 1. Handling Nulls safely
if "PLAN_NAME" in pd_mobile_clean.columns:
    pd_mobile_clean["PLAN_NAME"] = pd_mobile_clean["PLAN_NAME"].fillna("UNKNOWN")

if "CATEGORY" in pd_mobile_clean.columns:
    pd_mobile_clean["CATEGORY"] = pd_mobile_clean["CATEGORY"].fillna("UNKNOWN")

for num_col in ["PRICE", "SPEED", "QUOTA"]:
    if num_col in pd_mobile_clean.columns:
        pd_mobile_clean[num_col] = pd_mobile_clean[num_col].fillna(0.0)

# 2. Handling Duplicates
pd_mobile_clean = pd_mobile_clean.drop_duplicates()

# 3. Type Casting & Trimming
possible_mobile_cols = ["SERVICE_NUMBER#", "CUSTOMER_ID#", "PLAN_ID#", "PACKAGE_ID", "PROMO_ID", "LOG_ID"]
for c in possible_mobile_cols:
    if c in pd_mobile_clean.columns:
        pd_mobile_clean[c] = pd_mobile_clean[c].astype(str).str.strip()

for num_col in ["PRICE", "SPEED", "QUOTA"]:
    if num_col in pd_mobile_clean.columns:
        pd_mobile_clean[num_col] = pd_mobile_clean[num_col].astype(float)

print(f"DONE: Mobile App Cleaned. Final Rows: {len(pd_mobile_clean)}")

# COMMAND ----------

print("showing data types and info for all cleaned tables")

# Dictionary containing all your clean DataFrames
final_cleaned_dfs = {
    "Customer": pd_cust_clean, 
    "Payments": pd_pay_clean, 
    "Calls": pd_calls_clean,
    "Consumption": pd_cons_clean, 
    "Consumption LKP": pd_cons_lkp_clean,
    "Network Elements": pd_net_clean, 
    "Loyalty Configuration": pd_loyalty_clean, 
    "Mobile App": pd_mobile_clean
}

# Loop through each table and print its info structure
for name, df in final_cleaned_dfs.items():
    if df is not None:
        print("\n" + "="*40)
        print(f" TABLE: {name} ")
        print("="*40)
        # Using buf=None and capturing or directly printing info
        df.info()

# COMMAND ----------

print("final quality check ")

final_cleaned_dfs = {
    "Customer": pd_cust_clean, "Payments": pd_pay_clean, "Calls": pd_calls_clean,
    "Consumption": pd_cons_clean, "Consumption LKP": pd_cons_lkp_clean,
    "Network": pd_net_clean, "Loyalty": pd_loyalty_clean, "Mobile": pd_mobile_clean
}

all_clear = True
for name, df in final_cleaned_dfs.items():
    if df is not None:
        total_nulls = df.isnull().sum().sum()
        if total_nulls == 0:
            print(f"SUCCESS: {name} Table is clean. Rows: {len(df)} | Missing Values: 0")
        else:
            all_clear = False
            print(f"WARNING: {name} Table still contains {total_nulls} null values.")

if all_clear:
    print("\nVERIFICATION COMPLETE: All tables are 100% clean and ready for the next layer.")

# COMMAND ----------

print("--- FINAL PREVIEW AND SCHEMA CHECK FOR ALL TABLES ---")

final_cleaned_dfs = {
    "1. CUSTOMER TABLE": pd_cust_clean, 
    "2. PAYMENTS TABLE": pd_pay_clean, 
    "3. CALLS TABLE": pd_calls_clean,
    "4. NETWORK ELEMENTS TABLE": pd_net_clean, 
    "5. MOBILE APP TABLE": pd_mobile_clean, 
    "6. CONSUMPTION TABLE": pd_cons_clean, 
    "7. CONSUMPTION LKP TABLE": pd_cons_lkp_clean, 
    "8. LOYALTY CONFIGURATION TABLE": pd_loyalty_clean
}

for name, df in final_cleaned_dfs.items():
    if df is not None:
        print("\n" + "="*20 + f" {name} " + "="*20)
        print("Schema (Data Types):")
        print(df.dtypes)
        
        print("\nPreview (First 5 Rows):")
        # Automatically select the first 4 columns that actually exist to avoid KeyErrors
        available_cols = df.columns[:4]
        print(df[available_cols].head(5))

# COMMAND ----------

print("\nCustomer table check")

# 1. CUSTOMER TABLE
print("\n" + "="*20 + " 1. CUSTOMER TABLE " + "="*20)
print("Schema (Data Types):")
print(pd_cust_clean.dtypes)
print("\nPreview (First 5 Rows):")
print(pd_cust_clean[["CUSTOMER_ID#", "SUBSCRIBER_ID#", "ACTIVATION_DATE", "BIRTHDATE"]].head(5))

# COMMAND ----------

# شوف الـ catalogs المتاحة
spark.sql("SHOW CATALOGS").show()

# شوف الـ schemas
spark.sql("SHOW SCHEMAS IN depiworkspace").show()

# COMMAND ----------

spark.createDataFrame(pd_cust_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.customer_clean")
spark.createDataFrame(pd_pay_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.payments_clean")
spark.createDataFrame(pd_calls_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.calls_clean")
spark.createDataFrame(pd_net_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.network_clean")
spark.createDataFrame(pd_mobile_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.mobile_clean")
spark.createDataFrame(pd_cons_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.consumption_clean")
spark.createDataFrame(pd_cons_lkp_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.consumption_lookup_clean")
spark.createDataFrame(pd_loyalty_clean).write.mode("overwrite").saveAsTable("depiworkspace.default.loyalty_clean")

# COMMAND ----------

pd_cust_clean['SUBSCRIBER_STATUS'].value_counts()