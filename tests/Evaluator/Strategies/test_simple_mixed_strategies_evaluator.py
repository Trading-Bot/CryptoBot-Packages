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

import pytest

from tests.functional_tests.strategy_evaluators_tests.abstract_strategy_test import AbstractStrategyTest
from evaluator.Strategies import SimpleMixedStrategiesEvaluator
from trading.trader.modes import DailyTradingMode


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture()
def strategy_tester():
    strategy_tester_instance = TestSimpleMixedStrategiesEvaluator()
    strategy_tester_instance.initialize(SimpleMixedStrategiesEvaluator, DailyTradingMode)
    return strategy_tester_instance


class TestSimpleMixedStrategiesEvaluator(AbstractStrategyTest):

    @staticmethod
    async def test_default_run(strategy_tester):
        await strategy_tester.run_test_default_run(-4.5)

    @staticmethod
    async def test_slow_downtrend(strategy_tester):
        await strategy_tester.run_test_slow_downtrend(-4.5, -30, -30.5, -13.5)

    @staticmethod
    async def test_sharp_downtrend(strategy_tester):
        await strategy_tester.run_test_sharp_downtrend(-22, -21.5)

    @staticmethod
    async def test_flat_markets(strategy_tester):
        await strategy_tester.run_test_flat_markets(5.5, 3, 2, -2.5)

    @staticmethod
    async def test_slow_uptrend(strategy_tester):
        await strategy_tester.run_test_slow_uptrend(10.5, 0)

    @staticmethod
    async def test_sharp_uptrend(strategy_tester):
        await strategy_tester.run_test_sharp_uptrend(8, 9.5)

    @staticmethod
    async def test_up_then_down(strategy_tester):
        await strategy_tester.run_test_up_then_down(-7.5)
