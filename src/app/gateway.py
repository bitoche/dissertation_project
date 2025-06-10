from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from config.config import VERSIONS
from config.log_config import setup_logging
from src.model.interface import GeneralInfo
from src.main import start_calc, get_calc_status
from src.tests.database_tests import check_connection_status
from src.model.file_model_intefrace import JSONCrud, MetaFileInfo
from src.config.configurator import check_logic_of_configuration
import logging
import asyncio

setup_logging()

print("Starting gateway.py module import")  # Отладочное сообщение

app_log = logging.getLogger('app')

crud = JSONCrud()

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

from pathlib import Path 
import json
from enum import Enum

class SUPPORTED_FILE_TYPE(Enum):
    CONF = 'conf'
    REF = 'ref'
    CONSTR = 'constr'

@app.post(f"/{VERSIONS.API}/upload_file")
async def upload_file(
    file: UploadFile = File(...),
    file_type: SUPPORTED_FILE_TYPE = Form(...),
    file_desc: str = Form(...)
):
    try:
        meta_info, dataframes = await crud.save_file_with_meta(file, file_type.value, file_desc)

        # Валидация содержимого
        if file_type == SUPPORTED_FILE_TYPE.CONF:
            file_path = Path(meta_info.filename)
            with open(file_path, "r") as f:
                config_data = json.load(f)
            validation_result = check_logic_of_configuration(config_data, ignore_errors=True)
            if validation_result == 'bad':
                # Помечаем файл как неактивный и сохраняем мета-информацию
                meta_info.is_active = False
                crud_instance = JSONCrud()
                crud_instance.update(meta_info.id, meta_info)  # Перезаписываем с is_active=False
                # Удаляем файл из хранилища
                try:
                    file_path.unlink()
                    app_log.info(f"Deleted invalid configuration file: {file_path}")
                except Exception as e:
                    app_log.error(f"Failed to delete invalid configuration file {file_path}: {e}")
                # Формируем ответ с информацией об ошибке
                errors = []  # check_logic_of_configuration не возвращает список ошибок, поэтому заглушка
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid configuration: validation failed. Meta info saved with is_active=False. Errors: {errors}"
                )
        else:
            # Заглушка для валидации ref и constr
            app_log.info(f"Validation for {file_type} is not implemented yet")

        response = {
            "status": "success",
            "meta_info": meta_info.to_dict(),
        }
        
        if dataframes:
            response["sheets"] = {sheet: df.columns.tolist() for sheet, df in dataframes.items()}
        
        return JSONResponse(content=response)
    
    except Exception as e:
        app_log.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post(f"/{VERSIONS.API}/get_all_uploads")
async def get_all_meta(
    file_type: SUPPORTED_FILE_TYPE
):
    try:
        crud = JSONCrud()
        all_info = crud.get_all()
        response = [item.to_dict() for item in all_info if item.file_type == file_type.value]

        return JSONResponse(content=response)
    except Exception as e:
        app_log.error(f'Error get_all_uploads: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post(f"/{VERSIONS.API}/get_upload_by_id")
async def get_meta_by_id(
    upload_id: int
):
    try:
        crud = JSONCrud()
        response = crud.get_by_id(upload_id)
        if response != None:
            response = response.to_dict()
        else:
            response = {
                "status": "not found", 
                "message":f"Meta of file with upload_id={upload_id} not found in file"
                }
        return JSONResponse(content=response)
    except Exception as e:
        app_log.error(f'Error get_upload_by_id: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
