from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    signature_image = fields.Binary("Signature")
    invoice_note = fields.Text(string="Additional Notes for Invoice")
    invoice_note_foreign_currency = fields.Text(string="Additional Notes for Invoice (Foreign Currency)")