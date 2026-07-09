# NHA-4-87
# 📡 Telecom Customer Analytics & Churn Prediction

End-to-end data engineering & analytics project for a telecom operator: raw operational data is ingested, cleaned through a **Bronze → Silver → Gold (medallion)** pipeline on **Azure Databricks**, modeled into a **star-schema data warehouse**, used to train a **churn prediction model** (PySpark ML), and finally visualized in an interactive **Power BI** dashboard.

> Built as part of the DEPI (Digital Egypt Pioneers Initiative) data engineering track — project code `NHA-4-087`. The entire pipeline (storage, compute, Unity Catalog, notebooks) runs on **Microsoft Azure**, using **Azure Databricks** as the core engineering platform.

---

## 🎥 Demo

_🚧 Demo video/GIF coming soon — will be added here._

<!-- Once rea

https://github.com/user-attachments/assets/23e278dd-2e05-43f0-8f11-c2da43a60205

dy, replace with something like:
[![Watch the demo](assets/powerbi_dashboard.jpeg)](https://your-demo-link-here)

-->

## 🖼️ Dashboard Preview

![Power BI Dashboard](https://github.com/nhahub/NHA-4-087/blob/main/PowerBi.pdf)

---

## 🧱 Project Architecture

```
Raw CSV files (8 source tables)
        │
        ▼
   BRONZE  ──►  bronze_samples/*.csv           (raw, as-is)
        │
        ▼  ETL/bronze to silver.py
   SILVER  ──►  *_clean tables                 (deduped, typed, nulls handled, outliers removed)
        │
        ▼  ETL/silver to gold.py
   GOLD    ──►  gold_telecom                   (one wide, analytics-ready customer table + CHURN label)
        │
        ├──►  Data Warehouse/Telecom_DW.sql    ──►  Star schema (fact_telecom + 4 dimensions)
        │
        ├──►  Model.py                         ──►  PySpark churn prediction model (Logistic Regression)
        │
        └──►  Power BI                         ──►  Executive dashboard (see screenshot above)
```

For the full technical write-up (data dictionary, DW schema, ML methodology, Power BI details) see [**`docs/DOCUMENTATION.md`**](docs/DOCUMENTATION.md).

---

## 📂 Repository Structure

```
NHA-4-087/
├── bronze_samples/                 # Sample raw CSVs (8 source tables)
│   ├── customer_sample.csv
│   ├── payments_sample.csv
│   ├── calls_sample.csv
│   ├── consumption_sample.csv
│   ├── consumption_rg_lkp_sample.csv
│   ├── network_elements_sample.csv
│   ├── mobile_app_sample.csv
│   └── loyalty_points_configuration_sample.csv
├── ETL/
│   ├── bronze to silver.py         # Cleaning: nulls, duplicates, types, outliers (IQR)
│   └── silver to gold.py           # Feature engineering, aggregation, CHURN label, gold table
├── Data Warehouse/
│   ├── Telecom_DW.sql              # Star schema DDL (dims + fact) + constraints + data quality fixes
│   └── Screenshot ....png          # Entity-relationship diagram
├── Model.py                        # PySpark churn prediction (Logistic Regression + grid search)
├── docs/
│   ├── DOCUMENTATION.md            # Full technical documentation
│   └── POWER_BI.md                 # Power BI dashboard documentation
└── README.md
```

---

## 🛠️ Tech Stack

| Layer                | Tools |
|-----------------------|-------|
| Cloud platform          | Microsoft Azure |
| Data processing        | Azure Databricks, PySpark, Pandas |
| Storage / Warehouse    | Unity Catalog (Delta tables) on Azure Databricks, SQL (star schema) |
| Machine Learning       | PySpark MLlib (Logistic Regression, `VectorAssembler`, `StringIndexer`) |
| Visualization / BI     | Power BI |
| Language               | Python, SQL |

---

## 📊 Data Sources

Eight raw operational tables feed the pipeline: **Customer, Payments, Calls, Consumption, Consumption Rating-Group Lookup, Network Elements, Mobile App activity,** and **Loyalty Points Configuration**. Samples for each are provided under [`bronze_samples/`]([bronze_samples/](https://drive.google.com/drive/folders/1lShVj-sjA-i1eIJzwZx3-3xs3rUE57oW?usp=sharing)).

## 🏗️ Data Warehouse (Star Schema)

| Table | Type | Grain |
|---|---|---|
| `dim_customer` | Dimension | 1 row per customer |
| `dim_subscriber` | Dimension | 1 row per subscriber / service number |
| `dim_network` | Dimension | 1 row per network cabin/site |
| `dim_plan` | Dimension | 1 row per subscription plan |
| `fact_telecom` | Fact | 1 row per customer, with revenue, usage & churn metrics |

Full DDL, keys, and quality fixes: [`Data Warehouse/Telecom_DW.sql`]([<Data Warehouse/Telecom_DW.sql>](https://drive.google.com/drive/folders/1EsoNBv6jhmQgZcqbxDjKlzkasB-nWte9?usp=sharing)). Diagram: `Data Warehouse/Screenshot ....png`.

## 🤖 Churn Model

A **Logistic Regression** model (PySpark MLlib) predicts customer churn from the gold table, using:
- Encoded categorical features (`GENDER`, `NATIONALITY`, `CUSTOMER_CLASS`, `SUBSCRIBER_TYPE`, `TECHNOLOGY_TYPE`, `GOV`)
- Numeric usage/revenue features (tenure, consumption, calls, spend, devices, add-ons, etc.)
- Class-weighting to correct for churn label imbalance
- Grid search over regularization (`regParam`, `elasticNetParam`), evaluated with **ROC-AUC**, **accuracy**, **precision**, **recall**, **F1**

Details and results: [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md#-machine-learning-model).

## 📈 Power BI Dashboard

The dashboard gives an executive view of the customer base: KPIs (customer count, total rent, average tenure, total revenue), demographic breakdowns (gender, customer class, customer type), geographic distribution by governorate and map, and a churn-rate gauge. See the full page-by-page walkthrough in [`docs/POWER_BI.md`]([docs/POWER_BI.md](https://drive.google.com/file/d/16dbDtePzI-QLYRmbHT58p-nODEIqRCcz/view?usp=sharing)).

## ▶️ How to Reproduce

1. Provision an **Azure Databricks** workspace (Unity Catalog enabled) on **Microsoft Azure**.
2. Load the 8 raw tables into a Databricks Volume (`/Volumes/depiworkspace/default/telecom_data`).
3. Run `ETL/bronze to silver.py` to produce the cleaned `*_clean` Delta tables.
4. Run `ETL/silver to gold.py` to build the unified `gold_telecom` table.
5. Run `Data Warehouse/Telecom_DW.sql` to build the star-schema warehouse (`depiworkspace.telecom`).
6. Run `Model.py` to train/evaluate the churn model on `gold_telecom`.
7. Connect Power BI to the Azure Databricks warehouse (or `gold_telecom`) and refresh the dashboard.

## 👥 Team / Credits

Project developed as part of the DEPI Data Engineering track.
