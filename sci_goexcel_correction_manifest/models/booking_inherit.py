from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking1(models.Model):
    _inherit = "freight.booking"

    @api.multi
    def action_correction_manifest(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_correction_manifest.correction_manifest_view_form')
        return {
            'name': 'Create Correction Manifest',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'correction.manifest',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(booking_id=self.id),
        }

