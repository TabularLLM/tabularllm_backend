import datetime
import hashlib
import io
import os
import pathlib
import shutil
import tempfile
from contextlib import asynccontextmanager

import google.generativeai as genai
import pandas as pd
import pytz
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Request


TEMP_FOLDER = "_temp"

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER)
    yield


app = FastAPI(lifespan=lifespan)


def get_customized_model(filename: str):
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=f"You are an expert data analyst. You will provide basic statistical data and insights based on the attached dataset. Only respond with text related to your analysis.",
    )


@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    file_path = f"{TEMP_FOLDER}/{file.filename}"
    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()[0:8]
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    with open(f'{TEMP_FOLDER}/{file.filename}', 'wb') as temp_file:
        temp_file.write(contents)

    # TODO: Assign a UUID name
    uploaded_file = genai.upload_file(path=file_path, name=f"file-{file_hash}", mime_type="text/csv")
    response = await get_customized_model(uploaded_file.name).generate_content_async(
        [uploaded_file, "Provide the purpose and statistics of the attached data."]
    )
    os.remove(file_path)
    genai.delete_file(uploaded_file.name)
    return {"filename": file.filename, "data": df.to_dict(orient="records"), "summary": response.text}
