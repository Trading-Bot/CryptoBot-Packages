#  Drakkar-Software OctoBot-Interfaces
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
import json
from flask import request, jsonify

from octobot_services.interfaces.util.order import cancel_orders, get_all_open_orders
from octobot_services.interfaces.util.portfolio import trigger_portfolios_refresh
from . import api
from tentacles.Services.Interfaces.web_interface.util.flask_util import get_rest_reply
from tentacles.Services.Interfaces.web_interface.login.web_login_manager import login_required_when_activated


@api.route("/orders", methods=['GET', 'POST'])
@login_required_when_activated
def orders():
    if request.method == 'GET':
        real_open_orders, simulated_open_orders = get_all_open_orders()

        return json.dumps({"real_open_orders": real_open_orders, "simulated_open_orders": simulated_open_orders})
    elif request.method == "POST":
        result = ""
        request_data = request.get_json()
        action = request.args.get("action")
        if action == "cancel_order":
            if cancel_orders([request_data]):
                result = "Order cancelled"
            else:
                return get_rest_reply('Impossible to cancel order: order not found.', 500)
        elif action == "cancel_orders":
            removed_count = cancel_orders(request_data)
            result = f"{removed_count} orders cancelled"
        return jsonify(result)


@api.route("/refresh_portfolio", methods=['POST'])
@login_required_when_activated
def refresh_portfolio():
    try:
        trigger_portfolios_refresh()
        return jsonify("Portfolio(s) refreshed")
    except RuntimeError:
        return get_rest_reply("No portfolio to refresh", 500)
