from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class AccountLetterTemplate(models.Model):
    _inherit = "sale.letter.template"

    sq_type = fields.Selection([('freight', 'Freight'), ('warehouse', 'Warehouse')],string="SQ Type")
