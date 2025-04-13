from typing import List, Dict, Union
from pydantic import BaseModel

class DataSet(BaseModel):
    label: str
    data: List[Union[int, float, str]]

class GraphDataOutput(BaseModel):
    Graph_type: str
    title: str
    x_labels: List[str]
    multiple_dataset: bool
    dataset: List[DataSet]

class DataAnalyst(BaseModel):
    single_data_output: List[Dict[str, float]]
    graph_data_output: List[GraphDataOutput]

class MainModel(BaseModel):
    count_of_records: int
    number_of_numerical_features: int
    number_of_categorical_features: int
    general_analysis: str
    averages_per_numerical_feature: Dict[str, float]
    count_of_unique_fields_per_categorical_feature: Dict[str, Dict[str, int]]
    data_analyst: DataAnalyst

class ChatRequest(BaseModel):
    insight_id: int
    message: str

class RenameRequest(BaseModel):
    insight_id: int
    new_name: str
