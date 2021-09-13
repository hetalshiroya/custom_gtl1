# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models,_
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo.exceptions import UserError, ValidationError


class StockCardReportWizard(models.TransientModel):
    _name = 'stock.card.report.wizard'
    _description = 'Stock Card Report Wizard'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Period',
    )
    date_from = fields.Date(
        string='Start Date',
    )
    date_to = fields.Date(
        string='End Date',
    )
    # TS - customer
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        #required=True,
    )
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        #required=True,
    )
    #TS - customer
    customer = fields.Many2one('res.partner', string='Customer')

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'stock_card_report.action_report_stock_card_report_html')
        vals = action.read()[0]
        context = vals.get('context', {})
        if isinstance(context, pycompat.string_types):
            context = safe_eval(context)
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        context['active_id'] = report.id
        context['active_ids'] = report.ids
        vals['context'] = context
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_stock_card_report(self):
        self.ensure_one()
        #print('customer=' + self.customer.name)
        # TS - customer
        if not self.customer:
            raise ValidationError(_('Please select the Customer!!'))
        if not self.date_from:
            raise ValidationError(_('Please select the Date From!!'))
        if not self.date_to:
            raise ValidationError(_('Please select the Date To!!'))
        #print('_prepare_stock_card_report')
        return {
            'date_from': self.date_from,
            'date_to': self.date_to or fields.Date.context_today(self),
            'product_ids': [(6, 0, self.product_ids.ids)],
            'location_id': self.location_id.id,
            'customer': self.customer.id,
        }

    def _export(self, report_type):
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)
