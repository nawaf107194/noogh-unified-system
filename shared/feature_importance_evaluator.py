import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

class FeatureImportanceEvaluator:
    def __init__(self, model=None, n_repeats=5, random_state=42):
        """
        Initialize the FeatureImportanceEvaluator.
        
        :param model: The machine learning model to use for evaluating feature importance. Defaults to RandomForestClassifier.
        :param n_repeats: Number of times to permute each feature.
        :param random_state: Random state for reproducibility.
        """
        self.model = model if model else RandomForestClassifier(random_state=random_state)
        self.n_repeats = n_repeats
        self.random_state = random_state
    
    def evaluate(self, X, y):
        """
        Evaluate the importance of features in the dataset.
        
        :param X: DataFrame containing the features.
        :param y: Series or array containing the target variable.
        :return: DataFrame with feature names and their importance scores.
        """
        # Fit the model
        self.model.fit(X, y)
        
        # Perform permutation importance
        result = permutation_importance(self.model, X, y, n_repeats=self.n_repeats, random_state=self.random_state)
        
        # Create a DataFrame with feature names and their importance scores
        importance_df = pd.DataFrame({
            'feature': X.columns,
            'importance_mean': result.importances_mean,
            'importance_std': result.importances_std
        })
        
        return importance_df.sort_values(by='importance_mean', ascending=False)
    
    def plot(self, importance_df):
        """
        Plot the feature importance scores.
        
        :param importance_df: DataFrame with feature names and their importance scores.
        """
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.barh(importance_df['feature'], importance_df['importance_mean'])
            ax.set_xlabel('Importance')
            ax.set_title('Feature Importance')
            plt.show()
        except ImportError:
            print("Matplotlib is not installed. Please install it to visualize the results.")

# Example usage
if __name__ == "__main__":
    from sklearn.datasets import load_iris
    iris = load_iris()
    X = pd.DataFrame(iris.data, columns=iris.feature_names)
    y = pd.Series(iris.target)
    
    evaluator = FeatureImportanceEvaluator()
    importance_df = evaluator.evaluate(X, y)
    print(importance_df)
    evaluator.plot(importance_df)