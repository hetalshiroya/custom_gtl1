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

    _inherit = 'report.sci_goexcel_payment_receipt.report_pr_details'


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
                print('invoice payment')
                for payment_line in doc.payment_invoice_ids:
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
                                 'original_amount': payment_line.amount_total,
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
                                'payment_no': doc.name,
                                'payment_ref': doc.reference,
                                'period': period,
                                'original_amount': payment_line.amount_total,
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


