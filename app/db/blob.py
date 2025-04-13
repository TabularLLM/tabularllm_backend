import io
from fastapi import File
from azure.storage.blob import BlobServiceClient
import pandas as pd

async def save_csv_file(data, filename: str, service_client: BlobServiceClient):
    try:
        blob_client = service_client.get_blob_client(container="csv-files", blob=filename)
        blob_client.upload_blob(data, overwrite=True)
    except Exception as e:
        raise e
    
    print ({"status": "success", "action": "created", "filename": filename})

async def download_csv_file(filename: str, service_client: BlobServiceClient):
    try:
        blob_client = service_client.get_blob_client(container="csv-files", blob=filename)
        # Download the blob data
        data = blob_client.download_blob().readall()  
        
        # Convert the byte data to a Pandas DataFrame
        csv_string = data.decode('utf-8')  # Decode bytes to string
        df = pd.read_csv(io.StringIO(csv_string))  # Create DataFrame using StringIO

        return df
    
    except Exception as e:
        raise e

async def delete_csv_file(filename: str, service_client: BlobServiceClient):
    try:
        blob_client = service_client.get_blob_client(container="csv-files", blob=filename)
        blob_client.delete_blob()
    except Exception as e:
        raise e
    
    print ({"status": "success", "action": "deleted", "filename": filename})