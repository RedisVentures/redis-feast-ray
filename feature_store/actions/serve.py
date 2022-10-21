import os
import sys
import ray
import pickle
import typing as t
import os.path as osp
import pandas as pd
import xgboost as xgb
from feast import FeatureStore

from ray import serve
from pathlib import Path
from fastapi import FastAPI
from dataclasses import dataclass
from pydantic import BaseModel, Field
from sklearn.preprocessing import OrdinalEncoder
from xgboost_ray import RayParams, RayDMatrix


REPO_PATH = Path(osp.dirname(osp.abspath(__file__))).joinpath("../")
REMOTE_RAY = os.environ.get("RAY_ADDRESS", None)
if REMOTE_RAY:
    # ray.init(address='auto', namespace="serve")

    # option when using Redis to double as a Ray Cluster metadata
    # store for High Availability (HA) clusters
    ray.init(address='auto', namespace="serve", _redis_password="hello")

app = FastAPI()
serve.start(detached=True)


# replicated from schema.py to avoid import troubles
# TODO make this a python package to avoid this.
@dataclass
class FeatureData:

    def __init__(self):
        self.target = "loan_status"
        self.categorical_features = [
            "person_home_ownership",
            "loan_intent",
            "city",
            "state",
            "location_type",
            "dob_ssn",
        ]
        self.columns_to_drop = [
            "event_timestamp",
            "created_timestamp__",
            "loan_id",
            "loan_status",
        ]
        self.zipcode_features = [
            "zipcode_features:city",
            "zipcode_features:state",
            "zipcode_features:location_type",
            "zipcode_features:tax_returns_filed",
            "zipcode_features:population",
            "zipcode_features:total_wages",
            "credit_history:credit_card_due",
            "credit_history:mortgage_due",
            "credit_history:student_loan_due",
            "credit_history:vehicle_loan_due",
            "credit_history:hard_pulls",
            "credit_history:missed_payments_2y",
            "credit_history:missed_payments_1y",
            "credit_history:missed_payments_6m",
            "credit_history:bankruptcies",
        ]

class LoanRequest(BaseModel):
    zipcode: t.List[int]
    person_age: t.List[int]
    person_income: t.List[int]
    person_home_ownership: t.List[str]
    person_emp_length: t.List[float]
    loan_intent: t.List[str]
    loan_amnt: t.List[int]
    loan_int_rate: t.List[float]
    dob_ssn: t.List[str]


@serve.deployment
@serve.ingress(app)
class LoanModel:
    def __init__(self):
        self._store = FeatureStore(repo_path=REPO_PATH)
        self._data_cls = FeatureData()
        self._encoder = OrdinalEncoder()

        model_path = Path(osp.dirname(osp.abspath(__file__))).joinpath("../data/credit_model_xgb.pkl")
        self._read_model(str(model_path))

    def _read_model(self, model_path: str):
        with open(str(model_path), "rb") as f:
            self._model = pickle.load(f)

    @app.get("/loan")
    def predict(self, request: LoanRequest) -> str:
        zipcode_features = self._get_features(request)

        # Join features to request features
        features = request.dict()
        features.update(zipcode_features)
        features_df = pd.DataFrame.from_dict(features)
        features_df = features_df.reindex(sorted(features_df.columns), axis=1)

        # Apply ordinal encoding to categorical features
        features_df = self._apply_ordinal_encoding(features_df)

        # Make prediction
        data = RayDMatrix(data=features_df, enable_categorical=True)
        features_df["prediction"] = self._model.predict(data, ray_params=RayParams(num_actors=1))

        # return result of credit scoring
        return "Approved!" if features_df["prediction"].iloc[0] == 1 else "Rejected"


    def _get_features(self, request):
        zipcode = request.zipcode[0]
        dob_ssn = request.dob_ssn[0]

        return self._store.get_online_features(
            entity_rows=[{"zipcode": zipcode, "dob_ssn": dob_ssn}], features=self._data_cls.zipcode_features
        ).to_dict()


    def _apply_ordinal_encoding(self, data):
        data[self._data_cls.categorical_features] = self._encoder.fit_transform(
            data[self._data_cls.categorical_features])
        return data


# Deploy
LoanModel.options(
    ray_actor_options={"runtime_env": {"pip": ["feast", "xgboost", "pandas"]}}
).deploy()
