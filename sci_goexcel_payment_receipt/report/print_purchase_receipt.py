# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _
from datetime import datetime
import dateutil.relativedelta
from datetime import timedelta, date
import calendar
import math
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.misc import formatLang


class PrintSaleReceipt(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_av_pr_details'
    _description = "Print Purchase Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        #print("Print Sale Receipt")
        #docs = self.env['payment.receipt'].browse(data['form'])
        docs = self.env['account.voucher'].browse(data['form'])
        #_logger.warning('docs=' + str(docs))
        payment_docs = []

        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            period = str(doc.date.strftime("%m")) + '/' + str(doc.date.year)
            company = self.env['res.company'].browse(doc.company_id.id)
            company_info = {
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
            # for payment_line in doc.payment_lines:
            for payment_line in doc.line_ids:
                #print('payment_line name=' + str(payment_line.name))
                serial_no += 1
                #print('invoice=' + str(invoice_id.number))
                # _logger.warning('supplier invoice=' + str(invoice_id.reference))
                if doc.voucher_type == 'sale':
                    payment_docs.append({
                         'serial_no': serial_no,
                         'description': payment_line.name,
                         # 'payment_no': doc.number,
                         # 'source_doc': payment_line.origin,
                         #'invoice_date': payment_line.date_invoice,
                         #'payment_ref': doc.name,
                         #'period': period,
                         'amount': payment_line.price_subtotal,
                         'currency_id': doc.currency_id,
                    })
                elif doc.voucher_type == 'purchase':
                    #_logger.warning('supplier invoice lines=' + str(invoice_id.invoice_line_ids))
                    #line = invoice_id.invoice_line_ids.sorted(lambda c: c.sequence)[0]
                    payment_docs.append({
                        'serial_no': serial_no,
                        'description': payment_line.name,
                        'account': payment_line.account_id.name,
                        # 'source_doc': payment_line.origin,
                         'invoice_date': doc.date,
                        # 'payment_ref': doc.name,
                        # 'period': period,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                    })


        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].voucher_type, total_en,
                                                             total_amount, docs[0].currency_id)
        partner_info = self.get_partner_info(partner)
        bank_info = self.get_bank_info(docs[0])
        #print("Print AV PR Action")
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': payment_docs,
            # 'get_payment_lines':self.get_payment_lines,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
            'company_info': company_info,
            'bank_info': bank_info,
        }

    @api.multi
    def get_partner_info(self, o):
        # get the vendor bank info
        account_number = ''
        bank_name = ''
        company = self.env['res.company'].browse(o.company_id)
        if company:
            bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', o.id)
            ], limit=1)
            if bank:
                # print('acct_number"' + str(bank.acc_number))
                account_number = bank.acc_number
                bank_name = bank.bank_id.name

        partner_info = {
            'name': o.name,
            'street': o.street,
            'street2': o.street2,
            'zip': o.zip,
            'city': o.city,
            'state': o.state_id.name,
            'country': o.country_id.name,
            'phone': o.phone,
            'fax': o.fax,
            'account_number': account_number,
            'bank': bank_name,
        }
        return partner_info

    @api.multi
    def get_bank_info(self, o):
        # get the journal bank info
        account_number = ''
        bank = ''
        if o.journal_id:
            journal = self.env['account.journal'].browse(o.journal_id.id)
            if journal:
                if journal.bank_id:
                    print('bank=' + str(journal.bank_id.name))
                    bank = journal.bank_id.name
                if journal.bank_account_id:
                    print('acct_number=' + str(journal.bank_account_id.acc_number))
                    account_number = journal.bank_account_id.acc_number

        bank_info = {
            'account_number': account_number,
            'bank': bank,
        }

        return bank_info


    @api.multi
    def get_payment_receipt_info(self, o, voucher_type, total_en, total_amount, currency_id):
        #print("PR=" + o.name)
        payment_receipt_info = {
            #'payment_receipt_no': o.payment_receipt_no,
            'payment_receipt_no': o.number,
            'payment_receipt_date': o.date,
            'voucher_type': voucher_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
            'payment_ref': o.name,
            'cheque_no': o.cheque_no,
            'cheque_date': '',
        }
        return payment_receipt_info

    # def get_payment_date_period(self, payment_date):






    # def get_payment_lines(self, payment):
    #     res = []
    #     for payment_line in payment.payment_lines:
    #         res.append({
    #             'payment_date': payment_line.payment_date,
    #             'name': payment_line.name,
    #             'journal_id': payment_line.journal_id,
    #             'payment_method_id': payment_line.payment_method_id,
    #             'partner_id': payment_line.partner_id,
    #             'amount': payment_line.amount,
    #             'state': payment_line.state,
    #         })
    #
    #     return res
