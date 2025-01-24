import hashlib
import io
import os
import shutil
from contextlib import asynccontextmanager

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .preprocessing.helpers import remove_empty_values, validate_headers

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


def get_customized_model(filename: str):
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=f"You are an expert data analyst. You will provide basic statistical data and insights based on the attached dataset. First identify the attributes in the dataset and assign either a numerical or categorical value to each attribute. If categorical, provide a list of possible values. If numerical, provide the range of values and an average value. Check the internet to see if the possible values match convention.",
    )


async def get_genai_summary(file_path, file_hash):
    # TODO: Assign a UUID name
    uploaded_file = genai.upload_file(path=file_path, name=f"file-{file_hash}", mime_type="text/csv")
    response = await get_customized_model(uploaded_file.name).generate_content_async(
        [uploaded_file,
         "Provide a list of attributes found in the uploaded file. Assign either a numerical or categorical value to each attribute. If categorical, provide a list of possible values. If numerical, provide the range of values and an average value."],
    )
    genai.delete_file(uploaded_file.name)
    return response


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    file_path = f"{TEMP_FOLDER}/{file.filename}"
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()[0:8]
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    # Validate headers
    if not validate_headers(df):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_HEADERS_MESSAGE)

    # Remove records with empty values
    df = remove_empty_values(df)

    with open(f'{TEMP_FOLDER}/{file.filename}', 'wb') as temp_file:
        temp_file.write(contents)

<<<<<<< HEAD
    # TODO: Assign a UUID name
    uploaded_file = genai.upload_file(path=file_path, name=f"file-{file_hash}", mime_type="text/csv")
    response = await get_customized_model(uploaded_file.name).generate_content_async(
        [uploaded_file, "Rememeber your system instructions. Give me a summery of the attibutes of the dataset, identify the numerical and categorical values."],
    )
=======
    response = await get_genai_summary(file_path, file_hash)
>>>>>>> 734ca7a0dde85c5b851b722fba028cb4365215ef
    os.remove(file_path)

    return {"filename": file.filename, "data": df.to_dict(orient="records"), "summary": response.text}
