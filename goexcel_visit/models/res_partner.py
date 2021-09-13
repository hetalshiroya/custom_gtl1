from odoo import models, fields, api


class VisitResPartner(models.Model):

    _inherit = 'res.partner'

    visit_company_count = fields.Integer(compute='_compute_visit_company_count')
    visit_contact_count = fields.Integer(compute='_compute_visit_contact_count')
    partner_visit_frequency = fields.Selection([('01', 'Weekly'), ('02', 'Bi-Weekly'), ('03', 'Monthly'),
                                                ('04', 'Bi-Monthly'), ('06', 'Quarterly'),
                                                ('07', 'Half-Yearly'), ('08', 'Yearly')], string='Visit Frequency')

    def _compute_visit_company_count(self):
        for partner in self:
            visits = self.env['visit'].search([
                ('customer_name', '=', partner.id),
            ])
            partner.visit_company_count = len(visits)

    def _compute_visit_contact_count(self):
        for partner in self:
            visits = self.env['visit'].search([
                ('contact', '=', partner.id),
            ])
            partner.visit_contact_count = len(visits)




