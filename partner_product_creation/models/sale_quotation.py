from odoo import api, fields, models, exceptions
import logging

_logger = logging.getLogger(__name__)


class SaleQuotation(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_partner_product_creation(self):
        self.ensure_one()
        view = self.env.ref('partner_product_creation.master_data_view_form')
        return {
            'name': 'Create',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'master.data.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }