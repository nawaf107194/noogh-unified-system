import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

class DataTransformationUtility:
    def __init__(self, normalize=True, encode_categorical=True, impute_missing=True):
        self.normalize = normalize
        self.encode_categorical = encode_categorical
        self.impute_missing = impute_missing
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.imputer = SimpleImputer(strategy='mean')

    def fit_transform(self, df):
        if self.normalize:
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            df[numerical_cols] = self.scaler.fit_transform(df[numerical_cols])
        
        if self.encode_categorical:
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
        
        if self.impute_missing:
            df = pd.DataFrame(self.imputer.fit_transform(df), columns=df.columns)
        
        return df

    def transform(self, df):
        if self.normalize:
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            df[numerical_cols] = self.scaler.transform(df[numerical_cols])
        
        if self.encode_categorical:
            for col, le in self.label_encoders.items():
                df[col] = le.transform(df[col].astype(str))
        
        if self.impute_missing:
            df = pd.DataFrame(self.imputer.transform(df), columns=df.columns)
        
        return df

# Example usage
if __name__ == "__main__":
    df = pd.DataFrame({
        'age': [25, np.nan, 30],
        'gender': ['male', 'female', 'male'],
        'income': [50000, 60000, np.nan]
    })
    
    dtu = DataTransformationUtility(normalize=True, encode_categorical=True, impute_missing=True)
    transformed_df = dtu.fit_transform(df)
    print(transformed_df)