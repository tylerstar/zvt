# -*- coding: utf-8 -*-
from ...context import init_test_context

init_test_context()

from zvt.recorders.eastmoney.meta.eastmoney_stock_meta_recorder import EastmoneyChinaStockDetailRecorder

from zvt.consts import SAMPLE_STOCK_CODES


def test_meta_recorder():
    recorder = EastmoneyChinaStockDetailRecorder(codes=SAMPLE_STOCK_CODES)
    try:
        recorder.run()
    except:
        assert False
