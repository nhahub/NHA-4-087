# Databricks notebook source
df = spark.table("depiworkspace.default.gold_telecom")

# COMMAND ----------

drop_cols = [
    "SERVICE_NUMBER#",
    "SUBSCRIBER_ID#",
    "ACCOUNT_ID#",
    "CUSTOMER_ID#",
    "CABIN_CODE"
]

df = df.drop(*drop_cols)

# COMMAND ----------

train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

# COMMAND ----------

from pyspark.ml.feature import StringIndexer

categorical_cols = [
    "GENDER",
    "NATIONALITY",
    "CUSTOMER_CLASS",
    "SUBSCRIBER_TYPE",
    "TECHNOLOGY_TYPE",
    "GOV"
]

indexers = [
    StringIndexer(
        inputCol=c,
        outputCol=c+"_index",
        handleInvalid="keep"
    )
    for c in categorical_cols
]

# COMMAND ----------

from pyspark.ml import Pipeline
pipeline = Pipeline(stages=indexers)

pipeline_model = pipeline.fit(train_df)

train_df = pipeline_model.transform(train_df)
test_df = pipeline_model.transform(test_df)

# COMMAND ----------

from pyspark.ml.feature import VectorAssembler

numeric_cols = [
    "AGE",
    "TENURE_DAYS",
    "TOTAL_IN_BUNDLE",
    "TOTAL_OUT_BUNDLE",
    "TOTAL_DEVICES",
    "TOTAL_ADDON",
    "TOTAL_TAX",
    "AVG_IN_BUNDLE",
    "NUM_PAYMENTS",
    "TOTAL_CONSUMPTION_MB",
    "AVG_DAILY_CONSUMPTION_MB",
    "TOTAL_CONSUMPTION_RECORDS",
    "TOTAL_MOBILE_ACTIONS",
    "TOTAL_MOBILE_DURATION",
    "AVG_MOBILE_DURATION",
    "TOTAL_CALLS",
    "AVG_CALL_HOUR"
]

# COMMAND ----------

assembler = VectorAssembler(
    inputCols=[c+"_index" for c in categorical_cols] + numeric_cols,
    outputCol="features",
    handleInvalid="skip"
)

train_df = assembler.transform(train_df)
test_df = assembler.transform(test_df)

# COMMAND ----------

from pyspark.sql.functions import when

neg = train_df.filter("CHURN = 0").count()
pos = train_df.filter("CHURN = 1").count()

balance = neg / pos

train_df = train_df.withColumn(
    "classWeightCol",
    when(train_df.CHURN == 1, balance).otherwise(1.0)
)

# COMMAND ----------

from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator(
    labelCol="CHURN",
    metricName="areaUnderROC"
)

param_grid = [
    (0.0,0.0),
    (0.01,0.0),
    (0.0,1.0),
    (0.01,1.0)
]

best_auc = 0
best_model = None
best_params = None

for reg,elastic in param_grid:

    lr = LogisticRegression(
        labelCol="CHURN",
        featuresCol="features",
        weightCol="classWeightCol",
        regParam=reg,
        elasticNetParam=elastic,
        maxIter=100
    )

    model = lr.fit(train_df)

    pred = model.transform(test_df)

    auc = evaluator.evaluate(pred)

    print(f"reg={reg}, elastic={elastic}, AUC={auc:.4f}")

    if auc > best_auc:
        best_auc = auc
        best_model = model
        best_params = (reg,elastic)

print("Best Parameters:",best_params)
print("Best ROC-AUC:",best_auc)

# COMMAND ----------

predictions = best_model.transform(test_df)

# COMMAND ----------

from pyspark.ml.evaluation import MulticlassClassificationEvaluator

accuracy = MulticlassClassificationEvaluator(
    labelCol="CHURN",
    predictionCol="prediction",
    metricName="accuracy"
).evaluate(predictions)

precision = MulticlassClassificationEvaluator(
    labelCol="CHURN",
    predictionCol="prediction",
    metricName="weightedPrecision"
).evaluate(predictions)

recall = MulticlassClassificationEvaluator(
    labelCol="CHURN",
    predictionCol="prediction",
    metricName="weightedRecall"
).evaluate(predictions)

f1 = MulticlassClassificationEvaluator(
    labelCol="CHURN",
    predictionCol="prediction",
    metricName="f1"
).evaluate(predictions)

auc = BinaryClassificationEvaluator(
    labelCol="CHURN",
    metricName="areaUnderROC"
).evaluate(predictions)

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"ROC-AUC  : {auc:.4f}")

# COMMAND ----------

predictions.groupBy("CHURN", "prediction").count().show()