import pytest
import os
import json
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_calculate_endpoint(client, tmp_path):
    # Мокаем config.json
    config = {
        'paths': {
            'input': str(tmp_path),
            'output': str(tmp_path),
            'scripts': str(tmp_path)
        },
        'db_connection': {},
        'queries': {'input_data': 'SELECT 1'},
        'logging': {'level': 'INFO', 'file': str(tmp_path / 'calculator.log')}
    }
    with open(tmp_path / 'config.json', 'w') as f:
        json.dump(config, f)
    
    # Мокаем calc_type.json
    with open(tmp_path / 'IFRS17.json', 'w') as f:
        json.dump({'id': 'test'}, f)
    
    response = client.post('/api/calculate', json={
        'report_date': '2023-12-31',
        'prev_report_date': '2023-11-30',
        'data_date': '2023-12-31',
        'calc_type': 'IFRS17',
        'calculation_id': 'test_calc_001'
    })
    assert response.status_code == 500  # Ожидаем ошибку, так как нет БД

def test_status_endpoint(client, tmp_path):
    # Создаем мок статус-файла
    status_data = {
        'calculation_id': 'test_calc_002',
        'report_date': '2023-12-31',
        'status': 'SUCCESS',
        'showcase_path': '/tmp/test.csv'
    }
    with open(tmp_path / 'status_test_calc_002.json', 'w') as f:
        json.dump(status_data, f)
    
    # Мокаем config.json
    config = {
        'paths': {
            'input': str(tmp_path),
            'output': str(tmp_path),
            'scripts': str(tmp_path)
        },
        'db_connection': {},
        'queries': {'input_data': 'SELECT 1'},
        'logging': {'level': 'INFO', 'file': str(tmp_path / 'calculator.log')}
    }
    with open(tmp_path / 'config.json', 'w') as f:
        json.dump(config, f)
    
    response = client.get('/api/status/test_calc_002')
    assert response.status_code == 200
    assert response.json['status'] == 'SUCCESS'