from odoo import models, fields, api


class VisitPurpose(models.Model):
    _name = 'visit.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)

