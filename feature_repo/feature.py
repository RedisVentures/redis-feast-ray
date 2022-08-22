import os.path as osp
from pathlib import Path
from datetime import timedelta
from entity import zipcode, dob_ssn
from feast import (
    Feature,
    Field,
    FeatureService,
    ValueType,
    FeatureView,
    FileSource
)

dir_path = osp.dirname(osp.abspath(__file__))
data_path = osp.join(dir_path, "data")

zipcode_batch_source = FileSource(
    path=f"{data_path}/" + "zipcode_table.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp"
)

credit_history_source = FileSource(
    path=f"{data_path}/" + "credit_history.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp"
)

zipcode_features = FeatureView(
    name="zipcode_features",
    entities=["zipcode"],
    ttl=timedelta(days=3650),
    features=[
        Feature(name="city", dtype=ValueType.STRING),
        Feature(name="state", dtype=ValueType.STRING),
        Feature(name="location_type", dtype=ValueType.STRING),
        Feature(name="tax_returns_filed", dtype=ValueType.INT64),
        Feature(name="population", dtype=ValueType.INT64),
        Feature(name="total_wages", dtype=ValueType.INT64),
    ],
    batch_source=zipcode_batch_source,
    online=True,
)

credit_history = FeatureView(
    name="credit_history",
    entities=["dob_ssn"],
    ttl=timedelta(days=365),
    features=[
        Feature(name="credit_card_due", dtype=ValueType.INT64),
        Feature(name="mortgage_due", dtype=ValueType.INT64),
        Feature(name="student_loan_due", dtype=ValueType.INT64),
        Feature(name="vehicle_loan_due", dtype=ValueType.INT64),
        Feature(name="hard_pulls", dtype=ValueType.INT64),
        Feature(name="missed_payments_2y", dtype=ValueType.INT64),
        Feature(name="missed_payments_1y", dtype=ValueType.INT64),
        Feature(name="missed_payments_6m", dtype=ValueType.INT64),
        Feature(name="bankruptcies", dtype=ValueType.INT64),
    ],
    batch_source=credit_history_source,
    online=True
)

zipcode_features_svc = FeatureService(
    name="zipcode_features_svc",
    features=[zipcode_features, credit_history],
    tags={"Description": "Used for training a XGBoost Logistic Regression model"}
)
