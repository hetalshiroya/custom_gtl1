# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResUsers( models.Model ):
    _inherit = "res.users"

    preview_print = fields.Boolean(
        string  = "Preview print",
        default = True
    )

    automatic_printing = fields.Boolean(
        srting = "Automatic printing"
    )

    @api.multi
    def preview_reload(self):
        return {
            "type": "ir.actions.client", 
            "tag": "reload"
        }

    @api.multi
    def preview_print_save(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload_context"
        }

    def __init__(self, pool, cr):

        init_res = super(ResUsers, self).__init__(pool, cr)
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(["preview_print", "automatic_printing"])
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(["preview_print", "automatic_printing"])

        return init_res
        