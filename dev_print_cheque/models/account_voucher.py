# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
from odoo import models,fields, api
from odoo import tools

class account_voucher(models.Model):
    _inherit ='account.payment'
    
    @api.model
    def _get_check_formate(self):
        company_id = self.env.user.company_id.id
        formate_id = self.env['cheque.setting'].search([('set_default','=',True),('company_id','=',company_id)],limit=1)
        return formate_id.id

    cheque_formate_id = fields.Many2one('cheque.setting', 'Cheque Formate', default=_get_check_formate)
    cheque_no = fields.Char('Cheque No')
    text_free = fields.Char('Free Text')
    partner_text = fields.Char('Partner Title')


    
# vim:expandtab:smartindent:tabstop=4:4softtabstop=4:shiftwidth=4:    
