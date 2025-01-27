# -*- coding: utf-8 -*-
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from zvt import init_log, zvt_config
from zvt.domain import *
from zvt.informer.informer import EmailInformer

logger = logging.getLogger(__name__)

sched = BackgroundScheduler()


# 每天下午17:00抓取
@sched.scheduled_job('cron', hour=17, minute=00)
def record_margin_trading():
    email_action = EmailInformer()

    try:
        MarginTrading.record_data(provider='joinquant', sleeping_time=1)
        email_action.send_message(zvt_config['email_username'], 'joinquant record margin trading finished', '')
    except Exception as e:
        msg = f'joinquant record margin trading:{e}'
        logger.exception(msg)

        email_action.send_message(zvt_config['email_username'], 'joinquant record margin trading error', msg)
        time.sleep(60)


# 周6抓取
@sched.scheduled_job('cron', hour=2, minute=00, day_of_week=5)
def record_valuation():
    while True:
        email_action = EmailInformer()

        try:
            # 个股估值数据
            StockValuation.record_data(provider='joinquant', sleeping_time=1)

            email_action.send_message(zvt_config['email_username'], 'joinquant record valuation finished', '')
            break
        except Exception as e:
            msg = f'joinquant record kdata:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'joinquant record valuation error', msg)
            time.sleep(60)


# 周4抓取
@sched.scheduled_job('cron', hour=19, minute=00, day_of_week=3)
def record_others():
    while True:
        email_action = EmailInformer()

        try:
            Etf.record_data(provider='joinquant', sleeping_time=1)
            EtfStock.record_data(provider='joinquant', sleeping_time=1)

            email_action.send_message(zvt_config['email_username'], 'joinquant record etf finished', '')
            break
        except Exception as e:
            msg = f'joinquant record etf error:{e}'
            logger.exception(msg)

            email_action.send_message(zvt_config['email_username'], 'joinquant record etf error', msg)
            time.sleep(60)


if __name__ == '__main__':
    init_log('joinquant_other_data_runner.log')

    record_margin_trading()

    sched.start()

    sched._thread.join()
