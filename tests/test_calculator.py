import pytest
from app import create_app, db
from app.models.calculation_result import CalculationResult

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_calculate_endpoint(client):
    response = client.post('/api/calculate', json={
        'report_date': '2023-12-31',
        'prev_report_date': '2023-11-30',
        'data_date': '2023-12-31',
        'calc_type': 'IFRS17',
        'calculation_id': 'test_calc_001'
    })
    assert response.status_code == 200
    assert response.json['status'] == 'SUCCESS'

def test_status_endpoint(client):
    with client.application.app_context():
        result = CalculationResult(
            calculation_id='test_calc_002',
            report_date='2023-12-31',
            data={'showcase_path': '/tmp/test.csv'},
            status='SUCCESS'
        )
        db.session.add(result)
        db.session.commit()
    
    response = client.get('/api/status/test_calc_002')
    assert response.status_code == 200
    assert response.json['status'] == 'SUCCESS'