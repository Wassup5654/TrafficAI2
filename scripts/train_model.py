import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import joblib


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "ml",
    "traffic_training_data.csv"
)


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(DATA_PATH)

print("Training dataset loaded!")
print(f"Rows: {len(df)}")
print()


# ============================================================
# INPUT FEATURES
# ============================================================

X = df[
    [
        "location",
        "road_type",
        "speed_limit",
        "lanes",
        "aadt",
        "historical_crashes_2yr",
        "hour",
        "day_of_week",
        "is_weekend",
        "previous_speed",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
    ]
]


# ============================================================
# TARGETS
# ============================================================

targets = [
    "current_speed",
    "free_flow_speed",
    "temperature",
    "humidity",
    "precipitation",
    "wind_speed",
    "next_speed",
]


# ============================================================
# TRAIN EACH MODEL
# ============================================================

print("Training models...")
print()


for target in targets:

    print(f"Training {target} model...")

    Y = df[target]


    # --------------------------------------------------------
    # Split data
    # --------------------------------------------------------

    X_train, X_test, Y_train, Y_test = train_test_split(
        X,
        Y,
        test_size=0.2,
        random_state=42
    )


    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                [
                    "location",
                    "road_type"
                ]
            )
        ],
        remainder="passthrough"
    )


    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor
            ),

            (
                "model",
                RandomForestRegressor(
                    n_estimators=100,
                    random_state=42
                )
            )
        ]
    )


    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    pipeline.fit(
        X_train,
        Y_train
    )


    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )


    mae = mean_absolute_error(
        Y_test,
        predictions
    )


    r2 = r2_score(
        Y_test,
        predictions
    )


    print(
        f"{target:20} | "
        f"MAE: {mae:7.2f} | "
        f"R²: {r2:6.3f}"
    )


    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    if target == "next_speed":

        model_name = (
            "traffic_next_speed_model.pkl"
        )

    else:

        model_name = (
            f"traffic_{target}_model.pkl"
        )


    model_path = os.path.join(
        PROJECT_ROOT,
        "ml",
        model_name
    )


    joblib.dump(
        pipeline,
        model_path
    )


    print(
        f"Saved: {model_name}"
    )

    print()


# ============================================================
# FINISHED
# ============================================================

print(
    "All models trained and saved in ml/!"
)