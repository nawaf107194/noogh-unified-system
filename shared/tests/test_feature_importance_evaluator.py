import pytest
from shared.feature_importance_evaluator import FeatureImportanceEvaluator

@pytest.fixture
def evaluator():
    return FeatureImportanceEvaluator()

def test_plot_happy_path(evaluator):
    importance_df = {
        'feature': ['feat1', 'feat2', 'feat3'],
        'importance_mean': [0.9, 0.8, 0.7]
    }
    importance_df = pd.DataFrame(importance_df)
    
    # Mock plt.show to not block execution
    with patch('matplotlib.pyplot.show') as mock_show:
        evaluator.plot(importance_df)
        assert mock_show.call_count == 1

def test_plot_edge_case_empty_dataframe(evaluator):
    importance_df = pd.DataFrame(columns=['feature', 'importance_mean'])
    
    # Mock plt.show to not block execution
    with patch('matplotlib.pyplot.show') as mock_show:
        evaluator.plot(importance_df)
        assert mock_show.call_count == 0

def test_plot_edge_case_none_input(evaluator):
    importance_df = None
    
    # Mock plt.show to not block execution
    with patch('matplotlib.pyplot.show') as mock_show:
        evaluator.plot(importance_df)
        assert mock_show.call_count == 0

def test_plot_error_case_invalid_input_type(evaluator):
    importance_df = 'not a DataFrame'
    
    try:
        evaluator.plot(importance_df)
    except Exception as e:
        assert str(e) == "Matplotlib is not installed. Please install it to visualize the results."

def test_plot_error_case_matplotlib_not_installed(evaluator, monkeypatch):
    with monkeypatch.raises(ImportError):
        import matplotlib.pyplot