from datetime import timedelta
from typing import List, Optional
from pytz import timezone

from vnpy.trader.setting import SETTINGS
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, TickData, HistoryRequest
from vnpy.trader.utility import extract_vt_symbol
from vnpy.trader.datafeed import BaseDatafeed

from .pyTSL import Client, DoubleToDatetime


CHINA_TZ = timezone("Asia/Shanghai")

EXCHANGE_MAP = {
    Exchange.SSE: "SH",
    Exchange.SZSE: "SZ"
}

INTERVAL_MAP = {
    Interval.MINUTE: "cy_1m",
    Interval.HOUR: "cy_60m",
    Interval.DAILY: "cy_day",
}

SHIFT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
}


class TinysoftDatafeed(BaseDatafeed):
    """天软数据服务接口"""

    def __init__(self):
        """"""
        self.username: str = SETTINGS["datafeed.username"]
        self.password: str = SETTINGS["datafeed.password"]

        self.client: Client = None
        self.inited: bool = False

    def init(self) -> bool:
        """初始化"""
        if self.inited:
            return True

        self.client = Client(
            self.username,
            self.password,
            "tsl.tinysoft.com.cn",
            443
        )

        n = self.client.login()
        if n != 1:
            return False

        self.inited = True
        return True

    def query_bar_history(self, req: HistoryRequest) -> Optional[List[BarData]]:
        """查询K线数据"""
        if not self.inited:
            self.init()

        symbol, exchange = extract_vt_symbol(req.vt_symbol)
        tsl_exchange = EXCHANGE_MAP.get(exchange, "")
        tsl_interval = INTERVAL_MAP[req.interval]

        bars: List[BarData] = []

        start_str = req.start.strftime("%Y%m%d")
        end_str = req.end.strftime("%Y%m%d")

        cmd = (
            f"setsysparam(pn_cycle(),{tsl_interval}());"
            "return select * from markettable "
            f"datekey {start_str}T to {end_str}T "
            f"of '{tsl_exchange}{symbol}' end;"
        )
        result = self.client.exec(cmd)

        if not result.error():
            data = result.value()
            shift = SHIFT_MAP.get(req.interval, None)

            for d in data:
                dt = DoubleToDatetime(d["date"])
                if shift:
                    dt -= shift

                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=CHINA_TZ.localize(dt),
                    open_price=d["open"],
                    high_price=d["high"],
                    low_price=d["low"],
                    close_price=d["close"],
                    volume=d["vol"],
                    turnover=d["amount"],
                    gateway_name="TSL"
                )

                # 期货则获取持仓量字段
                if not tsl_exchange:
                    bar.open_interest = d["sectional_cjbs"]

                bars.append(bar)

        return bars

    def query_tick_history(self, req: HistoryRequest) -> Optional[List[TickData]]:
        """查询Tick数据"""
        if not self.inited:
            self.init()

        symbol, exchange = extract_vt_symbol(req.vt_symbol)
        tsl_exchange = EXCHANGE_MAP.get(exchange, "")

        ticks: List[TickData] = []

        dt = req.start
        while dt <= req.end:
            date_str = dt.strftime("%Y%m%d")
            cmd = f"return select * from tradetable datekey {date_str}T to {date_str}T+16/24 of '{tsl_exchange}{symbol}' end ; "
            result = self.client.exec(cmd)

            if not result.error():
                data = result.value()
                for d in data:
                    dt = DoubleToDatetime(d["date"])

                    tick = TickData(
                        symbol=symbol,
                        exchange=exchange,
                        name=d["StockName"],
                        datetime=CHINA_TZ.localize(dt),
                        open_price=d["sectional_open"],
                        high_price=d["sectional_high"],
                        low_price=d["sectional_low"],
                        last_price=d["price"],
                        volume=d["sectional_vol"],
                        turnover=d["sectional_amount"],
                        bid_price_1=d["buy1"],
                        bid_price_2=d["buy2"],
                        bid_price_3=d["buy3"],
                        bid_price_4=d["buy4"],
                        bid_price_5=d["buy5"],
                        ask_price_1=d["sale1"],
                        ask_price_2=d["sale2"],
                        ask_price_3=d["sale3"],
                        ask_price_4=d["sale4"],
                        ask_price_5=d["sale5"],
                        bid_volume_1=d["bc1"],
                        bid_volume_2=d["bc2"],
                        bid_volume_3=d["bc3"],
                        bid_volume_4=d["bc4"],
                        bid_volume_5=d["bc5"],
                        ask_volume_1=d["sc1"],
                        ask_volume_2=d["sc2"],
                        ask_volume_3=d["sc3"],
                        ask_volume_4=d["sc4"],
                        ask_volume_5=d["sc5"],
                        localtime=dt,
                        gateway_name="TSL"
                    )

                    # 期货则获取持仓量字段
                    if not tsl_exchange:
                        tick.open_interest = d["sectional_cjbs"]

                    ticks.append(tick)

            dt += timedelta(days=1)

        return ticks
