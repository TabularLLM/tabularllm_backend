import hashlib
import io
import os
import json, requests
import shutil
from contextlib import asynccontextmanager
import uuid
import string

from .prompts import intial_prompt_with_few_shot
from .schemas import AnalysisResponse, provide_example_schema
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .preprocessing.helpers import remove_empty_values, validate_headers, parse_attributes_from_response

TEMP_FOLDER = "_temp"

INVALID_HEADERS_MESSAGE = "Invalid headers in the CSV file."

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Meta prompting for system instructions.
import json

def strip_code_block(text):
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove starting markdown code block marker if present
    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    # Remove trailing markdown code block marker if present
    if text.endswith("```"):
        text = text[:-len("```")].strip()
    return text

def parse_json_response(response):
    # If response is a list, assume the first element contains the JSON text.
    if isinstance(response, list):
        response_text = response[0]
    else:
        response_text = response

    cleaned_text = strip_code_block(response_text)
    # Parse the cleaned JSON string into a dictionary
    return json.loads(cleaned_text)


def get_customized_model(filename: str):
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=(
            "You are an expert data analyst." \
            "Your primary task is to analyze datasets and provide basic statistical data and insights based on the uploaded dataset." \
            "Specifically, you need to identify all attributes in the dataset and determine whether each attribute is numerical or categorical." \
            "For numerical attributes, provide the range of values and calculate an average value." \
            "For categorical attributes, list the possible values. If there are more than five unique values in the dataset, summarize the common options." \
            "Use your domain knowledge and conventions to guide your analysis."
        ),
    )

@app.post("/upload-csv/")  
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()[0:8]

    # UUID
    uuid_part = ''.join([uuid.uuid4().hex[i] for i in range(10)]) 
    filename = f"file-{file_hash}-{uuid_part}".lower().replace("_", "-").strip("-")
    unique_filename = f"{filename}"[:40] 
    print(f"{unique_filename} HERE")
    file_path = f"{TEMP_FOLDER}/{unique_filename}"
    
    # Preprocessing
    
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    if not validate_headers(df):
        return {"error": "Invalid headers in the CSV file."}
    df = remove_empty_values(df)

    # Saving
    with open(file_path, 'wb') as temp_file:
        temp_file.write(contents)

    uploaded_file = genai.upload_file(path=file_path, name=unique_filename, mime_type="text/csv")
    
    # Initial Prompt
    # TODO: SCHEMA SETUP
    response = await get_customized_model(uploaded_file.name).generate_content_async(
        [uploaded_file, intial_prompt_with_few_shot()+provide_example_schema()]
    )

    #File Cleanup
    os.remove(file_path)
    genai.delete_file(uploaded_file.name)
    
    json_formatted =parse_json_response(response.text)
    print(json_formatted)

    return json_formatted
