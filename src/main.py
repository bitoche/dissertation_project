from src.db_connection import check_connection_status
from src.model.interface import GeneralInfo
from src.handlers import timer
from config.config import AppConfig
from src.configurator import read_configuration_file, ReportsConfigurationModel
import logging

app_log = logging.getLogger('app').getChild('rep')
mf_log = app_log.getChild('main')

calc_statuses = {}

class CalcStatus:
    def __init__(self, percent: int, status: str, message: str, calc_id: int):
        self.percent = percent
        self.status = status
        self.message = message
        calc_statuses[calc_id] = self

    def _upd(self, percent: int = None, status: str = None, message: str = None, calc_id: int = None):
        self.percent = percent if percent is not None else self.percent
        self.status = status if status is not None else self.status
        self.message = message if message is not None else self.message
        calc_statuses[calc_id] = self

    def get_dict_status(self):
        return {
            "percent": self.percent,
            "status": self.status,
            "message": self.message
        }

@timer
def start_calc(item: GeneralInfo):
    calc_id = item.calc_id
    report_date = item.report_date
    prev_report_date = item.prev_report_date
    actual_date = item.actual_date
    mf_log.info(f'Started task: (calc_id={calc_id}, report_date={report_date}, prev_report_date={prev_report_date}, actual_date={actual_date})')
    
    _status = CalcStatus(
        percent=1,
        status="in_progress",
        message="started",
        calc_id=calc_id
    )

    if check_connection_status() == "not connected":
        _status._upd(None, "error", "db connection does not exists", calc_id)
        return _status.get_dict_status()


    reports_config_data = read_configuration_file(AppConfig.PROJ_PARAM)
    reports_config = ReportsConfigurationModel(reports_config_data)
    activated_reports = reports_config.activated_reports
    refs_configuration = reports_config.refs
    
    mf_log.info(f"Activated reports: {activated_reports}")
        
    # load configuration
    #
    #

    # update refs if needed
    # if needed update 
    all_ref_names = [ref_name for ref_name,ref_config in refs_configuration.items()]
    percents_by_load_all_refs = 30
    percents_per_ref = (percents_by_load_all_refs - _status.percent) // len(all_ref_names) 
    for ref in all_ref_names:
        _status._upd(_status.percent + percents_per_ref, "in progress", f"processing load ref {ref}", calc_id)
        mf_log.info(f'Started update ref {ref}')
    
    percents_remain = 100 - _status.percent
    percents_per_rep = (percents_remain) // len(activated_reports)
    for rep in activated_reports:
        _status._upd(_status.percent + percents_per_rep, "in progress", f"processing report {rep}", calc_id)
        mf_log.info(f'Started report {ref}')
    _status._upd(100, "successful", "completed", calc_id)
    # except Exception as e:
    #     mf_log.error(f"Calculation failed: {str(e)}")
    #     _status._upd(None, "error", str(e), calc_id)
    return _status.get_dict_status()

def get_calc_status(calc_id: int):
    try:
        status = calc_statuses[calc_id]
        app_log.info(f'Status of {calc_id} calc is {status.get_dict_status()}')
        return status.get_dict_status()
    except KeyError:
        app_log.warning(f'Calculation {calc_id} not found')
        return {"status": "not_found", "message": "Calculation not found"}