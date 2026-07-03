# Databricks notebook source
import pandas as pd
import os
import glob
import pyspark as pys
from datetime import datetime

df_customers = spark.read.table("depiworkspace.default.customer_clean")
df_payments  = spark.read.table("depiworkspace.default.payments_clean")
df_calls     = spark.read.table("depiworkspace.default.calls_clean")
df_network   = spark.read.table("depiworkspace.default.network_clean")
df_mobile    = spark.read.table("depiworkspace.default.mobile_clean")
df_cons      = spark.read.table("depiworkspace.default.consumption_clean")
df_cons_lkp  = spark.read.table("depiworkspace.default.consumption_lookup_clean")
df_loyalty   = spark.read.table("depiworkspace.default.loyalty_clean")

print("Customers:", df_customers.count())
print("Payments:", df_payments.count())


display(df_customers.groupBy("SUBSCRIBER_STATUS").count())


from pyspark.sql import functions as F
from pyspark.sql.functions import col, when, datediff, current_date, floor

df_customers = df_customers.withColumn("CHURN", 
    when(col("SUBSCRIBER_STATUS") == "SUSPENDED", 1).otherwise(0))

df_customers = df_customers.toPandas(); df_customers['BIRTHDATE'] = pd.to_datetime(df_customers['BIRTHDATE'])
df_customers['AGE'] = (datetime.now() - df_customers['BIRTHDATE']).dt.days // 365

df_customers['ACTIVATION_DATE'] = pd.to_datetime(df_customers['ACTIVATION_DATE'])
df_customers['TENURE_DAYS'] = (datetime.now() - df_customers['ACTIVATION_DATE']).dt.days

df_customers = df_customers.drop(columns=['NAME', 'ID_TYPE', 'GROUP_ID#', 
                       'SUBSCRIBER_STATUS', 'STATUS_DATE',
                       'BIRTHDATE', 'ACTIVATION_DATE'])

display(df_customers.shape)
display(df_customers.head())



print("Shape:", df_customers.count(), len(df_customers.columns))
print("Columns:", df_customers.columns)
display(df_customers.describe())


from pyspark.sql.functions import sum, avg, count

df_payments_agg = df_payments.groupBy("SUBSCRIBER_ID#").agg(
    sum("RENT_REVENUE").alias("TOTAL_RENT"),
    sum("IN_BUNDLE_REVENUE").alias("TOTAL_IN_BUNDLE"),
    sum("OUT_BUNDLE_REVENUE").alias("TOTAL_OUT_BUNDLE"),
    sum("DEVICES_REVENUE").alias("TOTAL_DEVICES"),
    sum("ADDON_REVENUE").alias("TOTAL_ADDON"),
    sum("TAX_AMOUNT").alias("TOTAL_TAX"),
    avg("IN_BUNDLE_REVENUE").alias("AVG_IN_BUNDLE"),
    count("Payment_ID").alias("NUM_PAYMENTS")
)

display(df_payments_agg)


from pyspark.sql.functions import sum, avg, count, max, min

# Calls Aggregation
df_calls_agg = spark.read.table("depiworkspace.default.calls_clean") \
    .groupBy("ACCOUNT_ID#").agg(
        count("CALL_ID").alias("TOTAL_CALLS"),
        avg("C_HOUR").alias("AVG_CALL_HOUR")
    )

# Consumption Aggregation
df_cons_agg = spark.read.table("depiworkspace.default.consumption_clean") \
    .groupBy("SUBSCRIBER_ID#").agg(
        sum("DAILY_CONSUMPTION_MB").alias("TOTAL_CONSUMPTION_MB"),
        avg("DAILY_CONSUMPTION_MB").alias("AVG_DAILY_CONSUMPTION_MB"),
        count("Consumption_ID").alias("TOTAL_CONSUMPTION_RECORDS")
    )

# Mobile App Aggregation
df_mobile_agg = spark.read.table("depiworkspace.default.mobile_clean") \
    .groupBy("CUSTOMER_ID#").agg(
        count("LOG_ID").alias("TOTAL_MOBILE_ACTIONS"),
        sum("DURATION_IN_SEC").alias("TOTAL_MOBILE_DURATION"),
        avg("DURATION_IN_SEC").alias("AVG_MOBILE_DURATION")
    )

display(df_calls_agg.limit(5))
display(df_cons_agg.limit(5))
display(df_mobile_agg.limit(5))



df_customers_spark = spark.createDataFrame(df_customers)
df_payments_spark = df_payments_agg 
df_cons_spark = df_cons_agg         
df_mobile_spark = df_mobile_agg     
df_calls_spark = df_calls_agg        
df_network_spark = spark.read.table("depiworkspace.default.network_clean")

df_gold = df_customers_spark \
    .join(df_payments_spark, on="SUBSCRIBER_ID#", how="left") \
    .join(df_cons_spark, on="SUBSCRIBER_ID#", how="left") \
    .join(df_mobile_spark, 
          df_customers_spark["CUSTOMER_ID#"] == df_mobile_spark["CUSTOMER_ID#"], 
          how="left") \
    .drop(df_mobile_spark["CUSTOMER_ID#"]) \
    .join(df_calls_spark, 
          df_customers_spark["ACCOUNT_ID#"] == df_calls_spark["ACCOUNT_ID#"], 
          how="left") \
    .drop(df_calls_spark["ACCOUNT_ID#"]) \
    .join(df_network_spark, on="SERVICE_NUMBER#", how="left")

print("Gold Rows:", df_gold.count())
print("Gold Columns:", len(df_gold.columns))
display(df_gold.limit(5))


df_gold.write.mode("overwrite").saveAsTable("depiworkspace.default.gold_telecom")
print("Gold Table Saved!")
