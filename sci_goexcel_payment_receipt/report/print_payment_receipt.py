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


class PrintPaymentReceipt(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_pr_details'
    _description = "Print Payment Receipt for Vendor (vendor bill)"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        #Inbound
        #docs = self.env['payment.receipt'].browse(data['form'])
        docs = self.env['account.payment'].browse(data['form'])
        #_logger.warning('docs=' + str(docs))
        payment_docs = []
        journal_docs = []
        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            period = str(doc.payment_date.strftime("%m")) + '/' + str(doc.payment_date.year)
            company = self.env['res.company'].browse(doc.company_id.id)
            company_info = {
                'phone': company.phone,
                'fax': company.fax,
                'email': company.email,
                'website': company.website,
            }
            # if it is invoice payment
            #TS Bug - invoice lines are saved but not reconciled.
            filtered_invoice_ids = doc.payment_invoice_ids.filtered(lambda r: r.reconcile_amount != 0)

            if filtered_invoice_ids and len(filtered_invoice_ids) > 0:
                sorted_payment_lines = doc.payment_invoice_ids.sorted(key=lambda t: t.date_invoice, reverse=False)
                for payment_line in sorted_payment_lines:
                    if payment_line.reconcile_amount != 0:
                        #print('payment_line name=' + str(payment_line.name))
                        serial_no += 1
                        #print('invoice=' + str(invoice_id.number))
                        # _logger.warning('supplier invoice=' + str(invoice_id.reference))
                        if doc.payment_type == 'inbound':
                            payment_docs.append({
                                 'serial_no': serial_no,
                                 'invoice_no': payment_line.invoice_id.number,
                                 'payment_no': doc.name,
                                 'source_doc': payment_line.origin,
                                 'invoice_date': payment_line.date_invoice,
                                 'payment_ref': doc.reference,
                                 'period': period,
                                 'amount': payment_line.reconcile_amount,
                                 'currency_id': doc.currency_id,
                            })
                        elif doc.payment_type == 'outbound':
                            #_logger.warning('supplier invoice lines=' + str(invoice_id.invoice_line_ids))
                            #line = invoice_id.invoice_line_ids.sorted(lambda c: c.sequence)[0]
                            payment_docs.append({
                                'serial_no': serial_no,
                                'supplier_invoice_no': payment_line.reference,
                                'description': payment_line.description,
                                'payment_no': doc.name,
                                'source_doc': payment_line.origin,
                                'invoice_date': payment_line.date_invoice,
                                'original_amount': payment_line.invoice_id.amount_total,
                                'payment_no': doc.name,
                                'payment_ref': doc.reference,
                                'period': period,
                                'amount': payment_line.reconcile_amount,
                                'currency_id': doc.currency_id,
                            })
            # if it is journal payment (only for migrated journal entries)
            elif doc.open_move_line_ids:
                #for journal_line in doc.open_move_line_ids:
                #print('journal payment')
                if doc.payment_type == 'outbound' and doc.move_reconciled:
                    journal_items = self.env['account.move.line'].search([
                        ('payment_id', '=', doc.id)
                    ])
                    serial_no += 1
                    #print('journal items len=', str(len(journal_items)))
                    #TODO
                    #  Comment and Add by Kinjal
                    # for journal in journal_items:
                    #     reference = ''
                    #     amount = ''
                    #     #print('journal=', str(journal.move_id.name))
                    #     if journal.debit > 0:
                    #         #print('debit=', str(journal.debit))
                    #         if journal.reconciled:
                    #             #print('reconciled')
                    #             amount = journal.debit
                    #             for reconc_item in journal.full_reconcile_id:
                    #                 #print('full reconcile id')
                    #                 if reconc_item.reconciled_line_ids:
                    #                     #print('reconciled line ids')
                    #                     for recon_line in reconc_item.reconciled_line_ids:
                    #                         #print('reconciled line credit=' + str(recon_line.credit))
                    #                         if recon_line.credit > 0:
                    #                             reference = recon_line.move_id.name
                    #                             #break
                    #             for reconc_item in journal.matched_debit_ids:
                    #                 #print('partial matched debit ids')
                    #                 if reconc_item.debit_move_id:
                    #                     for recon_line in reconc_item.debit_move_id:
                    #                         #print('reconciled line debit=' + str(recon_line.debit))
                    #                         if recon_line.debit > 0:
                    #                             reference = recon_line.move_id.name
                    #             for reconc_item in journal.matched_credit_ids:
                    #                 #print('partial matched credit ids')
                    #                 if reconc_item.credit_move_id:
                    #                     for recon_line in reconc_item.credit_move_id:
                    #                         #print('reconciled line credit=' + str(recon_line.credit))
                    #                         if recon_line.credit > 0:
                    #                             reference = recon_line.move_id.name
                    #                             #break
                    #                 #     #print('partial reconciled line ids')
                    #                 #     for recon_line in reconc_item.reconciled_line_ids:
                    #                 #         #print('reconciled line credit=' + str(recon_line.credit))
                    #                 #         if recon_line.credit > 0:
                    #                 #              reference = recon_line.move_id.name
                    #                 #              break
                    #             #print('before journal_docs append reference=' + str(reference))
                    #             #print('before journal_docs append amount=' + str(amount))
                    #             journal_docs.append({
                    #                 'serial_no': serial_no,
                    #                 #'supplier_invoice_no': journal_line.reference,
                    #                 #'description': payment_line.description,
                    #                 'journal_no': journal.move_id.name,
                    #                 'reference': reference,
                    #                 'journal_date': journal.date,
                    #                 'amount': amount,
                    #                 'currency_id': doc.currency_id,
                    #             })
                    for journal in journal_items:
                        if journal.debit > 0 and journal.reconciled:
                            for recon_line in journal.full_reconcile_id.reconciled_line_ids.filtered(lambda x: x.invoice_id):
                                journal_docs.append({
                                        'serial_no': serial_no,
                                        'journal_no': recon_line.move_id.name,
                                        'reference': recon_line.invoice_id.number,
                                        'journal_date': recon_line.date,
                                        'amount': abs(recon_line.balance),
                                        'currency_id': doc.currency_id,
                                    })
                                serial_no += 1
        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].payment_type, total_en,
                                                             total_amount, docs[0].currency_id)


        partner_info = self.get_partner_info(partner)

        bank_info = self.get_bank_info(docs[0])

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': payment_docs,
            'journal_docs': journal_docs,
            # 'get_payment_lines':self.get_payment_lines,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
            'company_info': company_info,
            'bank_info': bank_info,

        }

    @api.multi
    def get_partner_info(self, o):
        #get the vendor bank info
        account_number = ''
        bank_name = ''
        company = self.env['res.company'].browse(o.company_id)
        if company:
            bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', o.id)
            ], limit=1)
            # if not bank:
            #     bank = self.env['res.partner.bank'].search([
            #         ('partner_id', '=', o.id), ('company_id', '=', False)
            #     ], limit=1)
            if bank:
                #print('acct_number"' + str(bank.acc_number))
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
                    #print('bank=' + str(journal.bank_id.name))
                    bank = journal.bank_id.name
                if journal.bank_account_id:
                    #print('acct_number=' + str(journal.bank_account_id.acc_number))
                    account_number = journal.bank_account_id.acc_number


        bank_info = {
            'account_number': account_number,
            'bank': bank,
        }

        return bank_info

    @api.multi
    def get_payment_receipt_info(self, o, payment_type, total_en, total_amount, currency_id):
        ##print("PR=" + o.name)
        #print("get_payment_receipt_info=" + str(o.bank_date))
        payment_receipt_info = {
            #'payment_receipt_no': o.payment_receipt_no,
            'payment_receipt_no': o.name,
            'payment_receipt_date': o.payment_date,
            'payment_type': payment_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
            #'cheque_no': o.check_no,
            'cheque_no': o.cheque_no,
            'payment_ref': o.reference,
            'cheque_date': o.bank_date,
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
