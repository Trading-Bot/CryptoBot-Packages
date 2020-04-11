#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
import math
import tulipy
import numpy as np

from octobot_commons.constants import CONFIG_TIME_FRAME, START_PENDING_EVAL_NOTE
from octobot_commons.enums import PriceIndexes
from octobot_commons.channels_name import OctoBotTradingChannelsName
from octobot_evaluators.evaluator.realtime_evaluator import RealTimeEvaluator


class InstantFluctuationsEvaluator(RealTimeEvaluator):
    """
    Idea: moves are lasting approx 12min
    Check the last 12 candles and compute mean closing prices as well as mean volume with a gradually narrower interval to
    compute the strength or weakness of the move
    """

    PRICE_THRESHOLD_KEY = "price_difference_threshold_percent"
    VOLUME_THRESHOLD_KEY = "volume_difference_threshold_percent"

    def __init__(self):
        super().__init__()
        self.something_is_happening = False
        self.last_notification_eval = 0

        self.average_prices = {}
        self.last_price = 0

        # Volume
        self.average_volumes = {}
        self.last_volume = 0

        # Constants
        self.TIME_FRAME = self.specific_config[CONFIG_TIME_FRAME]
        self.VOLUME_HAPPENING_THRESHOLD = 1 + (self.specific_config[self.VOLUME_THRESHOLD_KEY] / 100)
        self.PRICE_HAPPENING_THRESHOLD = self.specific_config[self.PRICE_THRESHOLD_KEY] / 100
        self.MIN_TRIGGERING_DELTA = 0.15
        self.candle_segments = [10, 8, 6, 5, 4, 3, 2, 1]

    async def ohlcv_callback(self, exchange: str, exchange_id: str, symbol: str,  time_frame, candle):
        volume_data = self.get_symbol_candles(exchange, exchange_id, symbol, time_frame).\
            get_symbol_volume_candles(self.candle_segments[0])
        close_data = self.get_symbol_candles(exchange, exchange_id, symbol, time_frame). \
            get_symbol_close_candles(self.candle_segments[0])
        for segment in self.candle_segments:
            volume_data = [d for d in volume_data[-segment:] if d is not None]
            price_data = [d for d in close_data[-segment:] if d is not None]
            self.average_volumes[segment] = np.mean(volume_data)
            self.average_prices[segment] = np.mean(price_data)

        self.last_volume = volume_data[-1]
        self.last_price = close_data[-1]
        await self._trigger_evaluation(symbol)

    async def kline_callback(self, exchange: str, exchange_id: str, symbol: str, time_frame, kline):
        self.last_volume = kline[PriceIndexes.IND_PRICE_VOL.value]
        self.last_price = kline[PriceIndexes.IND_PRICE_CLOSE.value]
        await self._trigger_evaluation(symbol)

    async def _trigger_evaluation(self, symbol):
        self.evaluate_volume_fluctuations()
        if self.something_is_happening and self.eval_note != START_PENDING_EVAL_NOTE:
            if abs(self.last_notification_eval - self.eval_note) >= self.MIN_TRIGGERING_DELTA:
                self.last_notification_eval = self.eval_note
                await self.evaluation_completed(self.cryptocurrency, symbol)
            self.something_is_happening = False
        else:
            self.eval_note = START_PENDING_EVAL_NOTE

    def evaluate_volume_fluctuations(self):
        volume_trigger = 0
        price_trigger = 0

        for segment in self.candle_segments:
            if segment in self.average_volumes and segment in self.average_prices:
                # check volume fluctuation
                if self.last_volume > self.VOLUME_HAPPENING_THRESHOLD * self.average_volumes[segment]:
                    volume_trigger += 1
                    self.something_is_happening = True

                # check price fluctuation
                segment_average_price = self.average_prices[segment]
                if self.last_price > (1 + self.PRICE_HAPPENING_THRESHOLD) * segment_average_price:
                    price_trigger += 1
                    self.something_is_happening = True

                elif self.last_price < (1 - self.PRICE_HAPPENING_THRESHOLD) * segment_average_price:
                    price_trigger -= 1
                    self.something_is_happening = True

        if self.candle_segments:
            average_volume_trigger = min(1, volume_trigger / len(self.candle_segments) + 0.2)
            average_price_trigger = price_trigger / len(self.candle_segments)

            if average_price_trigger < 0:
                # math.cos(1-x) between 0 and 1 starts around 0.5 and smoothly goes up to 1
                self.eval_note = -1 * math.cos(1 - (-1 * average_price_trigger * average_volume_trigger))
            elif average_price_trigger > 0:
                self.eval_note = math.cos(1 - average_price_trigger * average_volume_trigger)
            else:
                # no price info => high volume but no price move, can't say anything
                self.something_is_happening = False
        else:
            self.something_is_happening = False

    async def start(self, bot_id: str) -> bool:
        """
        Subscribe to Kline and OHLCV notification
        :return: bool
        """
        try:
            from octobot_trading.channels.exchange_channel import get_chan as get_trading_chan
            from octobot_trading.api.exchange import get_exchange_id_from_matrix_id
            exchange_id = get_exchange_id_from_matrix_id(self.exchange_name, self.matrix_id)
            await get_trading_chan(OctoBotTradingChannelsName.OHLCV_CHANNEL.value, exchange_id).new_consumer(
                callback=self.ohlcv_callback, symbol=self.symbol, time_frame=self.TIME_FRAME)
            await get_trading_chan(OctoBotTradingChannelsName.KLINE_CHANNEL.value, exchange_id).new_consumer(
                callback=self.kline_callback, symbol=self.symbol, time_frame=self.TIME_FRAME)
            return True
        except ImportError:
            self.logger.error("Can't connect to trading channels")
        return False

    def set_default_config(self):
        super().set_default_config()
        self.specific_config[CONFIG_TIME_FRAME] = "1m"

    @classmethod
    def get_is_symbol_wildcard(cls) -> bool:
        """
        :return: True if the evaluator is not symbol dependant else False
        """
        return False


