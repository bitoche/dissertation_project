from fastapi import FastAPI
from config.config import VERSIONS
from src.model.interface import StartReportItem

app=FastAPI()


# @app.get("/ver")
# def version_check():
#     return {'api_version':VERSIONS.API,
#             'calculator_version':VERSIONS.CALCULATOR}

@app.get(f"/{VERSIONS.API}/health")
def health_check():
    return {"status": "ok"}

@app.post(f"/{VERSIONS.CALCULATOR}/startCalc")
def add_report_task(item: StartReportItem):
    pass