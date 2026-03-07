import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class FeatureExtractionUtility:
    def __init__(self, n_components=None, scaler=StandardScaler()):
        self.n_components = n_components
        self.scaler = scaler
        self.pca = PCA(n_components=n_components)
    
    def fit_transform(self, data):
        """
        Fit the model with data and perform dimensionality reduction.
        
        Parameters:
            data (pd.DataFrame): The input data frame containing raw data.
            
        Returns:
            pd.DataFrame: Transformed data with extracted features.
        """
        # Scale the data
        scaled_data = self.scaler.fit_transform(data)
        
        # Apply PCA
        transformed_data = self.pca.fit_transform(scaled_data)
        
        # Convert back to DataFrame
        columns = [f"component_{i+1}" for i in range(transformed_data.shape[1])]
        return pd.DataFrame(transformed_data, columns=columns)
    
    def transform(self, data):
        """
        Perform dimensionality reduction using the fitted model.
        
        Parameters:
            data (pd.DataFrame): The input data frame containing raw data.
            
        Returns:
            pd.DataFrame: Transformed data with extracted features.
        """
        scaled_data = self.scaler.transform(data)
        transformed_data = self.pca.transform(scaled_data)
        columns = [f"component_{i+1}" for i in range(transformed_data.shape[1])]
        return pd.DataFrame(transformed_data, columns=columns)

# Example usage
if __name__ == "__main__":
    # Sample data
    data = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5],
        'feature2': [5, 4, 3, 2, 1],
        'feature3': [2, 3, 4, 5, 6]
    })
    
    # Initialize utility
    feu = FeatureExtractionUtility(n_components=2)
    
    # Fit and transform
    transformed_data = feu.fit_transform(data)
    print(transformed_data)