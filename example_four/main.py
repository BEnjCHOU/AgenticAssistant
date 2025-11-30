from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
from agent import AgentDocument

app = FastAPI()

# Define request/response models
class Request(BaseModel):
    message: str

# 1. Global Variable for Agent
# This will be initialized BEFORE the API starts accepting requests
agent_instance: AgentDocument = None

# 2. Startup Event Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent_instance
    agent_instance = AgentDocument()
    yield
    # Any cleanup can be done here if necessary

# post question
@app.post("/ask/")
async def ask_question(request: Request):
    """Ask a question to the agent"""
    try:
        agent = AgentDocument()
        response = await agent.get_agent().run(request.message)
        return {"response": response}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# upload new file
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Upload and save a file to the uploads directory"""
    try:
        uploadpath = "data"
        file_path = uploadpath / file.filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Add the new file context to the agent
        agent = AgentDocument()
        agent.add_file_context_to_agent(file.filename)

        return {
            "filename": file.filename,
            "message": "File saved successfully",
            "file_path": str(file_path)
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# update existing file
@app.put("/update/")
async def update_file(file: UploadFile = File(...)):
    """Update an existing file in the uploads directory"""
    try:
        uploadpath = "data"
        file_path = uploadpath / file.filename
        
        # Save the updated file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update the document in the agent
        agent = AgentDocument()
        agent.update_document(str(file_path))

        return {
            "filename": file.filename,
            "message": "File updated successfully",
            "file_path": str(file_path)
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# List all files in the agent
@app.get("/files/")
async def list_files():
    """List all files in the data directory"""
    try:
        uploadpath = "data"
        # for object in path, if it is a file, add file name to files
        files = [f.name for f in uploadpath.iterdir() if f.is_file()]
        return {"files": files}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# delete file from agent
@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    """Delete a file from the data directory and agent"""
    try:
        agent = AgentDocument()
        agent.delete_file(filename)
        return {"filename": filename, "message": "File deleted successfully"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

# find context from agent
# delete context from agent
# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

# GET endpoint
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id, "name": "Sample Item"}

# POST endpoint
@app.post("/items/")
async def create_item(item: Item):
    return {"created": item, "status": "success"}

# PUT endpoint
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, "updated": item}

# DELETE endpoint
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    return {"deleted": item_id, "status": "success"}

# Run with: uvicorn main:app --reload