import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif

class FeatureSelector:
    def __init__(self, k=10):
        self.k = k
        self.selector = SelectKBest(score_func=f_classif, k=k)

    def fit(self, X, y):
        """
        Fit the selector to the data.
        
        :param X: DataFrame containing the features.
        :param y: Series containing the target variable.
        """
        self.selector.fit(X, y)
        return self

    def transform(self, X):
        """
        Transform the input data using the fitted selector.
        
        :param X: DataFrame containing the features.
        :return: DataFrame with the selected features.
        """
        return pd.DataFrame(self.selector.transform(X), columns=X.columns[self.selector.get_support()])

    def get_selected_features(self, X):
        """
        Get the names of the selected features.
        
        :param X: DataFrame containing the features.
        :return: List of selected feature names.
        """
        return list(X.columns[self.selector.get_support()])

    def fit_transform(self, X, y):
        """
        Fit the selector to the data and transform it.
        
        :param X: DataFrame containing the features.
        :param y: Series containing the target variable.
        :return: DataFrame with the selected features.
        """
        self.fit(X, y)
        return self.transform(X)

# Example usage
if __name__ == "__main__":
    from sklearn.datasets import load_iris
    
    # Load sample data
    data = load_iris()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target)
    
    # Initialize and use FeatureSelector
    fs = FeatureSelector(k=2)
    X_selected = fs.fit_transform(X, y)
    print("Selected Features:", fs.get_selected_features(X))
    print(X_selected.head())