class InstantMAEvaluator(RealTimeEvaluator):

    def __init__(self):
        super().__init__()
        self.last_candle_data = {}
        self.last_moving_average_values = {}
        self.period = 6
        self.time_frame = self.specific_config[CONFIG_TIME_FRAME]

    async def ohlcv_callback(self, exchange: str, exchange_id: str, symbol: str, time_frame, candle):
        self.eval_note = 0
        new_data = self.get_symbol_candles(exchange, exchange_id, symbol, time_frame). \
            get_symbol_close_candles(20)
        should_eval = symbol not in self.last_candle_data or \
            not self._compare_data(new_data, self.last_candle_data[symbol])
        self.last_candle_data[symbol] = new_data
        if should_eval:
            if len(self.last_candle_data[symbol]) > self.period:
                self.last_moving_average_values[symbol] = tulipy.sma(self.last_candle_data[symbol],
                                                                     self.period)
                await self._evaluate_current_price(self.last_candle_data[symbol][-1], symbol)

    async def kline_callback(self, exchange: str, exchange_id: str, symbol: str, time_frame, kline):
        if symbol in self.last_moving_average_values and len(self.last_moving_average_values[symbol]) > 0:
            self.eval_note = 0
            last_price = kline[PriceIndexes.IND_PRICE_CLOSE.value]
            if last_price != self.last_candle_data[symbol][-1]:
                await self._evaluate_current_price(last_price, symbol)

    async def _evaluate_current_price(self, last_price, symbol):
        last_ma_value = self.last_moving_average_values[symbol][-1]
        if last_ma_value == 0:
            self.eval_note = 0
        else:
            current_ratio = last_price / last_ma_value
            if current_ratio > 1:
                # last_price > last_ma_value => sell ? => eval_note > 0
                if current_ratio >= 2:
                    self.eval_note = 1
                else:
                    self.eval_note = current_ratio - 1
            elif current_ratio < 1:
                # last_price < last_ma_value => buy ? => eval_note < 0
                self.eval_note = -1 * (1 - current_ratio)
            else:
                self.eval_note = 0

        await self.evaluation_completed(self.cryptocurrency, symbol)

    async def start(self, bot_id: str) -> bool:
        """
        Subscribe to Kline and OHLCV notification
        :return: bool
        """
        try:
            from octobot_trading.channels.exchange_channel import get_chan as get_trading_chan
            from octobot_trading.api.exchange import get_exchange_id_from_matrix_id
            exchange_id = get_exchange_id_from_matrix_id(self.exchange_name, self.matrix_id)
            await get_trading_chan(OctoBotTradingChannelsName.OHLCV_CHANNEL.value, exchange_id).new_consumer(
                callback=self.ohlcv_callback, time_frame=self.time_frame)
            await get_trading_chan(OctoBotTradingChannelsName.KLINE_CHANNEL.value, exchange_id).new_consumer(
                callback=self.kline_callback, time_frame=self.time_frame)
            return True
        except ImportError:
            self.logger.error("Can't connect to trading channels")
        return False

    def set_default_config(self):
        super().set_default_config()
        self.specific_config[CONFIG_TIME_FRAME] = "1m"

    @staticmethod
    def _compare_data(new_data, old_data):
        try:
            if new_data[PriceIndexes.IND_PRICE_CLOSE.value][-1] != old_data[PriceIndexes.IND_PRICE_CLOSE.value][-1]:
                return False
            return True
        except Exception:
            return False
