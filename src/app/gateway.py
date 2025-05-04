from fastapi import FastAPI
from config.config import VERSIONS
from src.model.interface import StartReportItem
from .worker_tasks.tasks import *
from ..db_connection import check_connection_status as check_db_connection_status
import logging
app_log = logging.getLogger('app')

app = FastAPI(title="Reports Service API", 
              version=VERSIONS.API,
              root_path="/python/api")

_CALC = ['Calculation functions']
_API = ['API']

app_log.info(f'---------------------- Started Application! ----------------------')
# @app.get("/ver")
# def version_check():
#     return {'api_version':VERSIONS.API,
#             'calculator_version':VERSIONS.CALCULATOR}

@app.get(f"/health", tags=_API)
def health_check():
    statuses = {
        "db_connection_status": check_db_connection_status(),
        "calculator_status": "ok"
    }
    check_result = "good"
    for k,v in statuses.items():
        if v!="ok":
            check_result = "bad"
        
    return {"check_result": check_result, "modules_statuses": statuses}

@app.get("/getStatus/{task_type}/{calc_id}", tags=_API)
async def get_status(task_type: str, calc_id: int):
    match task_type:
        case 'reports_task':
            return {"status": check_reports_task_status(calc_id)}
    return {"status": "error"}

@app.post(f"/{VERSIONS.CALCULATOR}/startCalc", tags=_CALC)
async def add_report_task(item: StartReportItem):
    return start_reports_task(item)

