from ...model.interface import StartReportItem
from main import get_calc_status, main_func as start_calc
from . import clr

@clr.task
def start_reports_task(start_report_item: dict):
    item = StartReportItem(**start_report_item)
    return start_calc(item.item)
    # return f"not implemented. recieved:{item}"

def check_reports_task_status(calc_id: int):
    return get_calc_status(calc_id) 
    # return f"not implemented. recieved:{calc_id}"