from odoo import api, fields, models


class MasterDataWizard(models.TransientModel):
    _name = 'master.data.wizard'

    name = fields.Char(string='Name', required=1)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one('res.country', string='Country')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    fax = fields.Char(string='Fax')
    email = fields.Char(string='Email')

    type = fields.Selection([('0', 'Consignee'),
                             ('1', 'Shipper'),
                             ('2', 'Notify Party'),
                             ('99', 'Commodity'),
                             ], string='Type')

    @api.multi
    def action_create(self):
        if self.type == '0':
            res_partner = self.env['res.partner']

            res_partner.create({
                'name': self.name,
                'street': self.street  or False,
                'street2': self.street2 or False,
                'city': self.city or False,
                'state_id': self.state_id.id or False,
                'zip': self.zip or False,
                'country_id': self.country_id.id or False,
                'phone': self.phone or False,
                'mobile': self.mobile or False,
                'fax': self.fax or False,
                'email': self.email or False,
                'company_type': 'company',
                'customer': False,
                'consignee': True,
                'property_account_receivable_id': self.env.user.company_id.partner_id.property_account_receivable_id.id,
                'property_account_payable_id': self.env.user.company_id.partner_id.property_account_payable_id.id,
            })

        if self.type == '1':
            res_partner = self.env['res.partner']
            res_partner.create({
                'name': self.name,
                'street': self.street  or False,
                'street2': self.street2 or False,
                'city': self.city or False,
                'state_id': self.state_id.id or False,
                'zip': self.zip or False,
                'country_id': self.country_id.id or False,
                'phone': self.phone or False,
                'mobile': self.mobile or False,
                'fax': self.fax or False,
                'email': self.email or False,
                'company_type': 'company',
                'customer': False,
                'shipper': True,
                'property_account_receivable_id': self.env.user.company_id.partner_id.property_account_receivable_id.id,
                'property_account_payable_id': self.env.user.company_id.partner_id.property_account_payable_id.id,
            })

        if self.type == '2':
            res_partner = self.env['res.partner']
            res_partner.create({
                'name': self.name,
                'street': self.street  or False,
                'street2': self.street2 or False,
                'city': self.city or False,
                'state_id': self.state_id.id or False,
                'zip': self.zip or False,
                'country_id': self.country_id.id or False,
                'phone': self.phone or False,
                'mobile': self.mobile or False,
                'fax': self.fax or False,
                'email': self.email or False,
                'company_type': 'company',
                'customer': False,
                'property_account_receivable_id': self.env.user.company_id.partner_id.property_account_receivable_id.id,
                'property_account_payable_id': self.env.user.company_id.partner_id.property_account_payable_id.id,
            })

        if self.type == '99':
            product = self.env['freight.commodity1']
            product.create({
                    'name': self.name,
            })



