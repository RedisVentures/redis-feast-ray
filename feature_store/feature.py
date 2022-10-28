import os.path as osp

from datetime import timedelta
from entity import (
    zipcode,
    dob_ssn
)
from feast import (
    Field,
    FeatureService,
    FeatureView,
    FileSource
)
from feast.types import (
    Int64,
    String
)

dir_path = osp.dirname(osp.abspath(__file__))
data_path = osp.join(dir_path, "data")

zipcode_batch_source = FileSource(
    path=f"{data_path}/" + "zipcode_table.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

credit_history_source = FileSource(
    path=f"{data_path}/" + "credit_history.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

zipcode_features = FeatureView(
    name="zipcode_features",
    entities=[zipcode],
    ttl=timedelta(days=365*10),
    schema=[
        Field(name="city", dtype=String),
        Field(name="state", dtype=String),
        Field(name="location_type", dtype=String),
        Field(name="tax_returns_filed", dtype=Int64),
        Field(name="population", dtype=Int64),
        Field(name="total_wages", dtype=Int64),
    ],
    source=zipcode_batch_source
)

credit_history = FeatureView(
    name="credit_history",
    entities=[dob_ssn],
    ttl=timedelta(days=365*10),
    schema=[
        Field(name="credit_card_due", dtype=Int64),
        Field(name="mortgage_due", dtype=Int64),
        Field(name="student_loan_due", dtype=Int64),
        Field(name="vehicle_loan_due", dtype=Int64),
        Field(name="hard_pulls", dtype=Int64),
        Field(name="missed_payments_2y", dtype=Int64),
        Field(name="missed_payments_1y", dtype=Int64),
        Field(name="missed_payments_6m", dtype=Int64),
        Field(name="bankruptcies", dtype=Int64),
    ],
    source=credit_history_source
)

zipcode_features_svc = FeatureService(
    name="zipcode_features_svc",
    features=[zipcode_features, credit_history],
    tags={"Description": "Used for training a XGBoost Logistic Regression model"}
)
