import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder

class DataPreprocessor:
    """
    A utility class to handle common data preprocessing and transformation tasks.
    Provides methods for normalization, encoding, and feature scaling.
    """

    def __init__(self):
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler()
        }
        self.encoders = {
            'onehot': OneHotEncoder()
        }

    def normalize(self, data, method='standard'):
        """
        Normalize the data using either standard or min-max scaling.

        :param data: DataFrame or array-like input data.
        :param method: Scaling method ('standard' or 'minmax').
        :return: Normalized data.
        """
        scaler = self.scalers[method]
        if isinstance(data, pd.DataFrame):
            return pd.DataFrame(scaler.fit_transform(data), columns=data.columns)
        else:
            return scaler.fit_transform(data)

    def encode(self, data, method='onehot'):
        """
        Encode categorical data using one-hot encoding.

        :param data: DataFrame or array-like input data.
        :param method: Encoding method ('onehot').
        :return: Encoded data.
        """
        encoder = self.encoders[method]
        if isinstance(data, pd.DataFrame):
            encoded_data = encoder.fit_transform(data)
            return pd.DataFrame(encoded_data.toarray(), columns=encoder.get_feature_names_out())
        else:
            return encoder.fit_transform(data).toarray()

    def scale_features(self, data, method='standard'):
        """
        Scale the features of the dataset using specified method.

        :param data: DataFrame or array-like input data.
        :param method: Scaling method ('standard' or 'minmax').
        :return: Scaled data.
        """
        return self.normalize(data, method)

    @staticmethod
    def log_transform(data):
        """
        Apply logarithmic transformation to the data.

        :param data: DataFrame or array-like input data.
        :return: Transformed data.
        """
        if isinstance(data, pd.DataFrame):
            return data.apply(lambda x: np.log(x + 1))
        else:
            return np.log(data + 1)

    @staticmethod
    def sqrt_transform(data):
        """
        Apply square root transformation to the data.

        :param data: DataFrame or array-like input data.
        :return: Transformed data.
        """
        if isinstance(data, pd.DataFrame):
            return data.apply(lambda x: np.sqrt(x))
        else:
            return np.sqrt(data)

# Example usage
if __name__ == "__main__":
    # Sample data
    df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': ['a', 'b', 'c', 'd', 'e']
    })

    preprocessor = DataPreprocessor()
    normalized_df = preprocessor.normalize(df[['feature1']])
    encoded_df = preprocessor.encode(df[['feature2']])
    scaled_df = preprocessor.scale_features(df[['feature1']], method='minmax')
    log_transformed_df = preprocessor.log_transform(df[['feature1']])
    sqrt_transformed_df = preprocessor.sqrt_transform(df[['feature1']])

    print("Normalized:\n", normalized_df)
    print("Encoded:\n", encoded_df)
    print("Scaled:\n", scaled_df)
    print("Log Transformed:\n", log_transformed_df)
    print("Square Root Transformed:\n", sqrt_transformed_df)