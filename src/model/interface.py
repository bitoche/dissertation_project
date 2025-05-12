from pydantic import BaseModel

class GeneralInfo(BaseModel):
    calc_id: int
    report_date: str
    actual_date: str
    prev_report_date: str