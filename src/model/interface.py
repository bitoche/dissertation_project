from pydantic import BaseModel
from datetime import datetime
import logging as _logging
from fastapi import UploadFile
from .file_model_intefrace import *
from src.config.configurator import check_logic_of_configuration
from .file_model_intefrace import MetaFileInfo
logger = _logging.getLogger("app").getChild("validator")

calc_date_fmts = {}

class GeneralInfo(BaseModel):
    calc_id: int
    report_date: str
    actual_date: str
    prev_report_date: str
    def is_valid(self):
        errors = []
        calc_date_fmts[self.calc_id] = {}
        try:
            report_date_obj = datetime.strptime(self.report_date, "%Y-%m-%d").date()
            calc_date_fmts[self.calc_id]['report_date_fmt'] = "%Y-%m-%d"
        except:
            try:
                report_date_obj = datetime.strptime(self.report_date, "%Y-%d-%m").date()
            except:
                errors.append({"by_check":"report_date","message": f'report date ({self.report_date}) does not parsed.'})
            calc_date_fmts[self.calc_id]['report_date_fmt'] = "%Y-%d-%m"
        try:
            prev_report_date_obj = datetime.strptime(self.prev_report_date, "%Y-%m-%d").date()
            calc_date_fmts[self.calc_id]['prev_report_date_fmt'] = "%Y-%m-%d"
        except:
            try:
                prev_report_date_obj = datetime.strptime(self.prev_report_date, "%Y-%d-%m").date()
            except:
                errors.append({"by_check":"prev_report_date","message": f'prev report date ({self.prev_report_date}) does not parsed.'})
            calc_date_fmts[self.calc_id]['prev_report_date_fmt'] = "%Y-%d-%m"
        try:
            actual_date_obj = datetime.strptime(self.actual_date, "%Y-%m-%d").date()
            calc_date_fmts[self.calc_id]['actual_date_fmt'] = "%Y-%m-%d"
        except:
            try:
                actual_date_obj = datetime.strptime(self.actual_date, "%Y-%d-%m").date()
            except:
                errors.append({"by_check":"actual_date","message": f'actual date ({self.report_date}) does not parsed.'})
            calc_date_fmts[self.calc_id]['actual_date_fmt'] = "%Y-%d-%m"
        try:
            if prev_report_date_obj>=report_date_obj:
                errors.append({"by_check": "dates", "message": f'report_date ({self.report_date}) is before or equals prev_report_date ({self.prev_report_date})'})
        except:
            None
        
        if len(errors)>0:
            calc_date_fmts.pop(self.calc_id)
        logger.debug(f'curr date fmts dict:\n{calc_date_fmts}')

        if len(errors)>0:
            return 'bad', errors
        return 'good', []


class StartReportItem(GeneralInfo):
    json_configuration_id: int
    reports_to_calc: list[str] # список отчетов, которые надо рассчитать, должна быть определены в конфигурации. например ["ABC", "XYZ"]
