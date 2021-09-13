from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta


class TelexRelease(models.TransientModel):
    _name = 'telex.release'

    date = fields.Date(string='Date')
    bl_no = fields.Char(string='B/L No.')
    vessel = fields.Char(string='Vessel')
    second_vessel = fields.Char(string='2nd Vessel')
    volume = fields.Char(string='Volume')
    container_no = fields.Char(string='Contr. No.')
    shipper = fields.Char(string='Shipper')
    release_to = fields.Many2one('res.partner', string='Release To')

    @api.model
    def default_get(self, fields):
        # _logger.warning('in default_get')
        result = super(TelexRelease, self).default_get(fields)
        booking_id = self.env.context.get('booking_id')
        booking = self.env['freight.booking'].browse(booking_id)

        bl_list = self.env['freight.bol'].sudo().search([('booking_ref', '=', booking_id )], limit=1)
        if bl_list:
            bl_no = bl_list.bol_no
        else:
            bl_no = ''

        if booking.cargo_type == 'fcl':
            cargo_line = booking.operation_line_ids
        else:
            cargo_line = booking.operation_line_ids2

        if cargo_line:
            volume = cargo_line[0].exp_vol or False
            container_no = cargo_line[0].container_no or False
        else:
            volume = ''
            container_no = ''

        result.update({'date': booking.booking_date_time or False,
                       'bl_no': bl_no,
                       'vessel': booking.vessel_name.name or False,
                       'second_vessel': booking.feeder_vessel_name,
                       'volume': volume,
                       'container_no': container_no,
                       'shipper': booking.shipper.name,
                       'owner': booking.owner.name,
                       })
        result = self._convert_to_write(result)
        return result

    @api.multi
    def action_print(self):
        booking = self.env['freight.booking']
        book_ids = self._context.get('active_ids')
        booking_ids = booking.browse(book_ids)
        if booking_ids:
            booking_ids.write({'release_to': self.release_to.id,
                               'bl_no': self.bl_no,
                               'volume': self.volume,
                               'container_no': self.container_no,
                               })
        return self.env.ref('sci_goexcel_telex_release.action_telex_release').report_action(booking_ids)


    @api.multi
    def action_send(self):
        booking = self.env['freight.booking']
        book_ids = self._context.get('active_ids')
        booking_ids = booking.browse(book_ids)
        if booking_ids:
            booking_ids.write({'release_to': self.release_to.id,
                               'bl_no': self.bl_no,
                               'volume': self.volume,
                               'container_no': self.container_no,
                               })
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_telex_release', 'email_template_telex_release')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.booking',
            'default_res_id': booking_ids.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }





