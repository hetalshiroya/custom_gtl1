from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_bank_account = fields.Many2one('res.partner.bank',string="Default Bank Account", domain="[('partner_id', '=', id)]")
    soa_note = fields.Text(string="Additional Notes for SOA")