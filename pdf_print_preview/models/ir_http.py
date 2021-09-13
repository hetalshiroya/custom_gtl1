# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(Http, self).session_info()

        user = request.env.user

        result.update({
            "preview_print": user.preview_print,
            "automatic_printing": user.automatic_printing,
            "report_layout": bool(user.company_id.external_report_layout_id),
            "exist_logo": bool(user.company_id.logo)
        })

        return result
