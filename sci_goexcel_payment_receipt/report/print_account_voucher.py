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


class PrintAcountVoucher(models.AbstractModel):
    _name = 'report.sci_goexcel_payment_receipt.report_av_details'
    _description = "Print Payment Receipt"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        #_logger.warning("_get_report_values")
        docs = self.env['account.voucher'].browse(data['form'])
        #_logger.warning('docs=' + str(docs))
        payment_docs = []
        for doc in docs:
            serial_no = 0
            period = str(doc.date.strftime("%m")) + '/' + str(doc.date.year)
            partner = doc.partner_id
            for payment_line in doc.line_ids:
                serial_no += 1
                if doc.voucher_type == 'sale':
                    payment_docs.append({
                         'serial_no': serial_no,
                         'invoice_no': doc.reference,
                         'payment_no': doc.move_id.name or False,
                         'payment_ref': doc.payment_journal_id.name or False,
                         'period': period,
                         'amount': payment_line.price_subtotal,
                         'currency_id': doc.currency_id,
                    })
                elif doc.voucher_type == 'purchase':
                    payment_docs.append({
                        'serial_no': serial_no,
                        'invoice_no': '',
                        'supplier_invoice_no': doc.reference,
                        'payment_no': doc.move_id.name or False,
                        'account': doc.account_id.name or False,
                        'description': payment_line.name,
                        'payment_ref': doc.payment_journal_id.name or False,
                        'period': period,
                        'amount': payment_line.price_subtotal,
                        'currency_id': doc.currency_id,
                    })

            total_en = doc.currency_id.amount_to_text(doc.amount)
        payment_receipt_info = self.get_payment_receipt_info(docs[0], docs[0].voucher_type, total_en,
                                                             docs[0].amount, docs[0].currency_id)
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
    def get_payment_receipt_info(self, o, voucher_type, total_en, total_amount, currency_id):
        #_logger.warning("PR=" + o.payment_receipt_no)
        payment_receipt_info = {
            'payment_receipt_no': o.number,
            'payment_receipt_date': o.date,
            'payment_type': voucher_type,
            'total_en': total_en,
            'total_amount': total_amount,
            'currency_id': currency_id,
        }
        return payment_receipt_info

