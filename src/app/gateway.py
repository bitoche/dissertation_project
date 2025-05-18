from fastapi import FastAPI
from config.config import VERSIONS
from config.log_config import setup_logging
from src.model.interface import GeneralInfo
from src.main import start_calc, get_calc_status
from src.tests.database_tests import check_connection_status
import logging
import asyncio

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

# Словарь для хранения задач и их статусов
calculation_tasks = {}

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
    if calc_id in calculation_tasks:
        task = calculation_tasks[calc_id]
        if task.done():
            try:
                result = task.result()
                return {"status": "completed", "result": result}
            except Exception as e:
                return {"status": "failed", "error": str(e)}
        else:
            return {"status": "in_progress"}
    return {"status": "not_found"}

@app.post(f"/{VERSIONS.CALCULATOR}/startCalc", tags=['calculation'])
async def start_calculation(item: GeneralInfo):
    check_res = item.is_valid()
    if check_res[0] == 'good':
        app_log.info(f"Received calculation request: {item.model_dump()}")
        async def run_calculation(item: GeneralInfo):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: start_calc(item))
            return result
        task = asyncio.create_task(run_calculation(item))
        calculation_tasks[item.calc_id] = task
        return {"status": "recieved"}
    else:
        return check_res[1]

