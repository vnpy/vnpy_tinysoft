from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional

from pyTSL import Client, DoubleToDatetime

from vnpy.trader.setting import SETTINGS
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData, TickData, HistoryRequest
from vnpy.trader.utility import extract_vt_symbol, ZoneInfo
from vnpy.trader.datafeed import BaseDatafeed


EXCHANGE_MAP: Dict[Exchange, str] = {
    Exchange.SSE: "SH",
    Exchange.SZSE: "SZ"
}

INTERVAL_MAP: Dict[Interval, str] = {
    Interval.MINUTE: "cy_1m",
    Interval.HOUR: "cy_60m",
    Interval.DAILY: "cy_day",
}

SHIFT_MAP: Dict[Interval, timedelta] = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
}

CHINA_TZ = ZoneInfo("Asia/Shanghai")


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

        n: int = self.client.login()
        if n != 1:
            return False

        self.inited = True
        return True

    def query_bar_history(self, req: HistoryRequest) -> Optional[List[BarData]]:
        """查询K线数据"""
        if not self.inited:
            self.init()

        symbol, exchange = extract_vt_symbol(req.vt_symbol)
        tsl_exchange: str = EXCHANGE_MAP.get(exchange, "")
        tsl_interval: str = INTERVAL_MAP[req.interval]

        bars: List[BarData] = []

        start_str: str = req.start.strftime("%Y%m%d")
        end_str: str = req.end.strftime("%Y%m%d")

        cmd: str = (
            f"setsysparam(pn_cycle(),{tsl_interval}());"
            "return select * from markettable "
            f"datekey {start_str}T to {end_str}T "
            f"of '{tsl_exchange}{symbol}' end;"
        )
        result = self.client.exec(cmd)

        if not result.error():
            data = result.value()
            shift: timedelta = SHIFT_MAP.get(req.interval, None)

            for d in data:
                dt: datetime = DoubleToDatetime(d["date"])
                if shift:
                    dt -= shift

                bar: BarData = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt.replace(tzinfo=CHINA_TZ),
                    interval=req.interval,
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
        tsl_exchange: str = EXCHANGE_MAP.get(exchange, "")

        ticks: List[TickData] = []
        dts: Set[datetime] = set()

        dt: datetime = req.start
        while dt <= req.end:
            date_str: str = dt.strftime("%Y%m%d")
            cmd: str = f"return select * from tradetable datekey {date_str}T to {date_str}T+16/24 of '{tsl_exchange}{symbol}' end ; "
            result = self.client.exec(cmd)

            if not result.error():
                data = result.value()
                for d in data:
                    dt: datetime = DoubleToDatetime(d["date"])
                    dt: datetime = dt.replace(tzinfo=CHINA_TZ)

                    # 解决期货缺失毫秒时间戳的问题
                    if dt in dts:
                        dt = dt.replace(microsecond=500000)
                    dts.add(dt)

                    tick: TickData = TickData(
                        symbol=symbol,
                        exchange=exchange,
                        name=d["StockName"],
                        datetime=dt,
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
