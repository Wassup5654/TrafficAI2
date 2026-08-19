import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import joblib

# Load training data
df = pd.read_csv("ml/traffic_training_data.csv")
print("Training dataset loaded!")
print(f"Rows: {len(df)}")
print()

# Features (same for all models)
X = df[["location", "road_type", "speed_limit", "lanes", "aadt", 
        "historical_crashes_2yr", "hour", "day_of_week", "is_weekend", 
        "temperature", "humidity", "precipitation", "wind_speed", ]]

# Targets to train
targets = ["current_speed", "free_flow_speed", "temperature", "humidity", 
           "precipitation", "wind_speed",]

print("Training models...")
print()

for target in targets:
    Y = df[target]
    
    # Split data
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
    
    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("onehot", OneHotEncoder(handle_unknown="ignore"), ["location", "road_type"])
        ],
        remainder="passthrough"
    )
    
    # Pipeline
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RandomForestRegressor(n_estimators=100, random_state=42))
        ]
    )
    
    # Train
    pipeline.fit(X_train, Y_train)
    
    # Evaluate
    predictions = pipeline.predict(X_test)
    mae = mean_absolute_error(Y_test, predictions)
    r2 = r2_score(Y_test, predictions)
    
    print(f"{target:20} | MAE: {mae:7.2f} | R²: {r2:6.3f}")
    
    # Save
    joblib.dump(pipeline, f"ml/traffic_{target}_model.pkl")

print()
print("All models trained and saved in ml/ folder!")