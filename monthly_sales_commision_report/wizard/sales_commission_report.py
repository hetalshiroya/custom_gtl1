# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models, _
import xlwt
import io
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class CommissionXlsReport(models.TransientModel):
    _name = "commission.xls.report"
    _description = "Commission Xls Report"

    file = fields.Binary("Click On Download Link To Download Xls File",
                         readonly=True)
    name = fields.Char("Name", size=32, invisible=True,
                       default='Financial_Report.xls')


class MonthlySalesCommissionReport(models.TransientModel):
    _name = 'monthly.sales.commission.report'

    date_range = fields.Selection([('current', 'Current Month'), (
        'last', 'Last Month'), ('custom_date', 'Custom Date')], string="Date Range", default='current')
    start_date = fields.Date(
        string="Start Date", default=datetime.now().date() + relativedelta(day=1))
    end_date = fields.Date(string="End Date", default=datetime.now(
    ).date() + relativedelta(day=1, months=+1, days=-1))

    @api.depends('date_range')
    @api.onchange('date_range')
    def onchange_date_range(self):
        if self.date_range:
            if self.date_range == 'current':
                self.start_date = datetime.now().date() + relativedelta(day=1)
                self.end_date = datetime.now().date() + relativedelta(day=1, months=+1, days=-1)
            if self.date_range == 'last':
                self.start_date = datetime.now().date() + relativedelta(day=1, months=-1)
                self.end_date = datetime.now().date() + relativedelta(day=1, days=-1)
            if self.date_range == 'custom_date':
                self.start_date = datetime.now().date()
                self.end_date = datetime.now().date()

    @api.multi
    def sales_commssion_excel_report(self):
        filename = str(datetime.now().strftime("%d-%m-%Y")) + '.xls'
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet("Monthly Sales Commission")
        style = xlwt.easyxf(
            'font:height 200, bold True, name Arial;align: horiz center; ')
        row_count = 0
        worksheet.write_merge(row_count, row_count, 2, 5,
                              "Monthly Sales Commission Export Report", style)

        row_count += 2
        start_date = self.start_date.strftime("%Y-%m-%d")
        worksheet.write(row_count, 2, 'Start Date', style)
        worksheet.write(row_count, 3, start_date, style)
        end_date = self.end_date.strftime("%Y-%m-%d")
        worksheet.write(row_count, 4, 'End Date', style)
        worksheet.write(row_count, 5, end_date, style)

        row_count += 3
        worksheet.write(row_count, 0, 'Salesperson', style)
        worksheet.write(row_count, 1, 'Customer', style)
        worksheet.write(row_count, 2, 'Analytic Account', style)
        worksheet.write(row_count, 3, 'Invoice Date', style)
        worksheet.write(row_count, 4, 'Invoice No', style)
        worksheet.write(row_count, 5, 'Revenue', style)
        worksheet.write(row_count, 6, 'Payment Amount', style)
        worksheet.write(row_count, 7, 'Cost', style)
        worksheet.write(row_count, 8, 'Gross Profit', style)

        invoice_lines = self.env['account.invoice.line'].search(
            [('invoice_id.state', 'in', ('open', 'paid')), ('invoice_id.type', '=', 'out_invoice'),
             ('invoice_id.date_invoice', '>=', self.start_date),
             ('invoice_id.date_invoice', '<=', self.end_date)])
        bill_lines = self.env['account.invoice.line'].search(
            [('invoice_id.state', 'in', ('open', 'paid')), ('invoice_id.type', '=', 'in_invoice'),
             ('invoice_id.date_invoice', '>=', self.start_date),
             ('invoice_id.date_invoice', '<=', self.end_date)])
        if not invoice_lines:
            raise UserError(('No records found for the selected date.'))
        analytic_dict = {}
        for line in invoice_lines:
            if line.account_analytic_id.id:
                analytic_dict.update({line.account_analytic_id.name: {}})
        for key, val in analytic_dict.items():
            for line in invoice_lines:
                if key == line.account_analytic_id.name:
                    analytic_line = self.env['account.analytic.line'].search([
                        ('account_id', '=', line.account_analytic_id.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date)])
                    payment_amount = 0.0
                    if line.invoice_id.state == 'paid':
                        payment_amount += float(line.price_total)
                    revenue_amount = sum(
                        [a.amount for a in analytic_line if a.amount > 0.0])
                    cost_amount = sum(
                        [abs(a.amount) for a in analytic_line if a.amount < 0.0])
                    if not val:
                        val.update({
                            'salesperson': line.invoice_id.user_id.name,
                            'customer': line.invoice_id.partner_id.name,
                            'invoice_date': line.invoice_id.date_invoice.strftime("%Y-%m-%d"),
                            'invoice_no': line.invoice_id.number,
                            'revenue': revenue_amount,
                            'payment_amount': payment_amount,
                            'cost': cost_amount,
                            'profit': revenue_amount - cost_amount})
                    else:
                        if val['salesperson'] != line.invoice_id.user_id.name:
                            val['salesperson'] += ', ' + \
                                line.invoice_id.user_id.name
                        if val['customer'] != line.invoice_id.partner_id.name:
                            val['customer'] += ', ' + \
                                line.invoice_id.partner_id.name
                        if val['invoice_date'] != line.invoice_id.date_invoice.strftime("%Y-%m-%d"):
                            val['invoice_date'] += ', ' + \
                                line.invoice_id.date_invoice.strftime(
                                    "%Y-%m-%d")
                        if val['invoice_no'] != line.invoice_id.number:
                            val['invoice_no'] += ', ' + \
                                line.invoice_id.number
                        val['payment_amount'] += payment_amount
                        val['revenue'] = revenue_amount
                        val['cost'] = cost_amount
                        val['profit'] = revenue_amount - cost_amount
                    if line.currency_id and not line.currency_id == self.env.user.company_id.currency_id:
                        currency = line.company_id.currency_id
                        val['revenue'] = currency._convert(abs(
                            val['revenue']), self.env.user.company_id.currency_id, self.env.user.company_id, fields.Date.today())
                        val['payment_amount'] = currency._convert(abs(
                            val['payment_amount']), self.env.user.company_id.currency_id, self.env.user.company_id, fields.Date.today())
                        val['cost'] = currency._convert(abs(
                            val['cost']), self.env.user.company_id.currency_id, self.env.user.company_id, fields.Date.today())
                        val['profit'] = currency._convert(abs(
                            val['profit']), self.env.user.company_id.currency_id, self.env.user.company_id, fields.Date.today())
