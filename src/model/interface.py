from pydantic import BaseModel

class StartReportItem(BaseModel):
    calc_id: int
    report_date: str
    prev_report_date: str = None
    actual_date: str = None
    type: str = 'start_report_item'

