import pandas as pd

def remove_empty_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove records with empty values in any of its attributes.
    
    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    
    Returns:
    pd.DataFrame: The DataFrame with empty value records removed.
    """
    return df.dropna()

def validate_headers(df: pd.DataFrame) -> bool:
    """
    Check if the first row has a category name for all columns.
    
    Parameters:
    df (pd.DataFrame): The DataFrame to check.
    
    Returns:
    bool: True if all columns have a category name, False otherwise.
    """
    return all(df.columns.notna() & (df.columns != ''))