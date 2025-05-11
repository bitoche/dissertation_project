from flask import Blueprint, request, jsonify
from app.calculator.ifrs17_calculator import IFRS17Calculator
from app.models.calculation_result import CalculationResult
from app import db
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger('financial_calculator')

@api_bp.route('/calculate', methods=['POST'])
def calculate():
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
    result = CalculationResult.query.filter_by(calculation_id=calculation_id).first()
    if result:
        logger.info(f"Status check for calculation {calculation_id}: {result.status}")
        return jsonify({'calculation_id': calculation_id, 'status': result.status})
    logger.warning(f"Calculation {calculation_id} not found")
    return jsonify({'status': 'NOT_FOUND'}), 404