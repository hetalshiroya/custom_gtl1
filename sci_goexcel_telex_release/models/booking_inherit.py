from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    release_to = fields.Many2one('res.partner', string='Release To', store=True)
    bl_no = fields.Char(string='B/L No.', store=True)
    volume = fields.Char(string='Volume', store=True)
    container_no = fields.Char(string='Contr. No.', store=True)

    @api.multi
    def action_telex_release(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_telex_release.telex_release_view_form')
        return {
            'name': 'Telex Release',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'telex.release',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(booking_id=self.id),
        }

