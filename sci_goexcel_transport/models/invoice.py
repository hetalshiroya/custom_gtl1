from odoo import models, fields


class RFTInvoice(models.Model):

    _inherit = 'account.invoice'

    rft_id = fields.Many2one('transport.rft', string='RFT ID', readonly=True)


