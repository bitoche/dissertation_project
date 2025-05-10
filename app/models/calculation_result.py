from app import db

class CalculationResult(db.Model):
    __tablename__ = 'calculation_results'
    id = db.Column(db.Integer, primary_key=True)
    calculation_id = db.Column(db.String(50), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False)