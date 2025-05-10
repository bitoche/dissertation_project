import pandas as pd
import os
import json
from app.config.config_manager import load_config
from app.models.calculation_result import CalculationResult
from app import db
import logging

logger = logging.getLogger('financial_calculator')

class IFRS17Calculator:
    def __init__(self):
        self.config = load_config()
        self.input_path = self.config['paths']['input']
        self.output_path = self.config['paths']['output']
    
    def load_data(self, calculation_id, data_date):
        """Загрузка входных данных из БД"""
        logger.info(f"Loading data for calculation {calculation_id}")
        query = self.config['queries']['input_data']
        data = pd.read_sql(query, db.engine, params={'data_date': data_date})
        return data
    
    def calculate_indicators(self, data, calc_config):
        """Расчет финансовых показателей МСФО 17"""
        logger.info("Calculating IFRS17 indicators")
        try:
            grouped = data.groupby('contract_group').agg({
                'insurance_liability': 'sum',
                'claims_liability': 'sum',
                'insurance_revenue': 'sum',
                'insurance_expense': 'sum',
                'financial_result': 'sum'
            })
            return grouped
        except Exception as e:
            logger.error(f"Indicator calculation failed: {str(e)}")
            raise
    
    def build_showcase(self, indicators, showcase_config):
        """Формирование витрины данных"""
        logger.info("Building data showcase")
        try:
            showcase = indicators.reset_index()
            output_file = os.path.join(self.output_path, f"showcase_{showcase_config['id']}.csv")
            showcase.to_csv(output_file, index=False)
            return output_file
        except Exception as e:
            logger.error(f"Showcase building failed: {str(e)}")
            raise
    
    def run_calculation(self, calc_params):
        """Основной метод расчета"""
        logger.info(f"Starting calculation with params: {calc_params}")
        try:
            data = self.load_data(calc_params['calculation_id'], calc_params['data_date'])
            
            # Загрузка конфигурации расчета
            calc_config_path = os.path.join(self.config['paths']['scripts'], f"{calc_params['calc_type']}.json")
            with open(calc_config_path, 'r') as f:
                calc_config = json.load(f)
            
            indicators = self.calculate_indicators(data, calc_config)
            showcase = self.build_showcase(indicators, calc_config)
            
            # Сохранение результата
            result = CalculationResult(
                calculation_id=calc_params['calculation_id'],
                report_date=calc_params['report_date'],
                data={'showcase_path': showcase},
                status='SUCCESS'
            )
            db.session.add(result)
            db.session.commit()
            
            logger.info(f"Calculation {calc_params['calculation_id']} completed")
            return {'status': 'SUCCESS', 'showcase': showcase}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Calculation failed: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}