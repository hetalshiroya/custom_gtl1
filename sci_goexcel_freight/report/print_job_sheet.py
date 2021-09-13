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
    _name = 'report.sci_goexcel_freight.report_job_sheet_details'
    _description = "Print Job Sheet"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['freight.booking'].browse(docids)
        cost_profit_ids = []
        invoice_ids = []
        for doc in docs:
            print('_get_report_values doc=' + str(doc))
            bol = self.env['freight.bol'].search([('booking_ref', '=', doc.id)])
            invoices = self.env['account.invoice'].search([('freight_booking', '=', doc.id)])
            for bol_line in bol:
                for bol_cost_profit_line in bol_line.cost_profit_ids:
                    cost_profit_ids.append({
                        'product_name': bol_cost_profit_line.product_name,
                        'costing': bol_cost_profit_line.cost_total,
                        'billing': bol_cost_profit_line.sale_total,
                    })
            for booking_cost_profit_line in doc.cost_profit_ids:
                cost_profit_ids.append({
                    'product_name': booking_cost_profit_line.product_name,
                    'costing': booking_cost_profit_line.cost_total,
                    'billing': booking_cost_profit_line.sale_total,
                })
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
            print(cost_profit_ids)
            print(invoice_ids)
            print(docs)
        return{
            'doc_ids': docs.ids,
            'doc_model': 'freight.booking',
            'docs': docs,
            'cost_profit_ids1': cost_profit_ids,
            'invoice_ids1': invoice_ids,
        }
