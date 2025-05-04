from pydantic import BaseModel

class GeneralInfo(BaseModel):
    calc_id: int = 111
    report_date: str = ''
    actual_date: str = ''
    prev_report_date: str = ''

class StartReportItem(BaseModel):
    item: GeneralInfo
    type: str = 'reports_task'