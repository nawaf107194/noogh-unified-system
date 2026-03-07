import pytest
import pandas as pd

def test_merge_price_and_funding_happy_path():
    # Create sample data for price and funding
    index = pd.date_range(start='2023-01-01 00:00', periods=5, freq='H')
    price_data = {'price': [100, 101, 102, 103, 104]}
    funding_data = {'funding_rate': [-0.01, -0.02, -0.03, -0.04, -0.05]}

    price_df = pd.DataFrame(price_data, index=index)
    funding_df = pd.DataFrame(funding_data, index=index)

    merged_df = merge_price_and_funding(price_df, funding_df)

    assert len(merged_df) == 5
    assert not merged_df['funding_rate'].isna().any()
    assert all(merged_df['funding_rate'] == range(-1, -6, -1))

def test_merge_price_and_funding_empty_inputs():
    # Empty price data
    price_df = pd.DataFrame({'price': []}, index=pd.date_range(start='2023-01-01 00:00', periods=5, freq='H'))
    funding_df = pd.DataFrame({'funding_rate': [-0.01, -0.02, -0.03, -0.04, -0.05]})

    merged_df = merge_price_and_funding(price_df, funding_df)
    assert len(merged_df) == 0
    assert 'funding_rate' not in merged_df.columns

    # Empty funding data
    price_df = pd.DataFrame({'price': [100, 101, 102, 103, 104]}, index=pd.date_range(start='2023-01-01 00:00', periods=5, freq='H'))
    funding_df = pd.DataFrame({'funding_rate': []}, index=pd.date_range(start='2023-01-01 00:00', periods=5, freq='H'))

    merged_df = merge_price_and_funding(price_df, funding_df)
    assert len(merged_df) == 5
    assert 'funding_rate' in merged_df.columns

def test_merge_price_and_funding_none_inputs():
    # None price data
    price_df = None
    funding_df = pd.DataFrame({'funding_rate': [-0.01, -0.02, -0.03, -0.04, -0.05]})

    merged_df = merge_price_and_funding(price_df, funding_df)
    assert merged_df is None

    # None funding data
    price_df = pd.DataFrame({'price': [100, 101, 102, 103, 104]}, index=pd.date_range(start='2023-01-01 00:00', periods=5, freq='H'))
    funding_df = None

    merged_df = merge_price_and_funding(price_df, funding_df)
    assert 'funding_rate' not in merged_df.columns

def test_merge_price_and_funding_boundary_conditions():
    # Boundary conditions
    index = pd.date_range(start='2023-01-01 00:00', periods=5, freq='H')
    price_data = {'price': [100, 101, 102, 103, 104]}
    funding_data = {'funding_rate': [-0.01]}

    price_df = pd.DataFrame(price_data, index=index)
    funding_df = pd.DataFrame(funding_data, index=index)

    merged_df = merge_price_and_funding(price_df, funding_df)

    assert len(merged_df) == 5
    assert not merged_df['funding_rate'].isna().any()
    assert all(merged_df['funding_rate'] == [-0.01] * 5)