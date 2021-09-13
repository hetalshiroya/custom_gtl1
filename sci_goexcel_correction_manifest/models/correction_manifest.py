from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions
from datetime import datetime, timedelta


class CorrectionManifest(models.TransientModel):
    _name = 'correction.manifest'

    date = fields.Date(string='Date')
    to_char = fields.Char(string='TO')
    tel_char = fields.Char(string='TEL')
    attn_char = fields.Char(string='ATTN')
    from_char = fields.Char(string='FROM') # Carrier

    description_char = fields.Char(string='DESCRIPTION')
    gross_weight_char = fields.Char(string='GROSS WEIGHT')
    measurement_char = fields.Char(string='MEASUREMENT')

    original_consignee_id = fields.Many2one('res.partner', string='Original Consignee')
    original_shipper_id = fields.Many2one('res.partner', string='Original Shipper')
    changed_shipper_id = fields.Many2one('res.partner', string='Changed Shipper')
    changed_consignee_id = fields.Many2one('res.partner', string='Changed Consignee')

    original_consignee = fields.Text(string='Original Consignee Input')
    original_shipper = fields.Text(string='Original Shipper Input')
    changed_consignee = fields.Text(string='Changed Consignee Input')
    changed_shipper = fields.Text(string='Changed Shipper Input')

    @api.model
    def default_get(self, fields):
        #print('>>>>>>>>>>>>> Correction Manifest in default_get')
        result = super(CorrectionManifest, self).default_get(fields)
        booking_id = self.env.context.get('booking_id')
        bl_id = self.env.context.get('bl_id')
        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            if booking.cargo_type == 'fcl':
                cargo_line = booking.operation_line_ids
            else:
                cargo_line = booking.operation_line_ids2
            gross_weight = 0
            measurement = 0
            description = ""
            if cargo_line:
                description = cargo_line[0].container_product_name
            #print('>>>>>>>>>>>>> Correction Manifest Description 1=', description)
            for booking_line in cargo_line:
                gross_weight = gross_weight + booking_line.exp_gross_weight
                measurement = measurement + booking_line.exp_vol

            date = datetime.now().date()
            changed_to = ''
            if booking.carrier:
                changed_to = booking.carrier.name
            if booking.changed_date:
                date = booking.changed_date
            if booking.changed_to:
                changed_to = booking.changed_to
            changed_tel = ''
            if booking.changed_tel:
                changed_tel = booking.changed_tel
            changed_attn = ''
            if booking.changed_attn:
                changed_attn = booking.changed_attn
            changed_from = ''
            if booking.changed_from:
                changed_from = booking.changed_from

            if booking.changed_description:
                description = booking.changed_description
            #TS bug
            #original_consignee_id = booking.consignee.id
            original_consignee = self.env.user.company_id.partner_id
            original_shipper_id = booking.shipper.id
            #print('>>>>>>>>>>>>> Correction Manifest Description 2=', description)
            #print('>>>>>>>>>>>>> Correction Manifest Consignee=', original_consignee.name)
            # for rec in self:
            result.update({'to_char': changed_to or False,
                           'tel_char': changed_tel or False,
                           'attn_char': changed_attn or False,
                           'from_char': changed_from or False,
                           'date': date or False,
                           'description_char': description or False,
                           'gross_weight_char': gross_weight or False,
                           'measurement_char': measurement or False,
                           'original_consignee_id': original_consignee.id or False,
                           'original_shipper_id': original_shipper_id or False,
                           })
            result = self._convert_to_write(result)

        if bl_id:
            bl = self.env['freight.bol'].browse(bl_id)
            cargo_line = bl.cargo_line_ids
            gross_weight = 0
            measurement = 0
            for bl_line in cargo_line:
                gross_weight = gross_weight + bl_line.exp_gross_weight
                measurement = measurement + bl_line.exp_vol
            description = ""
            if cargo_line:
                description = cargo_line[0].container_product_name
            date = datetime.now().date()
            changed_to = ''
            if bl.carrier_c:
                changed_to = bl.carrier_c.name

            if bl.changed_date:
                date = bl.changed_date
            if bl.changed_to:
                changed_to = bl.changed_to
            changed_tel = ''
            if bl.changed_tel:
                changed_tel = bl.changed_tel
            changed_attn = ''
            if bl.changed_attn:
                changed_attn = bl.changed_attn
            changed_from = ''
            if bl.changed_from:
                changed_from = bl.changed_from
            description = ''
            if bl.changed_description:
                description = bl.changed_description

            original_consignee_id = self.env.user.company_id.partner_id.id
            original_shipper_id = bl.shipper_c.id

            # for rec in self:
            result.update({'to_char': changed_to or False,
                           'tel_char': changed_tel or False,
                           'attn_char': changed_attn or False,
                           'from_char': changed_from or False,
                           'date': date or False,
                           'description_char': description or False,
                           'gross_weight_char': gross_weight or False,
                           'measurement_char': measurement or False,
                           'original_consignee_id': original_consignee_id or False,
                           'original_shipper_id': original_shipper_id or False,
                           })
            result = self._convert_to_write(result)
        return result

    @api.onchange('original_consignee_id')
    def onchange_original_consignee_id(self):
        adr = ''
        if self.original_consignee_id:
            #if self.consignee_address_input is False or '':
                adr += self.original_consignee_id.name + "\n"
                if self.original_consignee_id.street:
                    adr += self.original_consignee_id.street
                if self.original_consignee_id.street2:
                    adr += ' ' + self.original_consignee_id.street2
                if self.original_consignee_id.zip:
                    adr += ' ' + self.original_consignee_id.zip
                if self.original_consignee_id.city:
                    adr += ' ' + self.original_consignee_id.city
                if self.original_consignee_id.state_id:
                    adr += ', ' + self.original_consignee_id.state_id.name
                if self.original_consignee_id.country_id:
                    adr += ', ' + self.original_consignee_id.country_id.name + "\n"
                if not self.original_consignee_id.country_id:
                    adr += "\n"
                if self.original_consignee_id.phone:
                    adr += 'Phone: ' + self.original_consignee_id.phone
                elif self.original_consignee_id.mobile:
                    adr += '. Mobile: ' + self.original_consignee_id.mobile
                # if self.consignee.country_id:
                #     adr += ', ' + self.consignee.country_id.name
                # _logger.warning("adr" + adr)
                self.original_consignee = adr


    @api.onchange('original_shipper_id')
    def onchange_original_shipper_id(self):
        adr = ''
        if self.original_shipper_id:
            # if self.consignee_address_input is False or '':
            adr += self.original_shipper_id.name + "\n"
            if self.original_shipper_id.street:
                adr += self.original_shipper_id.street
            if self.original_shipper_id.street2:
                adr += ' ' + self.original_shipper_id.street2
            if self.original_shipper_id.zip:
                adr += ' ' + self.original_shipper_id.zip
            if self.original_shipper_id.city:
                adr += ' ' + self.original_shipper_id.city
            if self.original_shipper_id.state_id:
                adr += ', ' + self.original_shipper_id.state_id.name
            if self.original_shipper_id.country_id:
                adr += ', ' + self.original_shipper_id.country_id.name + "\n"
            if not self.original_shipper_id.country_id:
                adr += "\n"
            if self.original_shipper_id.phone:
                adr += 'Phone: ' + self.original_shipper_id.phone
            elif self.original_shipper_id.mobile:
                adr += '. Mobile: ' + self.original_shipper_id.mobile
            # if self.consignee.country_id:
            #     adr += ', ' + self.consignee.country_id.name
            # _logger.warning("adr" + adr)
            self.original_shipper = adr

    @api.onchange('changed_consignee_id')
    def onchange_changed_consignee_id(self):
        adr = ''
        if self.changed_consignee_id:
            # if self.consignee_address_input is False or '':
            adr += self.changed_consignee_id.name + "\n"
            if self.changed_consignee_id.street:
                adr += self.changed_consignee_id.street
            if self.changed_consignee_id.street2:
                adr += ' ' + self.changed_consignee_id.street2
            if self.changed_consignee_id.zip:
                adr += ' ' + self.changed_consignee_id.zip
            if self.changed_consignee_id.city:
                adr += ' ' + self.changed_consignee_id.city
            if self.changed_consignee_id.state_id:
                adr += ', ' + self.changed_consignee_id.state_id.name
            if self.changed_consignee_id.country_id:
                adr += ', ' + self.changed_consignee_id.country_id.name + "\n"
            if not self.changed_consignee_id.country_id:
                adr += "\n"
            if self.changed_consignee_id.phone:
                adr += 'Phone: ' + self.changed_consignee_id.phone
            elif self.changed_consignee_id.mobile:
                adr += '. Mobile: ' + self.changed_consignee_id.mobile
            # if self.consignee.country_id:
            #     adr += ', ' + self.consignee.country_id.name
            # _logger.warning("adr" + adr)
            self.changed_consignee = adr


    @api.onchange('changed_shipper_id')
    def onchange_changed_shipper_id(self):
        adr = ''
        if self.changed_shipper_id:
            # if self.consignee_address_input is False or '':
            adr += self.changed_shipper_id.name + "\n"
            if self.changed_shipper_id.street:
                adr += self.changed_shipper_id.street
            if self.changed_shipper_id.street2:
                adr += ' ' + self.changed_shipper_id.street2
            if self.changed_shipper_id.zip:
                adr += ' ' + self.changed_shipper_id.zip
            if self.changed_shipper_id.city:
                adr += ' ' + self.changed_shipper_id.city
            if self.changed_shipper_id.state_id:
                adr += ', ' + self.changed_shipper_id.state_id.name
            if self.changed_shipper_id.country_id:
                adr += ', ' + self.changed_shipper_id.country_id.name + "\n"
            if not self.changed_shipper_id.country_id:
                adr += "\n"
            if self.changed_shipper_id.phone:
                adr += 'Phone: ' + self.changed_shipper_id.phone
            elif self.changed_shipper_id.mobile:
                adr += '. Mobile: ' + self.changed_shipper_id.mobile
            # if self.consignee.country_id:
            #     adr += ', ' + self.consignee.country_id.name
            # _logger.warning("adr" + adr)
            self.changed_shipper = adr


    @api.multi
    def action_update_booking(self):
        print("Update")
        booking_id = self.env.context.get('booking_id')
        bl_id = self.env.context.get('bl_id')
        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)
            if self.changed_consignee_id:
                booking.consignee = self.changed_consignee_id.id
                booking.consignee_address_input = self.changed_consignee
            if self.changed_shipper_id:
                booking.shipper = self.changed_shipper_id.id
                booking.shipper_address_input = self.changed_shipper
            booking.changed_consignee = self.changed_consignee
            booking.changed_shipper = self.changed_shipper
            booking.original_consignee = self.original_consignee
            booking.original_shipper = self.original_shipper
            booking.changed_description = self.description_char
            booking.changed_gross_weight = self.gross_weight_char
            booking.changed_measurement = self.measurement_char
            booking.changed_date = self.date
            booking.changed_to = self.to_char
            booking.changed_tel = self.tel_char
            #booking.changed_fax = self.fax_char
            booking.changed_attn = self.attn_char
            booking.changed_from = self.from_char
        if bl_id:
            bl = self.env['freight.bol'].browse(bl_id)
            if self.changed_consignee_id:
                bl.consignee_c = self.changed_consignee_id.id
                bl.consignee = self.changed_consignee
            if self.changed_shipper_id:
                bl.shipper_c = self.changed_shipper_id.id
                bl.shipper = self.changed_shipper
            bl.changed_consignee = self.changed_consignee
            bl.changed_shipper = self.changed_shipper
            bl.original_consignee = self.original_consignee
            bl.original_shipper = self.original_shipper
            bl.changed_description = self.description_char
            bl.changed_gross_weight = self.gross_weight_char
            bl.changed_measurement = self.measurement_char
            bl.changed_date = self.date
            bl.changed_to = self.to_char
            bl.changed_tel = self.tel_char
            bl.changed_attn = self.attn_char
            bl.changed_from = self.from_char


    @api.multi
    def action_update_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        booking_id = self.env.context.get('booking_id')
        bl_id = self.env.context.get('bl_id')
        if booking_id:
            booking = self.env['freight.booking'].browse(booking_id)

            if self.changed_consignee_id:
                booking.consignee = self.changed_consignee_id.id
                booking.consignee_address_input = self.changed_consignee
            if self.changed_shipper_id:
                booking.shipper = self.changed_shipper_id.id
                booking.shipper_address_input = self.changed_shipper
            booking.changed_consignee = self.changed_consignee
            booking.changed_shipper = self.changed_shipper
            booking.original_consignee = self.original_consignee
            booking.original_shipper = self.original_shipper
            booking.changed_description = self.description_char
            booking.changed_gross_weight = self.gross_weight_char
            booking.changed_measurement = self.measurement_char
            booking.changed_date = self.date
            booking.changed_to = self.to_char
            booking.changed_tel = self.tel_char
            # booking.changed_fax = self.fax_char
            booking.changed_attn = self.attn_char
            booking.changed_from = self.from_char

            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_correction_manifest',
                                                       'email_template_correction_manifest')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'freight.booking',
                'default_res_id': self.env.context.get('booking_id'),
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

        if bl_id:
            bl = self.env['freight.bol'].browse(bl_id)
            if self.changed_consignee_id:
                bl.consignee_c = self.changed_consignee_id.id
                bl.consignee = self.changed_consignee
            if self.changed_shipper_id:
                bl.shipper_c = self.changed_shipper_id.id
                bl.shipper = self.changed_shipper
            bl.changed_consignee = self.changed_consignee
            bl.changed_shipper = self.changed_shipper
            bl.original_consignee = self.original_consignee
            bl.original_shipper = self.original_shipper
            bl.changed_description = self.description_char
            bl.changed_gross_weight = self.gross_weight_char
            bl.changed_measurement = self.measurement_char
            bl.changed_date = self.date
            bl.changed_to = self.to_char
            bl.changed_tel = self.tel_char
            bl.changed_attn = self.attn_char
            bl.changed_from = self.from_char

            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = \
                    ir_model_data.get_object_reference('sci_goexcel_correction_manifest',
                                                       'email_template_correction_manifest_bl')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False

            ctx = {
                'default_model': 'freight.bol',
                'default_res_id': self.env.context.get('bl_id'),
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






