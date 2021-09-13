from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_freight_note = fields.Boolean(string='Use Freight Note')
    freight_note = fields.Text(string="Remark")
