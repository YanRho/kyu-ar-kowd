from fastapi import FastAPI

app = FastAPI(title="Kyu-Ar-API")

@app.get("/")
def read_root():
    return {"message": "Welcome to Kyu-Ar-API"}