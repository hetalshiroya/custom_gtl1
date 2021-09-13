from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta


class ShippingInstructionWizard(models.TransientModel):
    _name = 'shipping.instruction.wizard'

    report_type = fields.Selection([('1', 'Shipping Instruction'), ('2', 'Shipping Instruction to Carrier')
                                    , ('3', 'Shipping Instruction (Excel)')], string="Report Type" , default='1')
    service_type = fields.Selection([('ocean', 'Ocean'), ('air', 'Air'), ('land', 'Land')], string="Shipment Mode")
    type = fields.Selection([('1', 'MAWB'), ('2', 'HAWB')], string='Type')
    to_char = fields.Char(string='TO')
    attn_char = fields.Char(string='ATTN')
    remarks = fields.Text(string='Remarks')

    shipper = fields.Text(string='Shipper')
    consignee = fields.Text(string='Consignee')
    oversea_agent = fields.Text(string='Overseas Agent')
    pcs_weight_m3 = fields.Char(string='Pcs/ Weight/ M3')
    commodity = fields.Char(string='Commodity')

    @api.model
    def default_get(self, fields):
        result = super(ShippingInstructionWizard, self).default_get(fields)
        si_id = self.env.context.get('si_id')
        if si_id:
            si = self.env['freight.website.si'].browse(si_id)
            if si.cargo_type == 'fcl':
                cargo_line = si.fcl_line_ids
            else:
                cargo_line = si.lcl_line_ids
            pcs = 0
            gross_weight = 0
            measurement = 0

            for si_line in cargo_line:
                pcs = pcs + si_line.packages_no
                gross_weight = gross_weight + si_line.exp_gross_weight
                measurement = measurement + si_line.exp_vol

            si_to_char = si.customer_name.name
            si_attn_char = si.contact_name.name
            si_note = si.note

            si_shipper = si.shipper
            si_consignee = si.consignee
            si_oversea_agent = si.shipping_agent
            si_pcs_weight_m3 = str(pcs) +' /' + str(gross_weight) +' /' + str(measurement)

            # for rec in self:
            result.update({'service_type': si.service_type,
                           'type': si.air_freight_type,
                           'to_char': si_to_char or False,
                           'attn_char': si_attn_char or False,
                           'remarks': si_note or False,
                           'shipper': si_shipper or False,
                           'consignee': si_consignee or False,
                           'oversea_agent': si_oversea_agent or False,
                           'pcs_weight_m3': si_pcs_weight_m3 or False,
                           #'commodity': si.booking_ref.commodity.name or False,
                           'commodity': si.booking_ref.commodity1 or False,
                           })
            result = self._convert_to_write(result)
        return result

    @api.multi
    def action_print(self):
        si = self.env['freight.website.si']
        si_ids = si.browse(self._context.get('active_ids'))
        if si_ids:
            if self.report_type == '1':
                si_ids.write({'air_freight_type': self.type,
                              'to_char': self.to_char,
                              'attn_char': self.attn_char,
                              'shipper': self.shipper,
                              'consignee': self.consignee,
                              'shipping_agent': self.oversea_agent,
                              'pcs_weight_m3': self.pcs_weight_m3,
                              'commodity': self.commodity,
                              'note': self.remarks,
                              })
                return self.env.ref('sci_goexcel_shipping_instruction.action_si_report').report_action(si_ids)
            if self.report_type == '2':
                return self.env.ref('sci_goexcel_shipping_instruction.action_si_report_carrier').report_action(si_ids)
            if self.report_type == '3':
                return self.env.ref('sci_goexcel_freight.action_si_report_xlsx').report_action(si_ids)

    @api.multi
    def action_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''

        si_id = self.env.context.get('si_id')
        if self.report_type == '1':
            si = self.env['freight.website.si'].browse(si_id)
            si.air_freight_type = self.type
            si.to_char = self.to_char
            si.attn_char = self.attn_char
            si.shipper = self.shipper
            si.consignee = self.consignee
            si.shipping_agent = self.oversea_agent
            si.pcs_weight_m3 = self.pcs_weight_m3
            si.commodity = self.commodity
            si.note = self.remarks

            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_shipping_instruction', 'email_template_si')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'freight.website.si',
                'default_res_id': self.env.context.get('si_id'),
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_light",
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
        if self.report_type == '2':
            '''
                    This function opens a window to compose an email, with the template message loaded by default
                    '''
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_shipping_instruction', 'email_template_si_carrier')[
                        1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'freight.website.si',
                'default_res_id': self.env.context.get('si_id'),
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




