from fastapi import UploadFile
import json
import os
from typing import List, Dict, Optional
from config.config import AppConfig
import logging as _log
from datetime import datetime
import pandas as pd
from pathlib import Path

logger = _log.getLogger('app').getChild('uploader')

class MetaFileInfo:
    def __init__(self, filename: str, file_desc: str, id: int, file_type: str, add_dttm: datetime, is_active: bool = True):
        self.filename = filename
        self.file_desc = file_desc
        self.id = id
        self.file_type = file_type
        self.add_dttm = add_dttm
        self.is_active = is_active

    def to_dict(self) -> Dict:
        """Преобразует объект MetaFileInfo в словарь для сохранения в JSON."""
        return {
            "filename": self.filename,
            "file_desc": self.file_desc,
            "id": self.id,
            "file_type": self.file_type,
            "add_dttm": self.add_dttm.isoformat(),
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MetaFileInfo':
        """Создает объект MetaFileInfo из словаря, загруженного из JSON."""
        return cls(
            filename=data["filename"],
            file_desc=data["file_desc"],
            id=data["id"],
            file_type=data["file_type"],
            add_dttm=datetime.fromisoformat(data["add_dttm"]),
            is_active=data.get("is_active", True)
        )

class FileStorageManager:
    VALID_FILE_TYPES = {"conf", "ref", "constr"}
    VALID_EXTENSIONS = {
        # "conf": ".json",
        "conf": ".yaml",
        "ref": ".xlsx",
        "constr": ".xlsx"
    }

    def __init__(self):
        self.storage_path = Path(AppConfig.UPLOADED_FILES_STORAGE_PATH)
        self._initialize_storage()

    def _initialize_storage(self):
        """Создает директории для хранения файлов по типам."""
        for file_type in self.VALID_FILE_TYPES:
            type_path = self.storage_path / file_type
            type_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ensured: {type_path}")

    def validate_file_type(self, file_type: str) -> bool:
        """Проверяет, является ли тип файла валидным."""
        return file_type in self.VALID_FILE_TYPES

    def validate_file_extension(self, filename: str, file_type: str) -> bool:
        """Проверяет соответствие расширения файла его типу."""
        expected_extension = self.VALID_EXTENSIONS.get(file_type)
        return filename.lower().endswith(expected_extension)

    async def save_file(self, file: UploadFile, file_type: str, file_id: int) -> str:
        """Сохраняет загруженный файл в соответствующую директорию."""
        if not self.validate_file_type(file_type):
            raise ValueError(f"Invalid file type: {file_type}")
        
        if not self.validate_file_extension(file.filename, file_type):
            raise ValueError(f"Invalid file extension for type {file_type}: {file.filename}")

        file_path = self.storage_path / file_type / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File saved: {file_path}")
        return str(file_path)

    def read_excel_to_dataframes(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """Читает XLSX файл и возвращает словарь датафреймов для каждого листа."""
        try:
            xl = pd.ExcelFile(file_path)
            return {sheet_name: xl.parse(sheet_name) for sheet_name in xl.sheet_names}
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {e}")
            raise

class JSONCrud:
    def __init__(self, filename: str = AppConfig.UPLOADED_FILES_META_INFO_FILE_PATH):
        self.filename = filename
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([], f)
        self.storage_manager = FileStorageManager()

    def create(self, item: MetaFileInfo) -> MetaFileInfo:
        """Создает новый объект и добавляет его в JSON файл."""
        logger.info(f'Started create new entry in json with id {item.id}')
        item_dict = item.to_dict()
        if "id" not in item_dict:
            raise ValueError("Item must have an id")
        
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        if any(existing["id"] == item_dict["id"] for existing in data):
            raise ValueError(f"Item with id {item_dict['id']} already exists")
        
        data.append(item_dict)
        
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)
        
        return item

    def get_all(self) -> List[MetaFileInfo]:
        """Возвращает список всех активных объектов."""
        logger.info(f'Started get all entries from json')
        with open(self.filename, "r") as f:
            data = json.load(f)
        return [MetaFileInfo.from_dict(item) for item in data if item.get("is_active", True)]

    def get_by_id(self, item_id: int) -> MetaFileInfo:
        """Возвращает активный объект по его id."""
        item_id = int(item_id)
        logger.info(f'Started get by id = {item_id} from metafile')
        with open(self.filename, "r") as f:
            data = json.load(f)
        for item in data:
            logger.debug(f'checking "{item}"')
            if item["id"] == item_id:
                if item.get("is_active", True):
                    return MetaFileInfo.from_dict(item)
                else:
                    logger.warning(f"Item with id {item_id} inactive - DELETED")
                    break
        logger.warning(f"Item with id {item_id} not found in metafile")
        return None
        # raise ValueError(f"Item with id {item_id} not found or inactive")

    def update(self, item_id: int, updated_item: MetaFileInfo) -> MetaFileInfo:
        """Обновляет объект по его id."""
        logger.info(f'Started update by id = {item_id} in json')
        updated_dict = updated_item.to_dict()
        if "id" not in updated_dict or updated_dict["id"] != item_id:
            raise ValueError("ID in item must match the provided id")
        
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        for i, item in enumerate(data):
            if item["id"] == item_id:
                data[i] = updated_dict
                with open(self.filename, "w") as f:
                    json.dump(data, f, indent=4)
                return updated_item
        raise ValueError(f"Item with id {item_id} not found")

    def delete(self, item_id: int) -> MetaFileInfo:
        """Помечает объект как неактивный (is_active = False) по его id."""
        logger.info(f'Started disable by id = {item_id} in json')
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        for i, item in enumerate(data):
            if item["id"] == item_id:
                if not item.get("is_active", True):
                    raise ValueError(f"Item with id {item_id} is already inactive")
                item["is_active"] = False
                with open(self.filename, "w") as f:
                    json.dump(data, f, indent=4)
                return MetaFileInfo.from_dict(item)
        return None
        # raise ValueError(f"Item with id {item_id} not found")
    
    def get_next_file_id(self) -> int:
        """Возвращает следующий доступный уникальный id на основе максимального id в JSON."""
        logger.info(f'Started getting next file id from json')
        with open(self.filename, "r") as f:
            data = json.load(f)
        
        if not data:
            return 1
        max_id = max(item["id"] for item in data if "id" in item)
        return max_id + 1

    async def save_file_with_meta(self, file: UploadFile, file_type: str, file_desc: str) -> tuple[MetaFileInfo, Optional[Dict[str, pd.DataFrame]]]:
        """Сохраняет файл и его мета-информацию, возвращает MetaFileInfo и датафреймы для XLSX."""
        file_id = self.get_next_file_id()
        saved_path = await self.storage_manager.save_file(file, file_type, file_id)
        
        meta_info = MetaFileInfo(
            filename=saved_path,
            file_desc=file_desc,
            id=file_id,
            file_type=file_type,
            add_dttm=datetime.now()
        )
        self.create(meta_info)
        
        dataframes = None
        if file_type in ["ref", "constr"]:
            dataframes = self.storage_manager.read_excel_to_dataframes(saved_path)
        
        return meta_info, dataframes

# Обновленные функции с использованием JSONCrud
def get_next_file_id():
    crud = JSONCrud()
    return crud.get_next_file_id()

def get_file_by_id(id: int):
    try:
        crud = JSONCrud()
        return crud.get_by_id(id)
    except ValueError:
        return None

def delete_file_by_id(id: int):
    if get_file_by_id(id) is not None:
        crud = JSONCrud()
        crud.delete(id)