# mlmodel.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
import joblib

def train_model():
    """
    Trains a multi-output model for supply chain optimization using INR data.
    """
    data = pd.read_csv('mock_historical_data.csv')

    # Define all the new input features for the model
    input_features = [
        'project_location', 'geographic_location', 'tower_type', 'budget_crore_inr', 
        'project_duration_months', 'seasonality_factor', 'material_id', 
        'material_unit_price_inr', 'material_lead_time_days', 
        'supplier_reliability_score', 'service_level_requirement_pct', 
        'inventory_holding_cost_pct', 'transportation_cost_pct', 
        'market_price_volatility', 'resource_availability', 
        'supply_chain_disruption_risk', 'historical_demand_variation_pct'
    ]
    
    # Define all the new output targets the model needs to predict
    output_targets = [
        'eoq', 'reorder_point', 'safety_stock', 'optimal_order_frequency_days', 
        'total_demand_quantity', 'total_supply_chain_cost_inr'
    ]

    X = data[input_features]
    y = data[output_targets]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define which columns are text (categorical) and which are numbers (numeric)
    categorical_features = [
        'project_location', 'geographic_location', 'tower_type', 'seasonality_factor', 
        'material_id', 'market_price_volatility', 'resource_availability'
    ]
    numeric_features = [
        'budget_crore_inr', 'project_duration_months', 'material_unit_price_inr', 
        'material_lead_time_days', 'supplier_reliability_score', 
        'service_level_requirement_pct', 'inventory_holding_cost_pct', 
        'transportation_cost_pct', 'supply_chain_disruption_risk', 
        'historical_demand_variation_pct'
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])

    # Use MultiOutputRegressor to predict multiple values at once
    multi_output_model = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=300, max_features='sqrt', min_samples_leaf=2, random_state=42, n_jobs=-1)
    )

    model_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                     ('regressor', multi_output_model)])
    
    model_pipeline.fit(X_train, y_train)

    print("\n--- Multi-Output Model Performance Evaluation ---")
    y_pred = model_pipeline.predict(X_test)
    r2 = r2_score(y_test, y_pred) # This calculates an average R² score across all outputs

    print(f"✅ Average R-squared (R²): {r2:.4f}")
    print("----------------------------------------------\n")

    # Train the final model on all available data
    model_pipeline.fit(X, y)

    joblib.dump(model_pipeline, 'demand_forecaster.joblib')
    print("✅ Final Multi-Output model trained and saved as demand_forecaster.joblib")

if __name__ == '__main__':
    train_model()