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

from flask import render_template

from tentacles.Interfaces.web import server_instance
from tentacles.Interfaces.web.models.community import can_get_community_metrics, \
    get_community_metrics_to_display


@server_instance.route("/community")
def community():
    can_get_metrics = can_get_community_metrics()
    community_metrics = get_community_metrics_to_display() if can_get_metrics else None
    return render_template('community.html',
                           can_get_metrics=can_get_metrics,
                           community_metrics=community_metrics
                           )
