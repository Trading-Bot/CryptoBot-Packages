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

import flask

import octobot.community
import octobot.constants as constants
import octobot_services.interfaces.util as interfaces_util
import tentacles.Services.Interfaces.web_interface as web_interface
import tentacles.Services.Interfaces.web_interface.login as login
import tentacles.Services.Interfaces.web_interface.models as models


@web_interface.server_instance.route("/community")
@login.login_required_when_activated
def community():
    authenticator = interfaces_util.get_bot_api().get_community_auth()
    logged_in_email = None
    try:
        logged_in_email = authenticator.get_logged_in_email()
    except octobot.community.AuthenticationRequired:
        pass
    except Exception as e:
        flask.flash(f"Error when contacting the community server: {e}", "error")
    if logged_in_email is None:
        return flask.redirect('community_login')
    # TODO
    default_image = f"{constants.OCTOBOT_COMMUNITY_URL}/assets/meganav/promo_banner_left-first-category-1e19fc784f709ed0ebbd047064cf872195c2d33da29996b7c7cf469f858a8a71.jpg"
    return flask.render_template('community.html',
                                 current_logged_in_email=logged_in_email,
                                 tentacles_packages=models.get_account_tentacles_packages(authenticator),
                                 current_bots_stats=models.get_current_octobots_stats(),
                                 community_url=constants.OCTOBOT_COMMUNITY_URL,
                                 default_tentacles_package_image=default_image)


@web_interface.server_instance.route("/community_metrics")
@login.login_required_when_activated
def community_metrics():
    can_get_metrics = models.can_get_community_metrics()
    community_metrics = models.get_community_metrics_to_display() if can_get_metrics else None
    return flask.render_template('community_metrics.html',
                                 can_get_metrics=can_get_metrics,
                                 community_metrics=community_metrics
                                 )
