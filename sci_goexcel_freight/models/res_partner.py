from odoo import api, models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    carrier = fields.Boolean(string="Is Carrier?")
    shipping_agent_code = fields.Char(string='Shipping Agent Code')
    shipper = fields.Boolean(string="Is Shipper?")
    transporter = fields.Boolean(string="Is Transporter?")
    consignee = fields.Boolean(string="Is Consignee?")
    company_booking_count = fields.Integer(compute='_compute_company_booking_count')
    is_company = fields.Boolean(string='Is a Company', default=True,
                                help="Check if the contact is a company, otherwise it is a person")
    def _compute_company_booking_count(self):
        for partner in self:
            bookings = self.env['freight.booking'].search([
                ('customer_name', '=', partner.id),
            ])
            partner.company_booking_count = len(bookings)

    @api.multi
    def default_company(self):
        res = super(ResPartner, self).default_company()
        self.is_company = True
        return res
