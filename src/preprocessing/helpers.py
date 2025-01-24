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

def parse_attributes_from_response(response_text):
    """
    Parses the response from the first step to extract attributes and their types.

    Expected Response Format:
    - "Attribute: Age, Type: Numerical"
    - "Attribute: Gender, Type: Categorical"
    """
    attributes = []
    for line in response_text.split("\n"):
        if "Attribute:" in line and "Type:" in line:
            parts = line.split(",")
            attribute_name = parts[0].split(":")[1].strip()
            attribute_type = parts[1].split(":")[1].strip().lower()
            attributes.append({"name": attribute_name, "type": attribute_type})
    return attributes
