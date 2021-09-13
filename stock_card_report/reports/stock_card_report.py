# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import datetime


class StockCardView(models.TransientModel):
    _name = 'stock.card.view'
    _description = 'Stock Card View'
    _order = 'date'

    date = fields.Datetime()
    date_in = fields.Datetime()
    date_out = fields.Datetime()
    job_no = fields.Char()
    doc_no = fields.Char()
    product_id = fields.Many2one(comodel_name='product.product')
    total_volume_uom = fields.Many2one(comodel_name='uom.uom')
    product_qty = fields.Float()
    product_uom_qty = fields.Float()
    product_uom = fields.Many2one(comodel_name='uom.uom')
    reference = fields.Char()
    location_id = fields.Many2one(comodel_name='stock.location')
    location_dest_id = fields.Many2one(comodel_name='stock.location')
    is_initial = fields.Boolean()
    product_in = fields.Float()
    product_out = fields.Float()
    customer = fields.Many2one('res.partner')
    name = fields.Text()
    volume = fields.Float()


class StockCardReport(models.TransientModel):
    _name = 'report.stock.card.report'
    _description = 'Stock Card Report'

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()

    product_ids = fields.Many2many(
        comodel_name='product.product',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
    )
    customer = fields.Many2one('res.partner')

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name='stock.card.view',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    def _compute_results(self):
        print('_compute_results')
        self.ensure_one()
        date_from = self.date_from or '0001-01-01'
        self.date_to = self.date_to or fields.Date.context_today(self)
        #print('_compute_results customer=' + self.customer.name)
        #print('_compute_results customer id=' + str(self.customer.id))
        #locations = self.env['stock.location'].search(
        #    [('id', 'child_of', [self.location_id.id])])
        self._cr.execute("""
                       SELECT ts.job_no, move.product_id, move.name, move.total_volume_uom, cl.volume, pick.name as doc_no,
                            case when pick.picking_type_id = 1
                            then pick.date_done end as date_in,
                            case when pick.picking_type_id = 1
                            then move.product_uom_qty end as product_in,
                            case when pick.picking_type_id = 2
                            then pick.date_done end as date_out,
                            case when pick.picking_type_id = 2
                            then move.product_uom_qty end as product_out 
                        FROM warehouse_tally_sheet ts
                            join stock_picking pick on ts.id = pick.tallysheet_reference
                            join stock_move move on pick.id = move.picking_id
                            left join warehouse_container_line cl on cl.container_line_id = ts.id
                        WHERE pick.owner_id = %s and pick.state = 'done' and CAST(pick.date_done AS date) >= %s
                            and CAST(pick.date_done AS date) <= %s 
                        GROUP BY ts.job_no, pick.picking_type_id, pick.name, move.product_id, move.name, move.total_volume_uom, pick.date_done, move.product_uom_qty, cl.volume
                        ORDER BY ts.job_no, move.product_id, pick.date_done;
                    """, (self.customer.id, date_from, self.date_to))
        # self._cr.execute("""
        #          SELECT move.date, move.product_id, move.product_qty,
        #              move.product_uom_qty, move.product_uom, move.reference,
        #              move.location_id, move.location_dest_id, move.partner_id,
        #              case when move.partner_id = %s
        #                  then move.product_qty end as product_in,
        #              case when move.partner_id = %s
        #                  then move.product_qty end as product_out,
        #              case when move.date < %s then True else False end as is_initial
        #          FROM stock_move move
        #          WHERE move.state = 'done' and CAST(move.date AS date) <= %s
        #          ORDER BY move.date, move.reference
        #      """, (
        #     self.customer.id, self.customer.id, date_from, self.date_to))
        # self._cr.execute("""
        #     SELECT move.date, move.product_id, move.product_qty,
        #         move.product_uom_qty, move.product_uom, move.reference,
        #         move.location_id, move.location_dest_id,
        #         case when move.location_dest_id in %s
        #             then move.product_qty end as product_in,
        #         case when move.location_id in %s
        #             then move.product_qty end as product_out,
        #         case when move.date < %s then True else False end as is_initial
        #     FROM stock_move move
        #     WHERE (move.location_id in %s or move.location_dest_id in %s)
        #         and move.state = 'done' and move.product_id in %s
        #         and CAST(move.date AS date) <= %s
        #     ORDER BY move.date, move.reference
        # """, (
        #     tuple(locations.ids), tuple(locations.ids), date_from,
        #     tuple(locations.ids), tuple(locations.ids),
        #     tuple(self.product_ids.ids), self.date_to))
        #print('_compute_results customer before dicfetchall')
        stock_card_results = self._cr.dictfetchall()
        #print('_compute_results customer after dicfetchall')
        #if stock_card_results:
        #    print('_compute_results stock_card_results=' + str(len(stock_card_results)))
        ReportLine = self.env['stock.card.view']
        self.results = [ReportLine.new(line).id for line in stock_card_results]


    @api.multi
    def _get_initial(self, product_line):
        #print('_get_initial')
        product_input_qty = sum(product_line.mapped('product_in'))
        product_output_qty = sum(product_line.mapped('product_out'))
        return product_input_qty - product_output_qty

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        action = report_type == 'xlsx' and self.env.ref(
            'stock_card_report.action_stock_card_report_xlsx') or \
            self.env.ref('stock_card_report.action_stock_card_report_pdf')
        return action.report_action(self, config=False)

    def _get_html(self):
        print(' _get_html')
        result = {}
        rcontext = {}
        report = self.browse(self._context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'stock_card_report.report_stock_card_report_html').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()
