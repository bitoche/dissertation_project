from flask import Blueprint, request, jsonify
from app.calculator.ifrs17_calculator import IFRS17Calculator
from app.config.config_manager import load_config
import logging
import os
import json

api_bp = Blueprint('api', __name__)
logger = logging.getLogger('financial_calculator')

@api_bp.route('/calculate', methods=['POST'])
def calculate():
    """
    Run IFRS17 calculation
    ---
    tags:
      - Calculation
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - report_date
            - prev_report_date
            - data_date
            - calc_type
            - calculation_id
          properties:
            report_date:
              type: string
              example: "2023-12-31"
            prev_report_date:
              type: string
              example: "2023-11-30"
            data_date:
              type: string
              example: "2023-12-31"
            calc_type:
              type: string
              example: "IFRS17"
            calculation_id:
              type: string
              example: "calc_001"
    responses:
      200:
        description: Calculation successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: "SUCCESS"
            showcase:
              type: string
              example: "/app/data/output/showcase_calc_001.csv"
      400:
        description: Missing required parameters
      500:
        description: Calculation failed
    """
    params = request.json
    required_params = ['report_date', 'prev_report_date', 'data_date', 'calc_type', 'calculation_id']
    
    if not all(param in params for param in required_params):
        logger.error("Missing required parameters")
        return jsonify({'status': 'ERROR', 'message': 'Missing required parameters'}), 400
    
    try:
        calculator = IFRS17Calculator()
        result = calculator.run_calculation(params)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Calculation failed: {str(e)}")
        return jsonify({'status': 'ERROR', 'error': str(e)}), 500

@api_bp.route('/status/<calculation_id>', methods=['GET'])
def check_status(calculation_id):
    config = load_config()
    status_file = os.path.join(config['paths']['output'], f"status_{calculation_id}.json")
    
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        logger.info(f"Status check for calculation {calculation_id}: {status_data['status']}")
        return jsonify({'calculation_id': calculation_id, 'status': status_data['status']})
    
    logger.warning(f"Calculation {calculation_id} not found")
    return jsonify({'status': 'NOT_FOUND'}), 404