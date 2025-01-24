import hashlib
import io
import os
import shutil
from contextlib import asynccontextmanager
import uuid
import string

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
        [uploaded_file, 
         "Provide a list of attributes found in the uploaded file. \
         Assign either a numerical or categorical value to each attribute. \
         If categorical, provide a list of possible values. \
        If numerical, provide the range of values and an average value."]
    )

    #File Cleanup
    os.remove(file_path)
    genai.delete_file(uploaded_file.name)
    
    return {
        "filename": file.filename,
        "data": df.to_dict(orient="records"),
        "summary": response.text
    }
