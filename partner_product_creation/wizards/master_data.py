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

    type = fields.Selection([('1', 'Consignee/ Shipper'), ('2', 'Commodity')], string='Type', default='1')

    @api.multi
    def action_create(self):
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
                'consignee': True,
                'shipper': True,
            })

        if self.type == '2':
            product = self.env['product.product']
            commodity_lines = self.env['freight.product.category'].search([('type', '=ilike', 'commodity')])
            if commodity_lines:
                product.create({
                    'name': self.name,
                    'list_price': 0,
                    'taxes_id': False,
                    'sale_ok': False,
                    'purchase_ok': False,
                    'categ_id': commodity_lines[0].product_category.id or False
                })
            else:
                product.create({
                    'name': self.name,
                    'list_price': 0,
                    'taxes_id': False,
                    'sale_ok': False,
                    'purchase_ok': False,
                })


