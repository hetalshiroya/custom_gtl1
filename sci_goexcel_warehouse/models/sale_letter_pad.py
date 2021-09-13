# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

states = [('draft', 'Draft'), ('approved', 'Approved')]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    template_id = fields.Many2one('sale.letter.template', 'Template', readonly=True, states={'draft': [('readonly', False)]})
    sale_term = fields.Html('Template', readonly=True, states={'draft': [('readonly', False)]})
    print_term = fields.Boolean('Print Terms', readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template

class AccountLetterTemplate(models.Model):
    _name = 'sale.letter.template'
    _description = 'Terms and Condition'

    name = fields.Char('Name', required=True)
    template = fields.Html('Template')
    active = fields.Boolean('Active', default=True)