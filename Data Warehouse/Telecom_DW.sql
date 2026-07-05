-- Databricks notebook source
CREATE OR REPLACE TABLE depiworkspace.default.dim_customer AS
SELECT DISTINCT
    `CUSTOMER_ID#` AS CUSTOMER_ID,
    GENDER,
    AGE,
    NATIONALITY,
    CUSTOMER_CLASS,
    CUSTOMER_TYPE
FROM depiworkspace.default.gold_telecom;

CREATE OR REPLACE TABLE depiworkspace.default.dim_subscriber AS
SELECT DISTINCT
    `SERVICE_NUMBER#` AS SERVICE_NUMBER,
    `SUBSCRIBER_ID#` AS SUBSCRIBER_ID,
    `ACCOUNT_ID#` AS ACCOUNT_ID,
    SUBSCRIBER_TYPE,
    TENURE_DAYS
FROM depiworkspace.default.gold_telecom;

CREATE OR REPLACE TABLE depiworkspace.default.dim_network AS
SELECT DISTINCT
    CABIN_CODE,
    CENTRAL_NAME,
    CABIN_LAT,
    CABIN_LONG,
    GOV,
    TECHNOLOGY_TYPE
FROM depiworkspace.default.gold_telecom;

CREATE OR REPLACE TABLE depiworkspace.default.dim_plan AS
SELECT DISTINCT
    `SUBSCRIPTION_PLAN_ID#` AS SUBSCRIPTION_PLAN_ID,
    MODEL,
    FAMILY,
    CATEGORY,
    ACCUMULATION_FACTOR
FROM depiworkspace.default.loyalty_clean;

CREATE OR REPLACE TABLE depiworkspace.default.fact_telecom AS
SELECT
    `CUSTOMER_ID#` AS CUSTOMER_ID,
    `SERVICE_NUMBER#` AS SERVICE_NUMBER,
    `SUBSCRIPTION_PLAN_ID#` AS SUBSCRIPTION_PLAN_ID,
    CABIN_CODE,
    CHURN,
    TOTAL_RENT,
    TOTAL_IN_BUNDLE,
    TOTAL_OUT_BUNDLE,
    TOTAL_DEVICES,
    TOTAL_ADDON,
    TOTAL_TAX,
    AVG_IN_BUNDLE,
    NUM_PAYMENTS,
    TOTAL_CONSUMPTION_MB,
    AVG_DAILY_CONSUMPTION_MB,
    TOTAL_CONSUMPTION_RECORDS,
    TOTAL_MOBILE_ACTIONS,
    TOTAL_MOBILE_DURATION,
    AVG_MOBILE_DURATION,
    TOTAL_CALLS,
    AVG_CALL_HOUR
FROM depiworkspace.default.gold_telecom;

-- COMMAND ----------

SELECT COUNT(*) AS Customer_Count
FROM depiworkspace.default.dim_customer;

-- COMMAND ----------

SELECT COUNT(*) AS Subscriber_Count
FROM depiworkspace.default.dim_subscriber;

-- COMMAND ----------

SELECT COUNT(*) AS Network_Count
FROM depiworkspace.default.dim_network;

-- COMMAND ----------

SELECT COUNT(*) AS Plan_Count
FROM depiworkspace.default.dim_plan;

-- COMMAND ----------

SELECT COUNT(*) AS Fact_Count
FROM depiworkspace.default.fact_telecom;

-- COMMAND ----------

SELECT
COUNT(*) AS Total,
COUNT(DISTINCT CUSTOMER_ID) AS Unique_Customers
FROM depiworkspace.default.dim_customer;

-- COMMAND ----------

SELECT
    CUSTOMER_ID,
    COUNT(*) AS cnt
FROM depiworkspace.default.dim_customer
GROUP BY CUSTOMER_ID
HAVING COUNT(*) > 1;

-- COMMAND ----------

SELECT *
FROM depiworkspace.default.dim_customer
WHERE CUSTOMER_ID IN ('1107071170', '11011235537')
ORDER BY CUSTOMER_ID;

-- COMMAND ----------

SELECT
COUNT(*) AS Total,
COUNT(DISTINCT SERVICE_NUMBER) AS Unique_Services
FROM depiworkspace.default.dim_subscriber;

-- COMMAND ----------

SELECT
COUNT(*) AS Total,
COUNT(DISTINCT CABIN_CODE) AS Unique_Cabins
FROM depiworkspace.default.dim_network;

-- COMMAND ----------

SELECT
    CABIN_CODE,
    COUNT(*) AS cnt
FROM depiworkspace.default.dim_network
GROUP BY CABIN_CODE
HAVING COUNT(*) > 1;

-- COMMAND ----------

SELECT
COUNT(*) AS Total,
COUNT(DISTINCT SUBSCRIPTION_PLAN_ID) AS Unique_Plans
FROM depiworkspace.default.dim_plan;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS depiworkspace.telecom;

ALTER TABLE depiworkspace.default.dim_customer   RENAME TO depiworkspace.telecom.dim_customer;
ALTER TABLE depiworkspace.default.dim_network    RENAME TO depiworkspace.telecom.dim_network;
ALTER TABLE depiworkspace.default.dim_plan       RENAME TO depiworkspace.telecom.dim_plan;
ALTER TABLE depiworkspace.default.dim_subscriber RENAME TO depiworkspace.telecom.dim_subscriber;
ALTER TABLE depiworkspace.default.fact_telecom   RENAME TO depiworkspace.telecom.fact_telecom;

-- COMMAND ----------

SHOW TABLES IN depiworkspace.telecom;

-- COMMAND ----------

