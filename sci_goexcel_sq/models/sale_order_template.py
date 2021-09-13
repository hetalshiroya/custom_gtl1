from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order.template"

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id.id)

    require_payment = fields.Boolean('Online Payment', default=True, help='Request an online payment to the customer in order to confirm orders automatically.')
