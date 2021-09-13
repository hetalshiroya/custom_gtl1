from odoo import models, fields, api


class ResCurrency(models.Model):
    _inherit = 'res.currency.rate'

    date_to = fields.Date(string='Date-To', track_visibility='onchange')
    name = fields.Date(string='Date-From', track_visibility='onchange')