DESCRIBE TABLE EXTENDED depiworkspace.telecom.dim_customer;

-- COMMAND ----------

GRANT MODIFY, SELECT ON TABLE depiworkspace.telecom.dim_customer TO `ha30607100203665@depi.eui.edu.eg`;

-- COMMAND ----------

GRANT ALL PRIVILEGES ON SCHEMA depiworkspace.telecom TO `ha30607100203665@depi.eui.edu.eg`;

-- COMMAND ----------

-- SELECT COUNT(*) AS null_count FROM depiworkspace.telecom.dim_customer   WHERE CUSTOMER_ID IS NULL;
-- SELECT COUNT(*) AS null_count FROM depiworkspace.telecom.dim_subscriber WHERE SERVICE_NUMBER IS NULL;
-- SELECT COUNT(*) AS null_count FROM depiworkspace.telecom.dim_plan       WHERE SUBSCRIPTION_PLAN_ID IS NULL;
SELECT COUNT(*) AS null_count FROM depiworkspace.telecom.dim_network    WHERE CABIN_CODE IS NULL;

-- COMMAND ----------

SELECT COUNT(*) AS affected_rows 
FROM depiworkspace.telecom.fact_telecom 
WHERE CABIN_CODE IS NULL;

-- COMMAND ----------

-- 1. ضيف صف "Unknown" لجدول الشبكة
INSERT INTO depiworkspace.telecom.dim_network 
(CABIN_CODE, CENTRAL_NAME, CABIN_LAT, CABIN_LONG, GOV, TECHNOLOGY_TYPE)
VALUES ('UNKNOWN', 'Unknown', NULL, NULL, 'Unknown', 'Unknown');

-- 2. حدّث الـ 77 صف في fact_telecom ليشاوروا على القيمة دي بدل NULL
UPDATE depiworkspace.telecom.fact_telecom
SET CABIN_CODE = 'UNKNOWN'
WHERE CABIN_CODE IS NULL;

-- 3. امسح الصف الفاضي الأصلي في dim_network (لو موجود منفصل عن UNKNOWN)
DELETE FROM depiworkspace.telecom.dim_network WHERE CABIN_CODE IS NULL;

-- COMMAND ----------

SELECT COUNT(*) AS remaining_nulls 
FROM depiworkspace.telecom.fact_telecom 
WHERE CABIN_CODE IS NULL;

-- COMMAND ----------

SELECT * FROM depiworkspace.telecom.dim_network WHERE CABIN_CODE = 'UNKNOWN';

-- COMMAND ----------

ALTER TABLE depiworkspace.telecom.dim_customer
  ALTER COLUMN CUSTOMER_ID SET NOT NULL;


ALTER TABLE depiworkspace.telecom.dim_customer
  ADD CONSTRAINT pk_customer PRIMARY KEY (CUSTOMER_ID);

-- COMMAND ----------

ALTER TABLE depiworkspace.telecom.dim_subscriber
  ALTER COLUMN SERVICE_NUMBER SET NOT NULL;
ALTER TABLE depiworkspace.telecom.dim_subscriber
  ADD CONSTRAINT pk_subscriber PRIMARY KEY (SERVICE_NUMBER);

ALTER TABLE depiworkspace.telecom.dim_plan
  ALTER COLUMN SUBSCRIPTION_PLAN_ID SET NOT NULL;
ALTER TABLE depiworkspace.telecom.dim_plan
  ADD CONSTRAINT pk_plan PRIMARY KEY (SUBSCRIPTION_PLAN_ID);

ALTER TABLE depiworkspace.telecom.dim_network
  ALTER COLUMN CABIN_CODE SET NOT NULL;
ALTER TABLE depiworkspace.telecom.dim_network
  ADD CONSTRAINT pk_network PRIMARY KEY (CABIN_CODE);

-- COMMAND ----------

DESCRIBE TABLE EXTENDED depiworkspace.telecom.dim_network;

-- COMMAND ----------

ALTER TABLE depiworkspace.telecom.dim_customer   ALTER COLUMN CUSTOMER_ID SET NOT NULL;
ALTER TABLE depiworkspace.telecom.dim_subscriber ALTER COLUMN SERVICE_NUMBER SET NOT NULL;
ALTER TABLE depiworkspace.telecom.dim_plan       ALTER COLUMN SUBSCRIPTION_PLAN_ID SET NOT NULL;

-- COMMAND ----------

ALTER TABLE depiworkspace.telecom.fact_telecom ADD CONSTRAINT fk_customer   FOREIGN KEY (CUSTOMER_ID) REFERENCES depiworkspace.telecom.dim_customer (CUSTOMER_ID);
ALTER TABLE depiworkspace.telecom.fact_telecom ADD CONSTRAINT fk_subscriber FOREIGN KEY (SERVICE_NUMBER) REFERENCES depiworkspace.telecom.dim_subscriber (SERVICE_NUMBER);
ALTER TABLE depiworkspace.telecom.fact_telecom ADD CONSTRAINT fk_plan       FOREIGN KEY (SUBSCRIPTION_PLAN_ID) REFERENCES depiworkspace.telecom.dim_plan (SUBSCRIPTION_PLAN_ID);
ALTER TABLE depiworkspace.telecom.fact_telecom ADD CONSTRAINT fk_network    FOREIGN KEY (CABIN_CODE) REFERENCES depiworkspace.telecom.dim_network (CABIN_CODE);

-- COMMAND ----------

DESCRIBE TABLE EXTENDED depiworkspace.telecom.fact_telecom;

-- COMMAND ----------

select * from telecom.dim_customer