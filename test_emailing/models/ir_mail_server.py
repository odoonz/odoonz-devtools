# Copyright 2020 RIL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import models


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def _tracking_email_id_body_get(self, body):
        """
        overwrite the function:
        re.search return None if no matching and raise error for match.group()
        """
        body = body or ""
        # https://regex101.com/r/lW4cB1/2
        match = re.search(r'<img[^>]*data-odoo-tracking-email=["\']([0-9]*)["\']', body)
        return int(match.group(1)) if match is not None and match.group(1) else False
