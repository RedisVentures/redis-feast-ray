import os
import sys
import ray
import time
import pandas as pd
import os.path as osp

from pathlib import Path
from feast import FeatureStore
from sklearn.model_selection import train_test_split
from xgboost_ray import RayXGBClassifier, RayParams, train, RayDMatrix

# add feature_repo path to PYTHONPATH
sys.path.insert(0, "../")

from utils.data_fetcher import DataFetcher
from actions.train import CreditXGBClassifier


RAY_ACTORS=1
RAY_CPU_PER_ACTOR=1
REMOTE_RAY = os.environ.get("RAY_ADDRESS", None)

if REMOTE_RAY:
    # ray.init(address='auto')
    # option when using Redis to double as a Ray Cluster metadata
    # store for High Availability (HA) clusters
    ray.init(address='auto', _redis_password="hello")
    RAY_ACTORS=5
    RAY_CPU_PER_ACTOR=4


class CreditRayXGBClassifier(CreditXGBClassifier):

    def __init__(self, fs, data_fetcher):
        super(CreditRayXGBClassifier, self).__init__(fs, data_fetcher)
        # Create an instance of the classifier
        self._model = RayXGBClassifier(
                    n_jobs=RAY_ACTORS,  # In XGBoost-Ray, n_jobs sets the number of actors
                    random_state=42
        )
        self._ray_params = RayParams(num_actors=RAY_ACTORS, cpus_per_actor=RAY_CPU_PER_ACTOR)

    def train(self) -> None:

        X_train, X_test, y_train, y_test = train_test_split(self._train_X, self._train_y, random_state=42)

        # use RayDMatrix for xgboost
        dtrain = RayDMatrix(data=X_train, label=y_train, enable_categorical=True)
        dtest = RayDMatrix(data=X_test, label=y_test, enable_categorical=True)

        # training and testing - numpy matrices
        bst = self._model.fit(X_train,y_train, ray_params=self._ray_params)

        pred_ray = bst.predict(X_test)
        print(f" predictions: {pred_ray}")

        # save the trained model
        self._trained_model = bst

    def predict(self, request):
        # Get Zipcode features from Feast
        zipcode_features = self._get_online_zipcode_features(request)

        # Join features to request features
        features = request.copy()
        features.update(zipcode_features)
        features_df = pd.DataFrame.from_dict(features)

        # Sort columns
        features_df = features_df.reindex(sorted(features_df.columns), axis=1)

        # Apply ordinal encoding to categorical features
        self._apply_ordinal_encoding(features_df)

        # Make prediction
        features_df["prediction"] = self.trained_model.predict(
                features_df,
                ray_params=RayParams(num_actors=1) # can't shard 1 piece of data over multiple actors
            )

        # return result of credit scoring
        return features_df["prediction"].iloc[0]


if __name__ == '__main__':
    REPO_PATH = Path(osp.dirname(osp.abspath(__file__))).joinpath("../")
    store = FeatureStore(repo_path=REPO_PATH)
    fetcher = DataFetcher(store, REPO_PATH)
    xgboost_cls = CreditRayXGBClassifier(store, fetcher)

    start = time.time()
    # Train the model
    xgboost_cls.train()

    loan_requests = [
        {
            "zipcode": [76104],
            "person_age": [22],
            "person_income": [59000],
            "person_home_ownership": ["RENT"],
            "person_emp_length": [123.0],
            "loan_intent": ["PERSONAL"],
            "loan_amnt": [35000],
            "loan_int_rate": [16.02],
            "dob_ssn": ["19530219_5179"]
        },
        {
            "zipcode": [69033],
            "person_age": [66],
            "person_income": [42000],
            "person_home_ownership": ["RENT"],
            "person_emp_length": [2.0],
            "loan_intent": ["MEDICAL"],
            "loan_amnt": [6475],
            "loan_int_rate": [9.99],
            "dob_ssn": ["19960703_3449"]
        }
    ]

    # Now do the predictions
    for loan_request in loan_requests:
        result = round(xgboost_cls.predict(loan_request))
        loan_status = "approved" if result == 1 else "rejected"
        print(f"Loan for {loan_request['zipcode'][0]} code {loan_status}: status_code={result}")

    elapsed = round(time.time() - start)
    print(f"Total time elapsed: {elapsed} sec")

    xgboost_cls.save("../data", "credit_model_xgb.pkl")