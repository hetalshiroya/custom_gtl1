from odoo import api, fields, models,exceptions
import logging
from datetime import date
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.voucher.line'

    freight_hbl = fields.Many2one('freight.bol', string='Booking HBL')

