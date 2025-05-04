# from src.app.gateway import app
from src.db_connection import get_connection_row
from src.model.interface import GeneralInfo
from src.handlers import get_param

calc_statuses = {}
class CalcStatus():
    percent: int
    status: str
    message: str
    def __init__(self, percent:int, status:str, message:str, calc_id:int):
        global calc_statuses
        self.percent = percent
        self.status = status
        self.message = message
        calc_statuses[calc_id] = self
    def _upd(self, percent:int = None, status:str = None, message:str = None, calc_id:int = None):
        global calc_statuses
        if get_param(None, calc_statuses, [calc_id]) is not None:
            self.percent = percent if percent is not None else self.percent
            self.status = status if status is not None else self.status
            self.message = message if message is not None else ""
            calc_statuses[calc_id] = self
    def get_dict_status(self):
        return {
            "percent": self.percent,
            "status": self.status,
            "message": self.message
        }


def main_func(item: GeneralInfo):
    calc_id = item.calc_id
    report_date = item.report_date
    prev_report_date = item.prev_report_date
    actual_date = item.actual_date

    _status = CalcStatus(
        percent=1, 
        status="in_progress", 
        message="started",
        calc_id=calc_id
    )

    # load configuration
    # upgrade refs?
    ## upgrade refs
    # for active report in config
    ## actions

    _status._upd(100, "successful", "completed", calc_id)

    return _status.get_dict_status()

def get_calc_status(calc_id:int):
    global calc_statuses
    found = get_param("not found", calc_statuses, [calc_id])
    return found.get_dict_status() if found != "not found" else found