# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import dateutil.relativedelta
from datetime import timedelta, date
import calendar
import math
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.misc import formatLang


class PrintJobSheet(models.AbstractModel):
    _name = 'report.sci_goexcel_job_sheet.report_job_sheet_details'
    _description = "Print Job Sheet"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['freight.booking'].browse(docids)
        cost_profit_ids = []
        test = []
        invoice_ids = []
        receipt_ids = []
        info_ids = []
        for doc in docs:
            sale_total = 0
            cost_total = 0
            bol = self.env['freight.bol'].search([('booking_ref', '=', doc.id)])
            invoices = self.env['account.invoice'].search([('freight_booking', '=', doc.id)])

            invoices_booking = self.env['account.invoice'].search([('freight_booking', '=', doc.id)])
            invoices_hbl = self.env['account.invoice'].search([('freight_hbl', '=', doc.id)])

            for invoice in invoices_booking:
                if invoice.type == 'in_invoice':
                    type = 'Vendor Bill'
                if invoice.type == 'out_invoice':
                    type = 'Customer Invoice'
                invoice_ids.append({
                    'type': type,
                    'partner_id': invoice.partner_id.name,
                    'number': invoice.number,
                    'currency_id': invoice.currency_id.name,
                    'amount_total': float(invoice.amount_total),
                })

            for invoice in invoices_hbl:
                if invoice.type == 'in_invoice':
                    type = 'Vendor Bill'
                if invoice.type == 'out_invoice':
                    type = 'Customer Invoice'
                invoice_ids.append({
                    'type': type,
                    'partner_id': invoice.partner_id.name,
                    'number': invoice.number,
                    'currency_id': invoice.currency_id.name,
                    'amount_total': float(invoice.amount_total),
                })

            dummy_product_id = 99999999
            receipt_booking = self.env['account.voucher.line'].search([('freight_booking', '=', doc.id)])
            for receipt in receipt_booking:
                receipt_ids.append(receipt.voucher_id.id)
                product_id = False
                if receipt.product_id:
                    product_id = receipt.product_id
                else:
                    product_id = dummy_product_id
                    dummy_product_id = dummy_product_id - 1
                cost_profit_ids.append({
                    'product_id': product_id,
                    'product_name': receipt.name,
                    'costing': float(receipt.price_subtotal),
                    'billing': 0.00,
                })

            receipt_hbl = self.env['account.voucher.line'].search([('freight_hbl', '=', doc.id)])
            for receipt in receipt_hbl:
                receipt_ids.append(receipt.voucher_id.id)
                product_id = False
                if receipt.product_id:
                    product_id = receipt.product_id
                else:
                    product_id = dummy_product_id
                    dummy_product_id = dummy_product_id - 1
                cost_profit_ids.append({
                    'product_id': product_id,
                    'product_name': receipt.name,
                    'costing': float(receipt.price_subtotal),
                    'billing': 0.00,
                })

            receipt_ids = list(dict.fromkeys(receipt_ids))

            for receipt in receipt_ids:
                invoice = self.env['account.voucher'].search([('id', '=', receipt)])
                invoice_ids.append({
                    'type': 'Purchase Receipt',
                    'partner_id': invoice.partner_id.name,
                    'number': invoice.number,
                    'currency_id': invoice.currency_id.name,
                    'amount_total': float(invoice.amount),
                })

                cost_total = cost_total + float(invoice.amount)


            for bol_line in bol:
                for bol_cost_profit_line in bol_line.cost_profit_ids:
                    cost_total = cost_total + bol_cost_profit_line.cost_total
                    sale_total = sale_total + bol_cost_profit_line.sale_total
                    cost_profit_ids.append({
                        'product_id': bol_cost_profit_line.product_id.id,
                        'product_name': bol_cost_profit_line.product_name,
                        'costing': bol_cost_profit_line.cost_total,
                        'billing': bol_cost_profit_line.sale_total,
                    })
            for booking_cost_profit_line in doc.cost_profit_ids:
                cost_total = cost_total + booking_cost_profit_line.cost_total
                sale_total = sale_total + booking_cost_profit_line.sale_total
                cost_profit_ids.append({
                    'product_id': booking_cost_profit_line.product_id.id,
                    'product_name': booking_cost_profit_line.product_name,
                    'costing': booking_cost_profit_line.cost_total,
                    'billing': booking_cost_profit_line.sale_total,
                })

            cost_profit_ids = sorted(cost_profit_ids, key=lambda x: x['product_id'])
            """
            for invoice in invoices:
                if invoice.type == 'in_invoice':
                    type = 'Vendor Bill'
                if invoice.type == 'out_invoice':
                    type = 'Customer Invoice'
                invoice_ids.append({
                    'type': type,
                    'partner_id': invoice.partner_id.name,
                    'number': invoice.number,
                    'currency_id': invoice.currency_id.name,
                    'amount_total': float(invoice.amount_total),
                })
            """


            margin = 0
            if cost_total == 0:
                margin = sale_total*100
            if cost_total > 0:
                margin = sale_total*100/cost_total
            profit = sale_total - cost_total

            info_ids.append({
                'cost_total': cost_total,
                'sale_total': sale_total,
                'margin': margin,
                'profit': profit,
            })
            print(cost_profit_ids)
            #print(invoice_ids)
            #print(docs)
        return{
            'doc_ids': docs.ids,
            'doc_model': 'freight.booking',
            'docs': docs,
            'cost_profit_ids1': cost_profit_ids,
            'invoice_ids1': invoice_ids,
            'info_ids1': info_ids,
        }
