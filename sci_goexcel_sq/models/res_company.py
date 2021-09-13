from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    air_freight_note = fields.Text(string="Air Freight Terms & Conditions")
    land_freight_note = fields.Text(string="Land Freight Terms & Conditions")
