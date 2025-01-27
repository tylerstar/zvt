# -*- coding: utf-8 -*-
import datetime
import json
import os
from typing import List

from sqlalchemy import or_

from zvt.api import float_to_pct_str
from zvt.contract import ActorType
from zvt.domain import FinanceFactor, BalanceSheet, IncomeStatement, Stock, StockActorSummary
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp, now_time_str


def get_subscriber_emails():
    emails_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'subscriber_emails.json'))
    with open(emails_file) as f:
        return json.load(f)


def risky_company(the_date=to_pd_timestamp(now_time_str()), income_yoy=-0.1, profit_yoy=-0.1, entity_ids=None):
    codes = []
    start_timestamp = to_pd_timestamp(the_date) - datetime.timedelta(130)
    # 营收降，利润降,流动比率低，速动比率低
    finance_filter = or_(FinanceFactor.op_income_growth_yoy < income_yoy,
                         FinanceFactor.net_profit_growth_yoy <= profit_yoy,
                         FinanceFactor.current_ratio < 0.7,
                         FinanceFactor.quick_ratio < 0.5)
    df = FinanceFactor.query_data(entity_ids=entity_ids, start_timestamp=start_timestamp, filters=[finance_filter],
                                  columns=['code'])
    if pd_is_not_null(df):
        codes = codes + df.code.tolist()

    # 高应收，高存货，高商誉
    balance_filter = (BalanceSheet.accounts_receivable + BalanceSheet.inventories + BalanceSheet.goodwill) \
                     > BalanceSheet.total_equity
    df = BalanceSheet.query_data(entity_ids=entity_ids, start_timestamp=start_timestamp, filters=[balance_filter],
                                 columns=['code'])
    if pd_is_not_null(df):
        codes = codes + df.code.tolist()

    # 应收>利润*1/2
    df1 = BalanceSheet.query_data(entity_ids=entity_ids, start_timestamp=start_timestamp,
                                  columns=[BalanceSheet.code, BalanceSheet.accounts_receivable])
    if pd_is_not_null(df1):
        df1.drop_duplicates(subset='code', keep='last', inplace=True)
        df1 = df1.set_index('code', drop=True).sort_index()

    df2 = IncomeStatement.query_data(entity_ids=entity_ids, start_timestamp=start_timestamp,
                                     columns=[IncomeStatement.code,
                                              IncomeStatement.net_profit])
    if pd_is_not_null(df2):
        df2.drop_duplicates(subset='code', keep='last', inplace=True)
        df2 = df2.set_index('code', drop=True).sort_index()

    if pd_is_not_null(df1) and pd_is_not_null(df2):
        codes = codes + df1[df1.accounts_receivable > df2.net_profit / 2].index.tolist()

    return list(set(codes))


def stocks_with_info(stocks: List[Stock]):
    infos = []
    for stock in stocks:
        info = f'{stock.name}({stock.code})'
        summary: List[StockActorSummary] = StockActorSummary.query_data(entity_id=stock.entity_id,
                                                                        order=StockActorSummary.timestamp.desc(),
                                                                        filters=[
                                                                            StockActorSummary.actor_type == ActorType.raised_fund.value],
                                                                        limit=1, return_type='domain')
        if summary:
            info = info + f'([{summary[0].timestamp}]共{summary[0].actor_count}家基金持股占比:{float_to_pct_str(summary[0].holding_ratio)}, 变化: {float_to_pct_str(summary[0].change_ratio)})'

        summary: List[StockActorSummary] = StockActorSummary.query_data(entity_id=stock.entity_id,
                                                                        order=StockActorSummary.timestamp.desc(),
                                                                        filters=[
                                                                            StockActorSummary.actor_type == ActorType.qfii.value],
                                                                        limit=1, return_type='domain')
        if summary:
            info = info + f'([{summary[0].timestamp}]共{summary[0].actor_count}家qfii持股占比:{float_to_pct_str(summary[0].holding_ratio)}, 变化: {float_to_pct_str(summary[0].change_ratio)})'

        infos.append(info)
    return infos


if __name__ == '__main__':
    print(get_subscriber_emails())
