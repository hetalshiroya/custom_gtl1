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


class PrintOfficialReceipt(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_or_details'
    _description = "Print Official Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        # Outbound
        #docs = self.env['payment.receipt'].browse(data['form'])
        docs = self.env['account.payment'].browse(data['form'])
        #_logger.warning('docs=' + str(docs))
        payment_docs = []

        total_amount = 0.00
        for doc in docs:
            serial_no = 0
            partner = doc.partner_id
            total_amount = doc.amount
            period = str(doc.payment_date.strftime("%m")) + '/' + str(doc.payment_date.year)
            sorted_payment_lines = doc.payment_invoice_ids.sorted(key=lambda t: t.date_invoice, reverse=False)
            for payment_line in sorted_payment_lines:
                if payment_line.reconcile_amount !=0:
                    #print('payment_line name=' + str(payment_line.name))
                    serial_no += 1
                    #print('invoice=' + str(invoice_id.number))
                    # _logger.warning('customer invoice=' + str(invoice_id.reference))
                    if doc.payment_type == 'inbound':
                        payment_docs.append({
                             'serial_no': serial_no,
                             'invoice_no': payment_line.invoice_id.number,
                             'payment_no': doc.name,
                             'source_doc': payment_line.origin,
                             'invoice_date': payment_line.date_invoice,
                             'original_amount': payment_line.invoice_id.amount_total,
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
                            'supplier_invoice_no': payment_line.invoice_id.number,
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

                        # payment_docs.append({
                        #     'serial_no': serial_no,
                        #     'invoice_no': invoice_id.number,
                        #     'supplier_invoice_no': invoice_id.reference,
                        #     'payment_no': account_payment.move_name,
                        #     'account': line.account_id.name,
                        #     'description': account_payment.communication,
                        #     'payment_ref': account_payment.reference,
                        #     'period': period,
                        #     'amount': account_payment.amount,
                        #     'currency_id': account_payment.currency_id,
                        # })


        total_en = doc.currency_id.amount_to_text(total_amount).upper()
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].payment_type, total_en,
                                                             total_amount, docs[0].currency_id)
        partner_info = self.get_partner_info(partner)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': payment_docs,
            # 'get_payment_lines':self.get_payment_lines,
            'partner_info': partner_info,
            'payment_receipt_info': payment_receipt_info,
        }

    @api.multi
    def get_partner_info(self, o):
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
        }
        return partner_info

    @api.multi
    def get_payment_receipt_info(self, o, payment_type, total_en, total_amount, currency_id):
        #print("OR=" + o.name)
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
