import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

class DataTransformer:
    def __init__(self, numerical_features=None, categorical_features=None):
        self.numerical_features = numerical_features if numerical_features else []
        self.categorical_features = categorical_features if categorical_features else []

    def create_pipeline(self):
        """Creates a preprocessing pipeline for numerical and categorical data."""
        # Numerical preprocessing: standard scaling
        num_pipeline = Pipeline([
            ('scaler', StandardScaler())
        ])

        # Categorical preprocessing: one-hot encoding
        cat_pipeline = Pipeline([
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', num_pipeline, self.numerical_features),
                ('cat', cat_pipeline, self.categorical_features)
            ]
        )
        
        return preprocessor

    def fit_transform(self, df):
        """Fit and transform the provided DataFrame using the created pipeline."""
        preprocessor = self.create_pipeline()
        preprocessor.fit(df)
        transformed_data = preprocessor.transform(df)
        return transformed_data

    @staticmethod
    def load_data(file_path):
        """Loads data from a CSV file into a DataFrame."""
        return pd.read_csv(file_path)

# Example usage
if __name__ == "__main__":
    transformer = DataTransformer(numerical_features=['age', 'salary'],
                                  categorical_features=['gender', 'education'])
    
    # Load sample data
    df = transformer.load_data('path/to/sample_data.csv')
    
    # Transform data
    transformed_data = transformer.fit_transform(df)
    print(transformed_data)