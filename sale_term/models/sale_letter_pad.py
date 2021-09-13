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

    @api.multi
    def _get_default_term(self):
        for rec in self:
            #print(' _get_default_term')
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'sq'),('default', '=', True)], limit=1)
            if template:
                #print(' _get_default_term template')
                return template.template


    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]},)
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]}, default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'invoice'), ('default', '=', True)],
                                                               limit=1)
            if template:
                return template.template

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]}, )
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]},
                            default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'po'), ('default', '=', True)],
                                                               limit=1)
            if template:
                return template.template

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]}, )
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]},
                            default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:
            self.sale_term = self.template_id.template


class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _get_default_term(self):
        for rec in self:
            template = self.env['sale.letter.template'].search([('doc_type', '=', 'do'), ('default', '=', True)],
                                                               limit=1)
            if template:
                return template.template

    template_id = fields.Many2one('sale.letter.template', 'Template', states={'draft': [('readonly', False)]}, )
    sale_term = fields.Html('Template', states={'draft': [('readonly', False)]},
                            default=_get_default_term)
    print_term = fields.Boolean('Print Terms', states={'draft': [('readonly', False)]})

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
    default = fields.Boolean('Active', default=True)
    doc_type = fields.Selection([('sq', 'Sale Quotation'), ('invoice', 'Invoice'), ('do', 'Delivery Order'),
                                 ('po', 'Purchase Order')], string="Document Type", track_visibility='onchange')