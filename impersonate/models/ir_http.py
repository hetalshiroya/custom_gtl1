# -*- coding: UTF-8 -*-

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()

        res.update({
            'impersonator_uid': request.session.get('impersonator_uid', False),
            'impersonate_check': request.env.user.impersonate_check(),
        })

        return res
