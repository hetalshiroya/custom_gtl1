from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class ShippingInstruction1(models.Model):
    _inherit = "freight.website.si"

    to_char = fields.Char(string='TO')
    attn_char = fields.Char(string='ATTN')
    pcs_weight_m3 = fields.Char(string='Pcs/ Weight/ M3')
    commodity = fields.Char(string='Commodity')


    @api.multi
    def action_send_si_carrier(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data.get_object_reference('sci_goexcel_shipping_instruction', 'email_template_si_carrier')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'freight.website.si',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_light",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # ctx['action_url'] = "{}/web?db={}".format(base_url, self.env.cr.dbname)
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

    @api.multi
    def action_shipping_instruction(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_shipping_instruction.shipping_instruction_wizard_view_form')
        return {
            'name': 'Shipping Instruction',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shipping.instruction.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

            'context': dict(si_id=self.id),
        }

