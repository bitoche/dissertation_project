if __name__ == '__main__':
    import config.config as conf
    import config.log_config as lconf
    import logging
    lconf.setup_logging()
    
    clog = logging.getLogger('calculation')
    clog.info(f'Started!')
    db_cfg = conf.DBConfig
    clog.info(db_cfg)
