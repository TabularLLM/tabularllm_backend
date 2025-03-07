from pydantic import BaseModel, ConfigDict
from collections.abc import Mapping
from typing import List, Dict

class AnalysisResponse(BaseModel):
    count_of_records: int
    number_of_numerical_features: int
    number_of_categorical_features: int
    general_analysis: str
    averages_per_numerical_feature: Dict[str, float]
    count_of_unique_fields_per_categorical_feature: Dict[str, Dict[str, int]]
    model_config = ConfigDict(extra='allow')

def provide_example_schema():

    example_schema = "The response must be a json format of the following: count_of_records: int \
        number_of_numerical_features: int \
        number_of_categorical_features: int \
        general_analysis: str \
        averages_per_numerical_feature: Dict[str, float] \
        count_of_unique_fields_per_categorical_feature: Dict[str, Dict[str, int]]\
        The number of categorical features should match the number of features in count_of_unique_fields_per_categorical_feature. \
        and the number of numerical features should match the number of features in averages_per_numerical_feature. Ensure that that is consistent."

    return example_schema