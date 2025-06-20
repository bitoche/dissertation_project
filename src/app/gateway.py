from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
import os
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
    },
    {
        "name": "file_manager",
        "description": "upload, inspect, delete files from module storage"
    }
]

app = FastAPI(title="IFRS17 Reports Service API",
              version=VERSIONS.API,
              root_path=f"/python/api",
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

@app.post(f"/startCalc/{VERSIONS.CALCULATOR}", tags=['calculation'])
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
import yaml
from enum import Enum

class SUPPORTED_FILE_TYPE(Enum):
    CONF = 'conf'
    REF = 'ref'
    CONSTR = 'constr'

@app.post(f"/upload_file", tags=['file_manager'])
async def upload_file(
    file: UploadFile = File(...),
    file_type: SUPPORTED_FILE_TYPE = Form(...),
    file_desc: str = Form(...)
):
    try:
        meta_info, dataframes = await crud.save_file_with_meta(file, file_type.value, file_desc)

        file_path = Path(meta_info.filename)

        # Валидация содержимого
        if file_type == SUPPORTED_FILE_TYPE.CONF:
            app_log.info(f"Started validation for loaded configuration: {meta_info.filename}")
            with open(file_path, "r") as f:
                # config_data = json.load(f)
                config_data = yaml.safe_load(f)
            validated = True if check_logic_of_configuration(config_data, ignore_errors=True)=='ok' else False
        elif file_type == SUPPORTED_FILE_TYPE.CONSTR:
            app_log.info(f"Started validation for loaded constructor: {meta_info.filename}")
            validated = False
            # легкая валидация на основе названий листов
            if "constructor" in dataframes.keys():
                validated = True
        else:
            app_log.info(f"Started validation for loaded ref: {meta_info.filename}")
            validated = False
            # легкая валидация на основе названий листов
            if "ref" in dataframes.keys():
                validated = True
        if validated:
            response = {
                "status": "success",
                "message": "validated",
                "saved_meta": meta_info.to_dict(),
            }
        else:
            # Помечаем файл как неактивный и сохраняем мета-информацию
            meta_info.is_active = False
            crud_instance = JSONCrud()
            crud_instance.update(meta_info.id, meta_info)  # Перезаписываем с is_active=False
            # Удаляем файл из хранилища
            try:
                file_path.unlink()
                app_log.info(f"Deleted invalid file: {file_path}")
            except Exception as e:
                app_log.error(f"Failed to delete invalid file {file_path}: {e}")
            response = {
                "status": "error",
                "message": "not validated",
                "saved_meta": meta_info.to_dict()
            }
        
        if dataframes:
            response["sheets_with_columns"] = {sheet: df.columns.tolist() for sheet, df in dataframes.items()}
        
        return JSONResponse(content=response)
    
    except Exception as e:
        app_log.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"/get_all_uploads", tags=['file_manager'])
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

@app.get("/get_upload_by_id/{upload_id}", tags=['file_manager'])
async def get_meta_by_id(
    upload_id: int
):
    try:
        crud = JSONCrud()
        response = crud.get_by_id(upload_id)
        if response != None:
            meta = response.to_dict()
            response = {} 
            response["status"] = "successful"
            response["meta"] = meta
        else:
            response = {
                "status": "not found", 
                "message":f"Meta of file with upload_id={upload_id} not found in file"
                }
        return JSONResponse(content=response)
    except Exception as e:
        app_log.error(f'Error get_upload_by_id: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/drop_file_by_id", tags=['file_manager'])
async def drop_uploaded_file_by_id(
    file_upload_id: int
):
    try:
        crud = JSONCrud()
        
        deleted = crud.delete(file_upload_id)
        
        response = {}
        if deleted != None:
            response["status"] = "successful"
            response["meta"] = deleted.to_dict()
            # Удаляем файл из хранилища
            try:
                file_path = Path(deleted.filename)
                file_path.unlink()
                app_log.info(f"Deleted valid uploaded file: {file_path}")
            except Exception as e:
                response["message"] = f"WARNING! FILE NOT DELETED BY ERROR! CHECK LOGS FOR MORE INFO."
                app_log.error(f"Failed to delete valid uploaded file {file_path}: {e}")
        else:
            response["status"] = "error"
            response["message"] = f"Not found file_upload_id={file_upload_id} in file"
        return JSONResponse(content=response)
    except Exception as e:
        app_log.error(f'Error drop_file_by_id: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download", tags=['file_manager'])
async def download_file(file_id: int):
    crud = JSONCrud()
    founded_file = crud.get_by_id(file_id)
    if founded_file != None:
        file_path = Path(founded_file.filename)
        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=file_path.name,
                media_type="application/octet-stream" # универсальный тип
            )
    return {"error": "File not found"}