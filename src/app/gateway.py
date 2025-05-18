from fastapi import FastAPI
from config.config import VERSIONS
from config.log_config import setup_logging
from src.model.interface import GeneralInfo
from src.main import start_calc, get_calc_status
from src.tests.database_tests import check_connection_status
import logging

setup_logging()

print("Starting gateway.py module import")  # Отладочное сообщение


app_log = logging.getLogger('app')
# app_log.info('---------------------- Gateway module loaded ----------------------')

_tags = [
    {
        "name": "calculation",
        "description": VERSIONS.CALCULATOR_COMMENT
    },
    {
        "name": "api"
    }
]

app = FastAPI(title="IFRS17 Reports Service API",
              version=VERSIONS.API,
              root_path="/python/api",
              openapi_tags=_tags,
              description=VERSIONS.API_COMMENT)



app_log.info('---------------------- Started Application! ----------------------')

@app.get("/health", tags=['api'])
def health_check():
    statuses = {
        "db_connection_status": check_connection_status(),
        "calculator_status": "ok"
    }
    check_result = "good" if all(v == "ok" for v in statuses.values()) else "bad"
    return {"check_result": check_result, "modules_statuses": statuses}

@app.get("/getStatus/{calc_id}", tags=['api'])
async def get_status(calc_id: int):
    status = get_calc_status(calc_id)
    return status

@app.post(f"/{VERSIONS.CALCULATOR}/startCalc", tags=['calculation'])
async def start_calculation(item: GeneralInfo):
    check_res = item.is_valid()
    if check_res[0] == 'good':
        app_log.info(f"Received calculation request: {item.model_dump()}")
        result = start_calc(item)
        return result # должен возвращать 'recieved'
    else:
        return check_res[1]