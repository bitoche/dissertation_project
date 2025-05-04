from fastapi import FastAPI
from config.config import VERSIONS

app=FastAPI()

@app.get("/")
def main():
    return {'api_version':VERSIONS.API,
            'calculator_version':VERSIONS.CALCULATOR}