#             for line in bill_lines:
#                 if key == line.account_analytic_id.name:
#                     if not val:
#                         val.update({
#                             'cost': float(line.price_total) or 0.0})
#                     else:
#                         val['cost'] += float(line.price_total)
#                 if line.currency_id and not line.currency_id == self.env.user.company_id.currency_id:
#                     currency = line.company_id.currency_id
#                     val['cost'] = currency._convert(abs(
#                         val['cost']), self.env.user.company_id.currency_id, self.env.user.company_id, fields.Date.today())
#                 val['profit'] = val['revenue'] - val['cost']
            row_count += 1
            worksheet.write(row_count, 0, val['salesperson'] or '')
            worksheet.write(row_count, 1, val['customer'] or '')
            worksheet.write(row_count, 2, key or '')
            worksheet.write(
                row_count, 3, val['invoice_date'] or '')
            worksheet.write(
                row_count, 4, val['invoice_no'] or '')
            worksheet.write(row_count, 5, val['revenue'] or 0.0)
            worksheet.write(row_count, 6, val['payment_amount'] or 0.0)
            worksheet.write(row_count, 7, val['cost'] or 0.0)
            worksheet.write(row_count, 8, val['profit'] or 0.0)

        worksheet.col(0).width = 256 * 20
        worksheet.col(1).width = 256 * 20
        worksheet.col(2).width = 256 * 20
        worksheet.col(3).width = 256 * 20
        worksheet.col(4).width = 256 * 20
        worksheet.col(5).width = 256 * 20
        worksheet.col(6).width = 256 * 20
        worksheet.col(7).width = 256 * 18
        worksheet.col(8).width = 256 * 20

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data1 = fp.read()
        fp.close()
        file_res = base64.b64encode(data1)
        rep_obj = self.env['commission.xls.report']
        report_rec = rep_obj.create({'file': file_res, 'name': filename})
        return {
            'name': _('Sales Commission Xls'),
            'res_id': report_rec.id,
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'commission.xls.report',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
