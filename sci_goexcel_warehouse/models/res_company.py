from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    do_note = fields.Text(string="Additional Notes for DO")
