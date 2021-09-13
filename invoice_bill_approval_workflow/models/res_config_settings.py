# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_bill_approval = fields.Boolean("Invoice/Bill Approval", related='company_id.invoice_bill_approval', readonly=False)
    invoice_ammount = fields.Monetary(related='company_id.invoice_ammount', string="Invoice Minimum Amount", readonly=False)
    bill_ammount = fields.Monetary(related='company_id.bill_ammount', string="Bill Minimum Amount", readonly=False)
    customer_vendor_credit_approval = fields.Boolean(related='company_id.customer_vendor_credit_approval', readonly=False)
    customer_credit_note_ammount_ammount = fields.Monetary(related='company_id.customer_credit_note_ammount_ammount', readonly=False)
    vendor_credit_note_ammount = fields.Monetary(related='company_id.vendor_credit_note_ammount', readonly=False)
    invoice_user_ids = fields.Many2many('res.users', related='company_id.invoice_user_ids', readonly=False, string="Invoice Users")
    bill_user_ids = fields.Many2many('res.users', related='company_id.bill_user_ids', readonly=False, string="Bill Users")
    invoice_cn_user_ids = fields.Many2many('res.users', related='company_id.invoice_cn_user_ids', readonly=False, string="Invoice CN Users")
    bill_cn_user_ids = fields.Many2many('res.users', related='company_id.bill_cn_user_ids', readonly=False, string="Bill CN Users")

    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     params_obj = self.env['ir.config_parameter']
    #     params_obj.sudo().set_param("invoice_user_ids", self.invoice_user_ids.ids)
    #     params_obj.sudo().set_param("bill_user_ids", self.bill_user_ids.ids)
    #     params_obj.sudo().set_param("invoice_cn_user_ids", self.invoice_cn_user_ids.ids)
    #     params_obj.sudo().set_param("bill_cn_user_ids", self.bill_cn_user_ids.ids)
