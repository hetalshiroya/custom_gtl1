from odoo import api, fields, models,exceptions
import logging
from datetime import date
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.voucher.line'

    freight_booking = fields.Many2one('freight.booking', string='Booking Job')

    def action_assign_job_cost(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_invoice.view_job_cost_form')
        return {
            'name': 'Add Job Cost',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'freight.booking.job.cost',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(self.env.context, voucher_id=self.voucher_id.id, partner_id=self.voucher_id.partner_id.id,),
        }
