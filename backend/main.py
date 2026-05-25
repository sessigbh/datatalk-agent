import uvicorn
from fastapi import FastAPI
from backend.app.api.routes import router

app = FastAPI(title="DataTalk Agent")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
