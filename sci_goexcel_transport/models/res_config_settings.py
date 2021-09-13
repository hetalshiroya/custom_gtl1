# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_po = fields.Boolean(string="Purchase Order For RFT?")
    use_vb = fields.Boolean(string="Vendor Bill For RFT?")
    use_packaging = fields.Boolean(string="Packaging for RFT?")
    use_manpower = fields.Boolean(string="Additional ManPower For RFT?")
    use_equipment = fields.Boolean(string="Additional Tool & Equipment For RFT?")
#    crm_alias_prefix = fields.Char('Default Alias Name for Leads')
#    generate_lead_from_alias = fields.Boolean('Manual Assignation of Emails', config_parameter='crm.generate_lead_from_alias')

#    module_crm_phone_validation = fields.Boolean("Phone Formatting")
#    module_crm_reveal = fields.Boolean("Create Leads/Opportunities from your website's traffic")



    # @api.onchange('group_use_po')
    # def _onchange_group_use_po(self):
    #     """ Reset alias / leads configuration if leads are not used """
    #     if not self.group_use_lead:
    #         self.generate_lead_from_alias = False


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        use_po = param.get_param('sci_goexcel_transport.use_po')
        use_vb = param.get_param('sci_goexcel_transport.use_vb')
        use_packaging = param.get_param('sci_goexcel_transport.use_packaging')
        use_manpower = param.get_param('sci_goexcel_transport.use_manpower')
        use_equipment = param.get_param('sci_goexcel_transport.use_equipment')
        res.update(use_po = use_po, use_vb = use_vb, use_packaging = use_packaging,
                   use_manpower = use_manpower, use_equipment=use_equipment)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        use_po = self.use_po or False
        param.set_param('sci_goexcel_transport.use_po', use_po)
        use_vb = self.use_vb or False
        param.set_param('sci_goexcel_transport.use_vb', use_vb)
        use_packaging = self.use_packaging or False
        param.set_param('sci_goexcel_transport.use_packaging', use_packaging)
        use_manpower = self.use_manpower or False
        param.set_param('sci_goexcel_transport.use_manpower', use_manpower)
        use_equipment = self.use_equipment or False
        param.set_param('sci_goexcel_transport.use_equipment', use_equipment)