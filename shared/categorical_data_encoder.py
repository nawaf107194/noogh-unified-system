import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

class CategoricalDataEncoder:
    """
    Utility class to encode categorical data into numerical formats.
    
    Methods:
        label_encode: Encodes categorical columns using Label Encoding.
        one_hot_encode: Encodes categorical columns using One-Hot Encoding.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def label_encode(self, columns=None):
        """
        Perform label encoding on specified columns or all categorical columns if none provided.
        
        :param columns: List of column names to encode. If None, all categorical columns will be encoded.
        :return: DataFrame with encoded columns.
        """
        le = LabelEncoder()
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns
        
        for col in columns:
            self.df[col] = le.fit_transform(self.df[col])
        return self.df
    
    def one_hot_encode(self, columns=None):
        """
        Perform one-hot encoding on specified columns or all categorical columns if none provided.
        
        :param columns: List of column names to encode. If None, all categorical columns will be encoded.
        :return: DataFrame with encoded columns.
        """
        ohe = OneHotEncoder(sparse=False, handle_unknown='ignore')
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns
        
        encoded_data = ohe.fit_transform(self.df[columns])
        encoded_df = pd.DataFrame(encoded_data, columns=ohe.get_feature_names_out(columns))
        
        # Drop original columns and concatenate encoded columns
        self.df = self.df.drop(columns=columns).join(encoded_df)
        return self.df