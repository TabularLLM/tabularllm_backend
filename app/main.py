import io
import pandas as pd
import hashlib
import os
import uuid
from dotenv import load_dotenv

from fastapi import BackgroundTasks, FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from contextlib import asynccontextmanager
from azure.storage.blob import BlobServiceClient
from sqlalchemy.orm import Session

from app.preprocessing.helpers import remove_empty_values, validate_headers
from app.schemas import *
from app.db.blob import save_csv_file, download_csv_file, delete_csv_file
from app.db.db import engine, get_db
from app.db.models import models
from app.db.crud import *

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
blob_service_client = BlobServiceClient.from_connection_string(os.getenv("AZURE_CONNECTION_STRING"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if the uploaded file is a CSV
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()[0:8]

    # UUID
    uuid_part = ''.join([uuid.uuid4().hex[i] for i in range(10)]) 
    filename = f"file-{file_hash}-{uuid_part}".lower().replace("_", "-").strip("-")
    unique_filename = f"{filename}"[:40] 
    print(f"Filename {unique_filename} generated")
    
    # Preprocessing
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV file: {e}")
    
    if not validate_headers(df):
        raise HTTPException(status_code=400, detail="Invalid headers in the CSV file.")
    df = remove_empty_values(df)

    # Combine the entire CSV content into one string (you can customize this)
    combined_text = df.to_string(index=False)

    # Send the combined text to your fine-tuned model using the chat endpoint
    response = client.chat.completions.create(
        model="ft:gpt-4o-2024-08-06:tabularllm::BB9lZEdE",  # Replace with your fine-tuned model ID
        response_format={"type":"json_object"},
        messages=[{"role": "system", "content": "You are an expert data analyst. Your primary task is to analyze datasets and provide basic statistical data and insights based on the uploaded dataset. Specifically, if a question is provided a long side the uploaded dataset you must answer the questions with respects to the dataset using your data analyst skills. BUT if there are no questions provided with the dataset and the dataset is the only item that was provided you must use your data analyst skills to analyze the dataset and provide a json output exactly to this: format{\"count_of_records\": \"int\", \"number_of_numerical_features\": \"int\", \"number_of_categorical_features\": \"int\", \"general_analysis\": \"str\", \"averages_per_numerical_feature\": \"Dict[str, float]\", \"count_of_unique_fields_per_categorical_feature\": \"Dict[str, Dict[str, int]]\", \"data_analyst\": {\"single_data_output\": [{\"label\": \"value\"}], \"graph_data_output\": [{\"Graph_type\": \"str\", \"title\": \"str\", \"x_labels\": \"str[]\", \"multiple_dataset\": \"bool\", \"dataset\": [{\"label\": \"str\", \"data\": \"[int]\"}]}]}} The most IMPORTANT section of the output is the data_analyst section. In this section you must use your data analyst skills extensively to provide at least a minimum of 3 entries for the single_data_output as well as minimum 3 graphs for the graph_data_output. The types of graph you can use are [\"bar\", \"line\", \"doughnut\"]. Feel free to go beyond the minimum of 3 if you believe there should be more based on you data analyst skills. You also need to identify all attributes in the dataset and determine whether each attribute is numerical or categorical. For numerical attributes, provide the range of values and calculate an average value. For categorical attributes, list the possible values. If there are more than five unique values in the dataset, summarize the common options. You must treat all datasets as unique and cannot assume that the attributes are the same across datasets. Use your domain knowledge and conventions to guide your analysis. Be careful to make sure that the analysis you do is correct and that the outputs is correct as well so that any data analyst can look at your output and agree with it. Also be careful to not get numerical and categorical attributes confused. For example if an attributes has only 1's and 0's in its column it is not a numerical attribute instead it is a categorical attribute."},
                  {"role": "user", "content": combined_text}],
        max_tokens=16384,  # Adjust this based on your model's token limit
        temperature=0.75,
    )

    result = response.choices[0].message.content.strip()

    try: 
        await save_csv_file(contents, unique_filename, blob_service_client)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unable to save csv file.")

    try:
        insight = await add_new_insight(db, unique_filename, result, file.filename)
        print(result)
        return(insight)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/chat/")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    insight_id = request.insight_id
    message = request.message
    response = None

    #DB fetch to get current response ID
    db_fetch = await get_insight(db, insight_id)
    if (db_fetch is None):
        raise HTTPException(status_code=404, detail="Invalid insight ID.")
    
    previous_response_id = db_fetch.previous_response_id
    file_id = db_fetch.file_id

    if (previous_response_id is None):
        try: 
            df = await download_csv_file(file_id, blob_service_client)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Unable to fetch csv file. {str(e)}")
        
        combined_text = df.to_string(index=False)

        response = client.responses.create(
            model="ft:gpt-4o-2024-08-06:tabularllm::BB9lZEdE",  # Replace with your fine-tuned model ID
            input=[{"role": "system", "content": "You are an expert data analyst. Your primary task is to analyze datasets and provide basic statistical data and insights based on the uploaded dataset. Specifically, if a question is provided a long side the uploaded dataset you must answer the questions with respects to the dataset using your data analyst skills. BUT if there are no questions provided with the dataset and the dataset is the only item that was provided you must use your data analyst skills to analyze the dataset and provide a json output exactly to this: format{\"count_of_records\": \"int\", \"number_of_numerical_features\": \"int\", \"number_of_categorical_features\": \"int\", \"general_analysis\": \"str\", \"averages_per_numerical_feature\": \"Dict[str, float]\", \"count_of_unique_fields_per_categorical_feature\": \"Dict[str, Dict[str, int]]\", \"data_analyst\": {\"single_data_output\": [{\"label\": \"value\"}], \"graph_data_output\": [{\"Graph_type\": \"str\", \"title\": \"str\", \"x_labels\": \"str[]\", \"multiple_dataset\": \"bool\", \"dataset\": [{\"label\": \"str\", \"data\": \"[int]\"}]}]}} The most IMPORTANT section of the output is the data_analyst section. In this section you must use your data analyst skills extensively to provide at least a minimum of 3 entries for the single_data_output as well as minimum 3 graphs for the graph_data_output. The types of graph you can use are [\"bar\", \"line\", \"doughnut\"]. Feel free to go beyond the minimum of 3 if you believe there should be more based on you data analyst skills. You also need to identify all attributes in the dataset and determine whether each attribute is numerical or categorical. For numerical attributes, provide the range of values and calculate an average value. For categorical attributes, list the possible values. If there are more than five unique values in the dataset, summarize the common options. You must treat all datasets as unique and cannot assume that the attributes are the same across datasets. Use your domain knowledge and conventions to guide your analysis. Be careful to make sure that the analysis you do is correct and that the outputs is correct as well so that any data analyst can look at your output and agree with it. Also be careful to not get numerical and categorical attributes confused. For example if an attributes has only 1's and 0's in its column it is not a numerical attribute instead it is a categorical attribute."},
                    {"role": "user", "content": combined_text + "/n" + message}],
            max_output_tokens=16384,  # Adjust this based on your model's token limit
        )
    else:
        response = client.responses.create(
            model="ft:gpt-4o-2024-08-06:tabularllm::BB9lZEdE",  # Replace with your fine-tuned model ID
            input=[{"role": "system", "content": "You are an expert data analyst. Your primary task is to analyze datasets and provide basic statistical data and insights based on the uploaded dataset. Specifically, if a question is provided a long side the uploaded dataset you must answer the questions with respects to the dataset using your data analyst skills. BUT if there are no questions provided with the dataset and the dataset is the only item that was provided you must use your data analyst skills to analyze the dataset and provide a json output exactly to this: format{\"count_of_records\": \"int\", \"number_of_numerical_features\": \"int\", \"number_of_categorical_features\": \"int\", \"general_analysis\": \"str\", \"averages_per_numerical_feature\": \"Dict[str, float]\", \"count_of_unique_fields_per_categorical_feature\": \"Dict[str, Dict[str, int]]\", \"data_analyst\": {\"single_data_output\": [{\"label\": \"value\"}], \"graph_data_output\": [{\"Graph_type\": \"str\", \"title\": \"str\", \"x_labels\": \"str[]\", \"multiple_dataset\": \"bool\", \"dataset\": [{\"label\": \"str\", \"data\": \"[int]\"}]}]}} The most IMPORTANT section of the output is the data_analyst section. In this section you must use your data analyst skills extensively to provide at least a minimum of 3 entries for the single_data_output as well as minimum 3 graphs for the graph_data_output. The types of graph you can use are [\"bar\", \"line\", \"doughnut\"]. Feel free to go beyond the minimum of 3 if you believe there should be more based on you data analyst skills. You also need to identify all attributes in the dataset and determine whether each attribute is numerical or categorical. For numerical attributes, provide the range of values and calculate an average value. For categorical attributes, list the possible values. If there are more than five unique values in the dataset, summarize the common options. You must treat all datasets as unique and cannot assume that the attributes are the same across datasets. Use your domain knowledge and conventions to guide your analysis. Be careful to make sure that the analysis you do is correct and that the outputs is correct as well so that any data analyst can look at your output and agree with it. Also be careful to not get numerical and categorical attributes confused. For example if an attributes has only 1's and 0's in its column it is not a numerical attribute instead it is a categorical attribute."},
                    {"role": "user", "content": message}],
            max_output_tokens=16384,  # Adjust this based on your model's token limit
            previous_response_id=previous_response_id,
        )
        
    try:
        await update_previous_response_id(db, insight_id, response.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    try:
        await add_new_message(db, message, "input", insight_id)
        await add_new_message(db, response.output_text, "output", insight_id)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    print(response.output_text)
    return (response.output_text)

@app.delete("/insight/delete/{insight_id}/")
async def delete(insight_id: int, db: Session = Depends(get_db)):
    try:
        db_fetch = await get_insight(db, insight_id)
        if (db_fetch is None):
            raise HTTPException(status_code=404, detail="Invalid insight ID.")

        await delete_csv_file(db_fetch.file_id, blob_service_client)
        await delete_insight(db, insight_id)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return JSONResponse("Insight successfully delete")

@app.patch("/insight/rename/")
async def update_name(request: RenameRequest, db: Session = Depends(get_db)):
    try:
        await update_insight_name(db, request.insight_id, request.new_name)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return JSONResponse("Successfully updated insight name")