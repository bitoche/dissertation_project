from pydantic import BaseModel

class StartReportItem(BaseModel):
    calc_id: int = 111
    report_date: str = ''
    actual_date: str = ''
    prev_report_date: str = ''
    type: str = 'reports_task'

