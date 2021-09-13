# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):

    _inherit = "res.company"

    fax = fields.Char(string='Fax')

