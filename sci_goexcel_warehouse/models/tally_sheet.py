from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
import logging

_logger = logging.getLogger(__name__)


class WarehouseTallySheet(models.Model):
    # tally sheet is actually the job sheet.
    _name = 'warehouse.tally.sheet'
    _description = 'Warehouse Job Sheet'
    _order = 'job_no desc, write_date desc'
    color = fields.Integer('Color Index', default=0, store=False)
    _inherit = ['mail.thread', 'mail.activity.mixin']

    job_status = fields.Selection([('01', 'Draft'),
                                   ('02', 'Confirmed'), ('03', 'Done'), ('05', 'In Progress'),('04', 'Cancelled')], string="Job Status",
                                  default="01", copy=False,
                                  track_visibility='onchange', store=True)

    # origin = fields.Char(string='Source Document',
    #                      help="Reference of the document that linked to Packing.")
    job_no = fields.Char(string='Job No', copy=False, readonly=True, index=True)
    receipt_date = fields.Datetime(string='Receipt Date', track_visibility='onchange', copy=False,
                                   index=True)
    sq_reference = fields.Many2one('sale.order', string='S.Q Reference', track_visibility='onchange', copy=False,
                                   index=True)
    # elapsed_day = fields.Char(string='Elapsed Days', copy=False, store=True)
    customer_reference_no = fields.Char(string='Customer Ref. No', track_visibility='onchange')
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')
    customer = fields.Many2one('res.partner', string='Customer', track_visibility='onchange')
    shipment_type = fields.Selection([('import', 'Import'), ('export', 'Export')], string="Shipment Type",
                                     track_visibility='onchange')
    invoice_status = fields.Selection([('01', 'New'),
                                       ('02', 'Partially Invoiced'),
                                       ('03', 'Fully Invoiced')],
                                      string="Invoice Status", default="01", copy=False,
                                      track_visibility='onchange')
    invoice_paid_status = fields.Selection([('01', 'New'),
                                       ('02', 'Partially Paid'),
                                       ('03', 'Fully Paid')],
                                      string="Paid Status", default="01", copy=False,
                                      track_visibility='onchange')
    # seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    # job_scope = fields.Many2many('warehouse.job.scope', string='Job Scope', track_visibility='onchange')
    # packing_type = fields.Many2many('warehouse.packing.type', string='Packing Type', track_visibility='onchange')
    # sorting_by = fields.Many2many('warehouse.sorting.by', string='Sorting By', track_visibility='onchange')
    # packing_on_pallet = fields.Many2many('warehouse.packing.on.pallet', string='Packing on Pallet', track_visibility='onchange')
    job_scope = fields.Many2one('warehouse.job.scope', string='Job Scope', track_visibility='onchange')
    packing_type = fields.Many2one('warehouse.packing.type', string='Packing Type', track_visibility='onchange')
    sorting_by = fields.Many2one('warehouse.sorting.by', string='Sorting By', track_visibility='onchange')
    packing_on_pallet = fields.Many2one('warehouse.packing.on.pallet', string='Packing on Pallet',
                                        track_visibility='onchange')
    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    container_qty = fields.Integer(string='Container Qty', track_visibility='onchange', compute='_get_container_count', store=True)
    total_packages = fields.Integer(string='Total Packages', track_visibility='onchange', compute='_compute_total_packages', store=True)
    cargo_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type', default="fcl", track_visibility='onchange')

    remark = fields.Text(string='Remarks', track_visibility='onchange')
    container_line_ids = fields.One2many('warehouse.container.line', 'container_line_id', string="Container", copy=True,
                                         auto_join=True)
    container_survey_line_ids = fields.One2many('warehouse.container.survey.line', 'container_survey_line_id',
                                                string="Container Survey", copy=True,
                                                auto_join=True)
    container_gatepass_line_ids = fields.One2many('warehouse.gate.pass.line', 'container_gatepass_line_id',
                                                string="Container Survey", copy=True,
                                                auto_join=True)
    cost_profit_ids = fields.One2many('warehouse.cost.profit', 'tallysheet_id', string="Cost & Profit",
                                      copy=True, auto_join=True, track_visibility='always')
    receipt_count = fields.Integer(string='Stock In Count', compute='_get_receipt_count')
    do_count = fields.Integer(string='Stock Out Count', compute='_get_do_count')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", track_visibility='always', copy=False)
    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id,
                            track_visibility='onchange')
    sales_person = fields.Many2one('res.users', string="Salesperson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)
    name = fields.Char(compute="name_get", store=True, readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced_count', copy=False)
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_get_bill_count', copy=False)
    loading_plan_count = fields.Integer(string='Loading Plan Count', compute='_get_loading_plan_count', copy=False)
    gate_pass_count = fields.Integer(string='Gate Pass Count', compute='_get_gate_pass_count', copy=False)
    google_drive_attachments_ids = fields.One2many('google.drive.attachments', 'tallysheet_id', string="Documents")
    folder_id = fields.Char()

    @api.onchange('container_line_ids')
    def _onchange_container_line_ids(self):
        for line in self.container_line_ids:
            line.warehouse_location = self.receipt_picking_type_id.id


    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    @api.model
    def create(self, vals):
        vals['job_no'] = self.env['ir.sequence'].next_by_code('tallysheet')
        res = super(WarehouseTallySheet, self).create(vals)
        return res

    @api.multi
    def name_get(self):
        result = []
        for tallysheet in self:
            name = str(tallysheet.job_no)
        result.append((tallysheet.id, name))
        return result

    @api.multi
    def action_cancel_tallysheet(self):
        self.job_status = '04'

    @api.model
    def _default_picking_receive(self):
        type_obj = self.env['stock.picking.type']
        warehouse = self.env.user.context_default_warehouse_id
        print('warehouse receive:' + str(warehouse.id))
        # company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        # types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)], limit=1)
        # if not types:
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id)])
        return types[:1]

    @api.model
    def _default_picking_delivery(self):
        type_obj = self.env['stock.picking.type']
        warehouse = self.env.user.context_default_warehouse_id
        # _logger.warning('warehouse delivery:' + str(warehouse.id))
        types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id', '=', warehouse.id)])
        return types[:4]

    # picking.type is operation type in warehouse, type=in for incoming (receipt, QA, stock)
    receipt_picking_type_id = fields.Many2one('stock.picking.type', 'Receipt',
                                              default=_default_picking_receive,
                                              help="This will determine picking type of incoming shipment")
    delivery_picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',
                                               default=_default_picking_delivery,
                                               help="This will determine picking type of outgoing shipment")

    @api.multi
    def action_create_pick_list(self):
        # Create receipt
        # _logger.warning('receipt_picking_type_id:' + str(self.receipt_picking_type_id))
        # _logger.warning('delivery_picking_type_id:' + str(self.delivery_picking_type_id))
        if self.container_line_ids is False:
            raise exceptions.ValidationError('Please create some container lines!!!')

        # warehouse = self.env.user.context_default_warehouse_id
        # for container_line in self.container_line_ids:
        pick = {
            'picking_type_id': self.receipt_picking_type_id.id,
            # 'partner_id': self.customer.id,
            'owner_id': self.customer.id,
            'origin': self.job_no,
            'tallysheet_reference': self.id,
            'location_dest_id': self.receipt_picking_type_id.default_location_dest_id.id,
            'location_id': self.customer.property_stock_supplier.id,
        }
        #print('self.receipt_picking_type_id.id=' +  str(self.receipt_picking_type_id))
        #print('self.customer=' + str(self.customer))
        #print('self.receipt_picking_type_id.default_location_dest_id=' + str(self.receipt_picking_type_id.default_location_dest_id))
        #print('self.customer.property_stock_supplier=' + str(self.customer.property_stock_supplier))
        picking = self.env['stock.picking'].create(pick)
        #print('picking id=' + str(picking.id))
        #         self.invoice_picking_id = picking.id
        #         self.picking_count = len(picking)
        moves = self.container_line_ids.filtered(
            lambda r: r.product.type in ['product', 'consu'])._create_stock_moves(picking)
        move_ids = moves._action_confirm()
        move_ids._action_assign()
        # Create Delivery order
        # pick = {
        #     'picking_type_id': self.delivery_picking_type_id.id,
        #     # 'partner_id': self.partner_id.id,
        #     'origin': self.job_no,
        #     'tallysheet_reference': self.id,
        #     'owner_id': self.customer.id,
        #     'location_dest_id': self.customer.property_stock_customer.id,
        #     'location_id': self.delivery_picking_type_id.default_location_src_id.id
        # }
        # picking = self.env['stock.picking'].create(pick)
        # moves = self.container_line_ids.filtered(
        #     lambda r: r.product.type in ['product', 'consu'])._create_stock_transfer(picking)
        # move_ids = moves._action_confirm()
        # move_ids._action_assign()
        # picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        self.job_status = '02'

    @api.multi
    def action_view_receipt(self):
        for operation in self:
            receipt = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.receipt_picking_type_id.id),
                ('origin', '=', operation.job_no),
                ('state', '!=', 'cancel'),
            ])

            if len(receipt)>1:
                views = [(self.env.ref('stock.vpicktree').id, 'tree'),
                         (self.env.ref('stock.view_picking_form').id, 'form')]
                return {
                    'name': 'Tally Sheet',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': False,
                    'res_model': 'stock.picking',
                    'views': views,
                    'domain': [('id', 'in', receipt.ids),('picking_type_id','=', 1)],
                    'type': 'ir.actions.act_window',
                    #'target': 'popup',  # readonly mode
                }
            elif len(receipt) == 1:
                views = [(self.env.ref('stock.view_picking_form').id, 'form')]
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': views,
                    'res_model': 'stock.picking',
                    'res_id': receipt.id or False,  # readonly mode
                    #'domain': [('picking_type_id','=', 1)],
                    'type': 'ir.actions.act_window',
                    'target': 'popup',  # readonly mode
                }
        # return result

    @api.multi
    def action_view_do(self):
        for operation in self:
            do = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.delivery_picking_type_id.id),
                ('origin', '=', operation.job_no),
                ('state', '!=', 'cancel'),
            ])
            if len(do)>1:
                views = [(self.env.ref('stock.vpicktree').id, 'tree'),
                         (self.env.ref('stock.view_picking_form').id, 'form')]
                return {
                    'name': 'Loading Plan',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': False,
                    'res_model': 'stock.picking',
                    'views': views,
                    'domain': [('id', 'in', do.ids),('picking_type_id','=', 2)],
                    'type': 'ir.actions.act_window',
                    #'target': 'popup',  # readonly mode
                }
            elif len(do) == 1:
                views = [(self.env.ref('stock.view_picking_form').id, 'form')]
                return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': views,
                    'res_model': 'stock.picking',
                    'res_id': do.id or False,  # readonly mode
                    #'domain': [('picking_type_id','=', 2)],
                    'type': 'ir.actions.act_window',
                    'target': 'popup',  # readonly mode
                }

    @api.multi
    def _get_do_count(self):
        print('_get_do_count')
        for operation in self:
            do = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.delivery_picking_type_id.id),
                ('origin', '=', operation.job_no),
                ('state', '!=', 'cancel'),
            ])
        #print('Receipt Count=' + str(len(do)))
        self.update({
            'do_count': len(do),
        })

    @api.multi
    def _get_receipt_count(self):
        #print('_get_receipt_count')
        for operation in self:
            receipt = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.receipt_picking_type_id.id),
                ('origin', '=', operation.job_no),
                ('state', '!=', 'cancel'),
            ])
        #print('Receipt Count=' + str(len(receipt)))
        self.update({
            'receipt_count': len(receipt),
        })

    @api.one
    @api.depends('container_line_ids')
    def _get_container_count(self):
        container_count = 0
        for operation in self:
            if operation.container_line_ids:
                container_count = len(operation.container_line_ids)

        self.update({
            'container_qty': container_count,
        })


    @api.one
    @api.depends('container_line_ids.no_of_packages')
    def _compute_total_packages(self):

        for operation in self:
            operation.total_packages = 0
            if operation.container_line_ids:
                for container_line in operation.container_line_ids:
                    operation.total_packages += container_line.no_of_packages


    @api.one
    @api.depends('cost_profit_ids.sale_total')
    def _compute_pivot_sale_total(self):
        # _logger.warning('onchange_pivot_sale_total')
        for service in self.cost_profit_ids:
            if service.product_id:
                self.pivot_sale_total = service.sale_total + self.pivot_sale_total

    @api.multi
    def copy_last_and_add_line(self):
        last_rec = self.container_line_ids.search([], order='id desc', limit=1)
        if last_rec:
            container_line_obj = self.env['warehouse.container.line']
            container_line_line = container_line_obj.create({
                'container_line_id': last_rec.container_line_id.id,
                'container_product_id': last_rec.container_product_id.id or False,
                'product': last_rec.product.id or False,
                'product_name': last_rec.product_name or '',
                'container_no': last_rec.container_no or '',
                'seal_no': last_rec.seal_no or '',
                'no_of_packages': last_rec.no_of_packages or '',
                'no_of_package_uom': last_rec.no_of_package_uom.id or False,
                'warehouse_location': last_rec.warehouse_location.id or False,
                'volume': last_rec.volume or '',
                'remark_line': last_rec.remark_line or '',
            })
            container_line_ids = self.container_line_ids.ids
            container_line_ids.append(container_line_line.id)
            self.container_line_ids = [(6, 0, container_line_ids)]

    @api.multi
    def action_create_loading_plan(self):
        # Create receipt
        if self.container_line_ids is False:
            raise exceptions.ValidationError('Please create some container lines!!!')

        pick = {
            'picking_type_id': self.delivery_picking_type_id.id,
            # 'partner_id': self.partner_id.id,
            'origin': self.job_no,
            'tallysheet_reference': self.id,
            'owner_id': self.customer.id,
            'location_dest_id': self.customer.property_stock_customer.id,
            'location_id': self.delivery_picking_type_id.default_location_src_id.id,
            #'scheduled_date': fields.Datetime.now(),
        }
        picking = self.env['stock.picking'].create(pick)
        moves = self.container_line_ids.filtered(lambda r: r.product.type in ['product', 'consu'])._create_stock_transfer(picking)
        move_ids = moves._action_confirm()
        move_ids._action_assign()
        # picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        self.job_status = '02'

    # @api.multi
    # def action_create_loading_plan(self):
    #     # Returns an action that will open a form view (in a popup)
    #     self.ensure_one()
    #
    #     view = self.env.ref('sci_goexcel_warehouse.loading_plan_view_form')
    #     return {
    #         'name': 'Create Loading Plan',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'loading.plan.wizard',
    #         'views': [(view.id, 'form')],
    #         'view_id': view.id,
    #         'target': 'new',  # readonly mode
    #         'context': dict(tallysheet_id=self.id),
    #         # 'res_id': self.id,
    #
    #     }

    @api.multi
    def action_invoice(self):
        self.ensure_one()
        view = self.env.ref('sci_goexcel_warehouse.invoice_view_form_tallysheet')
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.wizard.tallysheet',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(tallysheet_id=self.id),
        }

    @api.multi
    def action_create_vendor_bill(self):
        # only lines with vendor
        vendor_po = self.cost_profit_ids.filtered(lambda c: c.vendor_id)
        # print('vendor_po=' + str(len(vendor_po)))
        po_lines = vendor_po.sorted(key=lambda p: p.vendor_id.id)
        # print('po_lines=' + str(len(po_lines)))
        vendor_count = False
        vendor_id = False
        if not self.analytic_account_id:
            values = {
                'name': '%s' % self.job_no,
                'company_id': self.company_id.id,
            }

            analytic_account = self.env['account.analytic.account'].sudo().create(values)
            self.write({'analytic_account_id': analytic_account.id})
        for line in po_lines:
            # print('line.vendor_id=' + line.vendor_id.name)
            if line.vendor_id != vendor_id:
                print('not same partner')
                vb = self.env['account.invoice']
                vendor_count = True
                vendor_id = line.vendor_id
                value = []
                filtered_vb_lines = po_lines.filtered(lambda r: r.vendor_id == vendor_id)
                for vb_line in filtered_vb_lines:
                    # print('combine lines')
                    if not vb_line.invoiced:
                        account_id = False
                        price_after_converted = vb_line.cost_price * vb_line.cost_currency_rate
                        print(vb_line)
                        print(vb_line.product_id)
                        print(vb_line.product_id.categ_id)
                        if vb_line.product_id.property_account_expense_id:
                            account_id = vb_line.product_id.property_account_expense_id
                        elif vb_line.product_id.categ_id.property_account_expense_categ_id:
                            account_id = vb_line.product_id.categ_id.property_account_expense_categ_id
                        value.append([0, 0, {
                            # 'invoice_id': vendor_bill.id or False,
                            'account_id': account_id.id or False,
                            'name': vb_line.product_id.name or '',
                            'product_id': vb_line.product_id.id or False,
                            'quantity': vb_line.cost_qty or 0.0,
                            'uom_id': vb_line.uom_id.id or False,
                            'price_unit': price_after_converted or 0.0,
                            'account_analytic_id': self.analytic_account_id.id,
                        }])
                        vb_line.invoiced = True
                if value:
                    vb.create({
                        'type': 'in_invoice',
                        'invoice_line_ids': value,
                        #  'default_purchase_id': self.booking_no,
                        'default_currency_id': self.env.user.company_id.currency_id.id,
                        'company_id': self.company_id.id,
                        'date_invoice': fields.Date.context_today(self),
                        'origin': self.job_no,
                        'partner_id': vendor_id.id,
                        'account_id': vb_line.vendor_id.property_account_payable_id.id or False,
                        'talley_sheet': self.id,
                    })
        if vendor_count is False:
            raise exceptions.ValidationError('No Vendor in Cost & Profit!!!')

    def _get_invoiced_count(self):
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('origin', '=', operation.job_no),
                ('type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
            ])

        self.update({
            'invoice_count': len(invoices),
        })

    def _get_bill_count(self):
        # vendor bill is created from booking job, vendor bill header will have the booking job id
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('origin', '=', operation.job_no),
                ('type', '=', 'in_invoice'),
                ('state', '!=', 'cancel'),
            ])
            if len(invoices) > 0:
                self.update({
                    'vendor_bill_count': len(invoices),
                })
            else:
                self.update({
                    'vendor_bill_count': len(invoices),
                })


    @api.onchange('sq_reference')
    def onchange_sq_reference(self):
        if self.sq_reference:
            sq = self.env['sale.order'].search([('id', '=', self.sq_reference.id)])
            tallysheet = self.env['warehouse.tally.sheet'].search([('job_no', '=', self.job_no)])
            if not tallysheet:
                raise exceptions.ValidationError('You must save the Job Sheet to Generate the Job No First!')
            if sq.partner_id:
                self.customer = sq.partner_id.id or False
            if sq.user_id:
                self.sales_person = sq.user_id.id
            #sq.state = 'sale'
            #if self.cost_profit_ids:
            for line in self.cost_profit_ids:
                line.unlink()
            cost_profit_obj = self.env['warehouse.cost.profit']
            for line in sq.order_line:
                if line.product_id:
                    if line.freight_foreign_price > 0.0:
                        price_unit = line.freight_foreign_price
                    else:
                        price_unit = line.price_unit
                    cost_profit_line = cost_profit_obj.create({
                        'product_id': line.product_id.id or False,
                        'product_name': line.name or False,
                        'tallysheet_id': tallysheet.id,
                        'profit_qty': line.product_uom_qty or 0,
                        'profit_currency': line.freight_currency.id,
                        'profit_currency_rate': line.freight_currency_rate or 1.0,
                        'list_price': price_unit or 0.0,
                    })
                    self.write({'cost_profit_ids': cost_profit_line or False})
            sq.state = 'sale'


    def _get_loading_plan_count(self):
        for operation in self:
            loading_plans = self.env['warehouse.loading.plan'].search([
                ('ts_reference', '=', operation.id),
            ])

        self.update({
            'loading_plan_count': len(loading_plans),
        })


    @api.multi
    def operation_invoices(self):
        """Show Invoice for specific Freight Operation smart Button."""
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('origin', '=', self.job_no),
                ('type', '=', 'out_invoice'),
            ])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _get_gate_pass_count(self):
        for operation in self:
            gatepass = self.env['warehouse.gate.pass.line'].search([
                ('container_gatepass_line_id', '=', operation.id),
            ])

        self.update({
            'gate_pass_count': len(gatepass),
        })

    # @api.multi
    # def operation_invoices(self):
    #     for operation in self:
    #         loading_plans = self.env['warehouse.loading.plan'].search([
    #             ('ts_reference', '=', operation.id),
    #         ])
    #     if len(loading_plans) > 1:
    #         #             # _logger.warning('in vendor bill length >1')
    #         #             # need to have both form and tree view so that can click on the tree to view form
    #         views = [(self.env.ref('sci_goexcel_warehouse.view_tree_warehouse_loading_plan').id, 'tree'),
    #                  (self.env.ref('sci_goexcel_warehouse.view_form_warehouse_loading_plan').id, 'form')]
    #         return {
    #             'name': 'Loading Plan',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
    #             'view_id': False,
    #             'res_model': 'warehouse.loading.plan',
    #             'views': views,
    #             # 'context': "{'type':'in_invoice'}",
    #             'domain': [('id', 'in', loading_plans.ids)],
    #             'type': 'ir.actions.act_window',
    #             # 'target': 'new',
    #         }
    #     elif len(loading_plans) == 1:
    #         # print('in vendor bill length =1')
    #         return {
    #             # 'name': self.booking_no,
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'warehouse.loading.plan',
    #             'res_id': loading_plans.id or False,  # readonly mode
    #             #  'domain': [('id', 'in', purchase_order.ids)],
    #             'type': 'ir.actions.act_window',
    #             'target': 'popup',  # readonly mode
    #         }




    @api.multi
    def operation_bill(self):
        for operation in self:
            invoices = self.env['account.invoice'].search([
                ('origin', '=', self.job_no),
                ('type', '=', 'in_invoice'),
                ('state', '!=', 'cancel'),
            ])
        # print('Vendor bill length=' + str(len(invoices)))
        if len(invoices) > 1:
            #             # _logger.warning('in vendor bill length >1')
            #             # need to have both form and tree view so that can click on the tree to view form
            views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                     (self.env.ref('account.invoice_supplier_form').id, 'form')]
            return {
                'name': 'Vendor bills',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'account.invoice',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', invoices.ids)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(invoices) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': invoices.id or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }
        else:
            print('operation_bill no VB on header')
            vbs_to_view = self.env['account.invoice']
            # vendor bill is created manually and assigned the cost by the invoice line
            billed_vbs = operation.cost_profit_ids.filtered(lambda r: r.invoiced is True)
            print('operation_bill billed_vbs=' + str(len(billed_vbs)))
            if billed_vbs:
                for billed_vb in billed_vbs:
                    invoice_lines = self.env['account.invoice.line'].search([
                        ('id', '=', billed_vb.bill_line_id.id),
                    ])
                    for invoice_line in invoice_lines:
                        vbs_to_view |= invoice_line.invoice_id

                views = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'),
                         (self.env.ref('account.invoice_supplier_form').id, 'form')]
                return {
                    'name': 'Vendor bills',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                    'view_id': False,
                    'res_model': 'account.invoice',
                    'views': views,
                    # 'context': "{'type':'in_invoice'}",
                    'domain': [('id', 'in', vbs_to_view.ids)],
                    'type': 'ir.actions.act_window',
                    # 'target': 'new',
                }

    @api.multi
    def operation_loading_plan(self):

        for operation in self:
            loading_plans = self.env['warehouse.loading.plan'].search([
                ('ts_reference', '=', operation.id),
            ])
        if len(loading_plans) > 1:
            #             # _logger.warning('in vendor bill length >1')
            #             # need to have both form and tree view so that can click on the tree to view form
            views = [(self.env.ref('sci_goexcel_warehouse.view_tree_warehouse_loading_plan').id, 'tree'),
                     (self.env.ref('sci_goexcel_warehouse.view_form_warehouse_loading_plan').id, 'form')]
            return {
                'name': 'Loading Plan',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'warehouse.loading.plan',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', loading_plans.ids)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(loading_plans) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'warehouse.loading.plan',
                'res_id': loading_plans.id or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


    @api.multi
    def operation_gate_pass(self):

        for operation in self:
            gatepass = self.env['warehouse.gate.pass.line'].search([
                ('container_gatepass_line_id', '=', operation.id),
            ])
        if len(gatepass) > 1:
            #             # _logger.warning('in vendor bill length >1')
            #             # need to have both form and tree view so that can click on the tree to view form
            views = [(self.env.ref('sci_goexcel_warehouse.view_tree_warehouse_gate_pass').id, 'tree'),
                     (self.env.ref('sci_goexcel_warehouse.view_form_warehouse_gate_pass').id, 'form')]
            return {
                'name': 'Loading Plan',
                'view_type': 'form',
                'view_mode': 'tree,form',
                # 'view_id': self.env.ref('account.invoice_supplier_tree').id,
                'view_id': False,
                'res_model': 'warehouse.gate.pass.line',
                'views': views,
                # 'context': "{'type':'in_invoice'}",
                'domain': [('id', 'in', gatepass.ids)],
                'type': 'ir.actions.act_window',
                # 'target': 'new',
            }
        elif len(gatepass) == 1:
            # print('in vendor bill length =1')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'warehouse.gate.pass.line',
                'res_id': gatepass.id or False,  # readonly mode
                #  'domain': [('id', 'in', purchase_order.ids)],
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }


class WarehouseContainerLine(models.Model):
    """Warehouse Operation Line Model."""

    _name = 'warehouse.container.line'
    _description = 'Container Line'

    container_line_id = fields.Many2one('warehouse.tally.sheet', string='Container', required=True, ondelete='cascade',
                                        index=True, copy=False)
    container_line_survey_ids2 = fields.One2many('warehouse.container.survey.line', 'container_survey_line_id2',
                                              'Container Survey Lines')
    container_line_gatepass_ids2 = fields.One2many('warehouse.gate.pass.line', 'container_gatepass_id2',
                                                 'Gate Pass Lines')
    sequence = fields.Integer(string="sequence")
    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    product = fields.Many2one('product.product', string='SKU', track_visibility='onchange')
    product_name = fields.Text(string='Description', track_visibility='onchange')
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    receipt_date = fields.Datetime(string='Receipt Date', track_visibility='onchange', copy=False,
                                   index=True)
    unstuff_date = fields.Datetime(string='Unstuff Date', track_visibility='onchange', copy=False,
                                   index=True)
    marking = fields.Text(string="Marking/Label", track_visibility='onchange')
    inventory_marking = fields.Text(string="Inventory Marking", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    no_of_packages = fields.Integer(string="No. of Packages", track_visibility='onchange')
    no_of_package_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    dim_length = fields.Float(string='Length', help="Length", default="0.00", track_visibility='onchange')
    dim_width = fields.Float(string='Width', default="0.00", help="Width", track_visibility='onchange')
    dim_height = fields.Float(string='Height', default="0.00", help="Height", track_visibility='onchange')
    add_to_loading_plan = fields.Boolean(string='Add to Loading Plan')
    # receipt_no_of_package_uom= fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')

    # no_of_package_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    warehouse_location = fields.Many2one('stock.location', string='Location', track_visibility='onchange')
    volume = fields.Float(string="Measurement",
                          help="Volume", track_visibility='onchange')
    volume_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Weight(KG)", digits=(12,4),
                                    help="Weight in kg.", track_visibility='onchange')
    exp_gross_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    total_volume = fields.Float(string="Total Vol.", compute="_compute_total_volume",
                                help="Total Volume", track_visibility='onchange')
    total_volume_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    remark_line = fields.Text(string='Remark', track_visibility='onchange')


    @api.multi
    def _get_default_container_category(self):
        container_lines = self.env['freight.product.category'].search([('type', '=ilike', 'container')])
        for container_line in container_lines:
            # _logger.warning('_get_default_container_category=' + str(container_line.product_category))
            return container_line.product_category

    container_category_id = fields.Many2one('product.category', string="Container Product Id",
                                            default=_get_default_container_category)

    # container_door = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Door', track_visibility='onchange')
    # container_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Panel', track_visibility='onchange')
    # front_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Front Panel', track_visibility='onchange')
    # internal_floor = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Internal Floor', track_visibility='onchange')
    # internal_floor = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Internal Floor', track_visibility='onchange')
    # remark_line = fields.Text(string='Remark', track_visibility='onchange')

    # total_volume_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')

    # exp_net_weight = fields.Float(string="Net Weight(KG)", help="Expected Weight in kg.", track_visibility='onchange')
    # exp_net_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    # exp_gross_weight = fields.Float(string="Gross Weight(KG)",
    #                                 help="Expected Weight in kg.", track_visibility='onchange')
    # exp_gross_weight_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')

    @api.multi
    def _compute_receipt(self):
        for operation in self:
            receipts = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.container_line_id.receipt_picking_type_id.id),
                ('origin', '=', operation.container_line_id.job_no),
                ('state', '!=', 'cancel'),
            ])
            #print('_compute_receipt=' + str(len(receipts)))
            qty = 0
            for receipt in receipts:
                filtered_recordset = receipt.move_ids_without_package.filtered(
                    lambda r: r.product_id.id == operation.product.id)
                if filtered_recordset:
                    #print('filtered_recordset' + str(filtered_recordset[0].quantity_done))
                    qty += filtered_recordset[0].quantity_done
            operation.receipt_no_of_packages = qty
    receipt_no_of_packages = fields.Float(string="Stock In Qty", compute='_compute_receipt', copy=False)



    @api.multi
    def _compute_delivered(self):
        for operation in self:
            dos = self.env['stock.picking'].search([
                ('picking_type_id', '=', operation.container_line_id.delivery_picking_type_id.id),
                ('origin', '=', operation.container_line_id.job_no),
                ('state', '!=', 'cancel'),
            ])
            #print('_compute_delivered=' + str(len(dos)))
            qty = 0
            for do in dos:
                filtered_recordset = do.move_ids_without_package.filtered(
                    lambda r: r.product_id.id == operation.product.id)
                if filtered_recordset:
                    print('filtered_recordset' + str(filtered_recordset[0].quantity_done))
                    qty += filtered_recordset[0].quantity_done
            operation.delivered_no_of_packages = qty
    delivered_no_of_packages = fields.Float(string="Stock Out Qty", compute='_compute_delivered', copy=False)

    @api.depends('volume', 'no_of_packages','dim_length', 'dim_width', 'dim_height')
    def _compute_total_volume(self):
        for line in self:
            if line.volume or line.no_of_packages:
                # _logger.warning("_compute_volume length:" + str(line.actual_dim_width_uom.name))
                # _logger.warning("_compute_volume volume:" + str(line.volume_uom.name))
                line.total_volume = line.volume * line.no_of_packages
            if line.dim_length or line.dim_width or line.dim_height:
                line.total_volume = line.dim_length * line.dim_width * line.dim_height * line.no_of_packages


    @api.onchange('product')
    def _onchange_product(self):
        vals = {}
        if self.product:
            vals['product_name'] = self.product.name
            vals['no_of_package_uom'] = self.product.uom_id.id
            vals['volume_uom'] = self.product.uom_id.id
            vals['total_volume_uom'] = self.product.uom_id.id
        if not self.container_product_id:
            if self.container_line_id.container_product_id:
                vals['container_product_id'] = self.container_line_id.container_product_id.id

        self.update(vals)

    #Receipt
    @api.multi
    def _create_stock_moves(self, picking):
        # _logger.warning('_create_stock_moves')
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        # tally_sheet = self.env.context.get('parent_id')
        # _logger.warning('tally_sheet id=' + str(tally_sheet))
        for line in self:
            if not line.no_of_packages or line.no_of_packages < 1:
                raise exceptions.ValidationError('No Of Packages must be more than 0!!!')
            # price_unit = line.price_unit
            # if line.container_no:
            #     name = line.container_no + ' ' + line.product_name or '',
            # else:
            #     name = line.product_name
            diff_quantity = line.no_of_packages
            template = {
                'name': line.product_name,
                'product_id': line.product.id,
                'product_uom': line.no_of_package_uom.id,
                'location_id': line.warehouse_location.id or False,
                'container_no': line.container_no,
                'container_product_id': line.container_product_id.id or False,
                'marking': line.marking,
                'inventory_marking': line.inventory_marking,
                'seal_no': line.seal_no,
                'dim_length': line.dim_length,
                'dim_width': line.dim_width,
                'dim_height': line.dim_height,
                'volume': line.volume,
                'volume_uom': line.volume_uom.id,
                'total_volume': line.total_volume,
                'total_volume_uom': line.total_volume_uom.id,
                # 'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                'location_dest_id': line.warehouse_location.id,
                'picking_id': picking.id,
                'move_dest_id': False,
                'state': 'draft',
                # 'owner_id': picking.owner_id.id,
                #   'company_id': line.invoice_id.company_id.id,
                'reserved_availability': diff_quantity,
                'picking_type_id': picking.picking_type_id.id,
                'procurement_id': False,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
            }
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            #template['reserved_availability'] = diff_quantity
            done += moves.create(template)

        # picking.move_line_ids.write({'owner_id': picking.owner_id.id})
        return done

    # DO
    @api.multi
    def _create_stock_transfer(self, picking):
        # _logger.warning('_create_stock_moves')
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        # tally_sheet = self.env.context.get('parent_id')
        # _logger.warning('tally_sheet id=' + str(tally_sheet))
        for line in self:
            # if line.container_no:
            #     name = line.container_no + ' ' + line.product_name or '',
            # else:
            #     name = line.product_name
            diff_quantity = line.no_of_packages
            template = {
                'name': line.product_name,
                'product_id': line.product.id,
                'product_uom': line.no_of_package_uom.id,
                'container_no': line.container_no,
                'container_product_id': line.container_product_id.id or False,
                'marking': line.marking,
                'inventory_marking': line.inventory_marking,
                'seal_no': line.seal_no,
                'dim_length': line.dim_length,
                'dim_width': line.dim_width,
                'dim_height': line.dim_height,
                'volume': line.volume,
                'volume_uom': line.volume_uom.id,
                'total_volume': line.total_volume,
                'total_volume_uom': line.total_volume_uom.id,
                'location_id': line.warehouse_location.id,
                'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
                # 'location_dest_id': self.warehouse_location.id,
                'picking_id': picking.id,
                'move_dest_id': False,
                'state': 'draft',
                # 'owner_id': picking.owner_id.id,
                #   'company_id': line.invoice_id.company_id.id,
                'reserved_availability': diff_quantity,
                'picking_type_id': picking.picking_type_id.id,
                'procurement_id': False,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
            }

            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,

            })
            template['product_uom_qty'] = diff_quantity
            #template['reserved_availability'] = diff_quantity
            done += moves.create(template)

        return done

    def action_survey_lines(self):
        #Returns an action that will open a form view (in a popup)
        self.ensure_one()

        view = self.env.ref('sci_goexcel_warehouse.container_survey_view_form')
        return {
            'name': 'Create Container Survey',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'container.survey.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(container_line_id=self.id,
                            tally_sheet_id=self.container_line_id.id),
            # 'res_id': self.id,

        }

    def action_gate_pass(self):
        #Returns an action that will open a form view (in a popup)
        self.ensure_one()

        view = self.env.ref('sci_goexcel_warehouse.gate_pass_view_form')
        return {
            'name': 'Create Gate Pass',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gate.pass.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',  # readonly mode
            'context': dict(container_line_id=self.id,
                            tally_sheet_id=self.container_line_id.id),
            # 'res_id': self.id,

        }



    # def action_create_container_survey(self):
    #     # Returns an action that will open a form view (in a popup)
    #     self.ensure_one()
    #     print("1")

    # @api.onchange('container_no')
    # def _onchange_container_no(self):
    #     _logger.warning(" _onchange_container_no:")
    #
    #     tally_sheet = self.env['warehouse.tally.sheet'].search([
    #         ('id', '=', self),
    #     ])
    #     for container_line in self:
    #         container_survey = self.env['warehouse.container.survey.line'].search([
    #              ('container_no', '=', container_line.container_no),
    #          ])
    #         _logger.warning("container_survey:" + str(len(container_survey)))
    #         if len(container_survey)==0:
    #             survey_line_obj = self.env['warehouse.container.survey.line']
    #             survey_line = survey_line_obj.create({
    #                  'container_survey_line_id': tally_sheet.id,
    #                  'container_no': container_line.container_no,
    #                  'container_product_id': container_line.container_product_id.id,
    #              })
    #             tally_sheet.write({'container_survey_line_ids': survey_line or False})

    # else:



class CostProfit(models.Model):
    _name = 'warehouse.cost.profit'
    _description = "Cost & Profit"

    sequence = fields.Integer(string="sequence")
    #operation_id = fields.Many2one('warehouse.tally.sheet', string='Operation')
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Text(string="Description")
    # qty for sales
    profit_qty = fields.Integer(string='Qty', default="1")
    list_price = fields.Float(string="Unit Price")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    profit_gst = fields.Selection([('zer', 'ZER')], string="GST", default="zer", track_visibility='onchange')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    tallysheet_id = fields.Many2one('warehouse.tally.sheet', string='Job Sheet', required=True, ondelete='cascade',
                                    index=True,copy=False)

    # company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
    #                             default=lambda self: self.env.user.company_id.id)
    # profit_currency = fields.Many2one(related='company_id.currency_id', string="Curr")
    profit_currency = fields.Many2one('res.currency', 'Currency',
                                      default=lambda self: self.env.user.company_id.currency_id.id,
                                      track_visibility='onchange')
    # profit_currency = fields.Many2one('res.currency', string="Curr")
    profit_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    # sale amount
    profit_amount = fields.Float(string="Amt",
                                 compute="_compute_profit_amount", store=True, track_visibility='onchange')
    sale_total = fields.Float(string="Total Sales",
                              compute="_compute_sale_total", store=True, track_visibility='onchange')

    cost_qty = fields.Integer(string='Qty', default="1", track_visibility='onchange')
    cost_price = fields.Float(string="Unit Price", track_visibility='onchange')
    cost_gst = fields.Selection([('zer', 'ZER')], string="Tax", default="zer", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    cost_currency = fields.Many2one('res.currency', string="Curr", required=True,
                                    default=lambda self: self.env.user.company_id.currency_id.id,
                                    track_visibility='onchange')
    cost_currency_rate = fields.Float(string='Rate', default="1.00", track_visibility='onchange')
    cost_amount = fields.Float(string="Amt",
                               compute="_compute_cost_amount", store=True, track_visibility='onchange')
    cost_total = fields.Float(string="Total Cost",
                              compute="_compute_cost_total", store=True, track_visibility='onchange')

    #   po_created = fields.Boolean(string="PO created", default=False)
    invoiced = fields.Boolean(string='Billed', copy=False)
    is_billed = fields.Char('Is Biiled?', compute='_compute_is_billed', store=True)

    added_to_invoice = fields.Boolean(string='Invoiced', copy=False)
    invoice_paid = fields.Boolean(string='Invoice Paid', copy=False)

    paid = fields.Boolean(string='Paid', copy=False)
    is_paid = fields.Char('Is Paid?', compute='_compute_is_paid', store=True)

    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    inv_line_id = fields.Many2one('account.invoice.line',
                                  string="Invoice Line")
    bill_id = fields.Many2one('account.invoice', string="Bill")
    bill_line_id = fields.Many2one('account.invoice.line', string="Bill Line")
    route_service = fields.Boolean(string='Is Route Service', default=False)
    profit_total = fields.Float(string="Total Profit",
                                compute="_compute_profit_total", store=True)
    margin_total = fields.Float(string="Margin %",
                                compute="_compute_margin_total", digits=(8, 2), store=True, group_operator="avg")

    @api.depends('profit_qty', 'list_price', )
    def _compute_profit_amount(self):
        for service in self:
            if service.product_id:
                service.profit_amount = service.profit_qty * service.list_price or 0.0

    @api.depends('cost_qty', 'cost_price')
    def _compute_cost_amount(self):
        for service in self:
            if service.product_id:
                service.cost_amount = service.cost_qty * service.cost_price or 0.0

    @api.depends('profit_amount', 'profit_currency_rate')
    def _compute_sale_total(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0

    @api.onchange('profit_currency_rate')
    def _onchange_profit_currency_rate(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0

    @api.onchange('profit_amount')
    def _onchange_profit_amount(self):
        for service in self:
            if service.product_id:
                service.sale_total = service.profit_amount * service.profit_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('cost_amount', 'cost_currency_rate')
    def _compute_cost_total(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.onchange('cost_amount')
    def _onchange_cost_amount(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.onchange('cost_currency_rate')
    def _onchange_cost_currency_rate(self):
        for service in self:
            if service.product_id:
                service.cost_total = service.cost_amount * service.cost_currency_rate or 0.0
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('cost_total', 'sale_total')
    def _compute_profit_total(self):
        for service in self:
            if service.product_id:
                service.profit_total = service.sale_total - service.cost_total or 0.0

    @api.depends('profit_total', 'sale_total')
    def _compute_margin_total(self):
        for service in self:
            if service.product_id:
                if service.sale_total > 0:
                    service.margin_total = service.profit_total / service.sale_total * 100

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'uom_id': []}}

        vals = {}
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
            vals['uom_id'] = self.product_id.uom_id
            vals['product_name'] = self.product_id.name

        self.update(vals)

        if self.product_id:
            self.update({
                'list_price': self.product_id.list_price or 0.0,
                'cost_price': self.product_id.standard_price or 0.0
            })

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        print('OnChange Vendor_ID')
        if self.vendor_id:
            if not self.invoiced:
                self.invoiced = False
                print('Invoiced False')

    @api.multi
    @api.depends('invoiced')
    def _compute_is_billed(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'Y'
                elif not cost_profit_line.invoiced:
                    cost_profit_line.is_billed = 'N'

    @api.multi
    @api.depends('paid')
    def _compute_is_paid(self):
        for cost_profit_line in self:
            if cost_profit_line.vendor_id:
                if cost_profit_line.paid:
                    cost_profit_line.is_paid = 'Y'
                elif not cost_profit_line.paid:
                    cost_profit_line.is_paid = 'N'

    @api.model
    def create(self, vals):
        # _logger.warning("in create")
        res = super(CostProfit, self).create(vals)

        # currency = self.env.user.company_id.currency_id.id
        content = ""
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("profit_qty"):
            content = content + "  \u2022 Profit Qty: " + str(vals.get("profit_qty")) + "<br/>"
        if vals.get("list_price"):
            content = content + "  \u2022 Profit Unit Rate: " + str(vals.get("list_price")) + "<br/>"
        if vals.get("profit_amount"):
            content = content + "  \u2022 Profit Amt: " + str(vals.get("profit_amount")) + "<br/>"
        if vals.get("profit_currency"):
            currency = self.env['res.currency'].search([('id', '=', vals.get("profit_currency"))])
            content = content + "  \u2022 Profit Currency: " + str(currency.name) + "<br/>"
        if vals.get("profit_currency_rate"):
            content = content + "  \u2022 Profit Currency Rate: " + str(vals.get("profit_currency_rate")) + "<br/>"
        if vals.get("sale_total"):
            content = content + "  \u2022 Total Sales: " + str(vals.get("sale_total")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Cost Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Cost Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Cost Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id.name")) + "<br/>"
        if vals.get("cost_currency"):
            currency = self.env['res.currency'].search([('id', '=', vals.get("cost_currency"))])
            content = content + "  \u2022 Cost Currency: " + str(currency.name) + "<br/>"
        if vals.get("cost_currency_rate"):
            content = content + "  \u2022 Cost Currency Rate: " + str(vals.get("cost_currency_rate")) + "<br/>"
        if vals.get("cost_total"):
            content = content + "  \u2022 Total Cost: " + str(vals.get("cost_total")) + "<br/>"
        if vals.get("profit_total"):
            content = content + "  \u2022 Total Profit: " + str(vals.get("profit_total")) + "<br/>"

        # _logger.warning("create content:" + content)
        res.tallysheet_id.message_post(body=content)
        print(self.cost_currency)
        print(self.profit_currency)
        return res

    @api.multi
    def write(self, vals):
        # _logger.warning("in write")
        res = super(CostProfit, self).write(vals)
        # _logger.warning("after super write")
        content = ""
        if vals.get("product_name"):
            content = content + "  \u2022 Description: " + str(vals.get("product_name")) + "<br/>"
        if vals.get("profit_qty"):
            content = content + "  \u2022 Profit Qty: " + str(vals.get("profit_qty")) + "<br/>"
        if vals.get("list_price"):
            content = content + "  \u2022 Profit Unit Rate: " + str(vals.get("list_price")) + "<br/>"
        if vals.get("profit_amount"):
            content = content + "  \u2022 Profit Amt: " + str(vals.get("profit_amount")) + "<br/>"
        if vals.get("profit_currency"):
            content = content + "  \u2022 Profit Currency: " + str(self.profit_currency.name) + "<br/>"
        if vals.get("profit_currency_rate"):
            content = content + "  \u2022 Profit Currency Rate: " + str(vals.get("profit_currency_rate")) + "<br/>"
        if vals.get("sale_total"):
            content = content + "  \u2022 Total Sales: " + str(vals.get("sale_total")) + "<br/>"
        if vals.get("cost_qty"):
            content = content + "  \u2022 Cost Qty: " + str(vals.get("cost_qty")) + "<br/>"
        if vals.get("cost_price"):
            content = content + "  \u2022 Cost Unit Price: " + str(vals.get("cost_price")) + "<br/>"
        if vals.get("cost_amount"):
            content = content + "  \u2022 Cost Amt: " + str(vals.get("cost_amount")) + "<br/>"
        if vals.get("vendor_id"):
            content = content + "  \u2022 Vendor: " + str(vals.get("vendor_id.name")) + "<br/>"
        if vals.get("cost_currency"):
            content = content + "  \u2022 Cost Currency: " + str(self.cost_currency.name) + "<br/>"
        if vals.get("cost_currency_rate"):
            content = content + "  \u2022 Cost Currency Rate: " + str(vals.get("cost_currency_rate")) + "<br/>"
        if vals.get("cost_total"):
            content = content + "  \u2022 Total Cost: " + str(vals.get("cost_total")) + "<br/>"
        if vals.get("profit_total"):
            content = content + "  \u2022 Total Profit: " + str(vals.get("profit_total")) + "<br/>"

        # _logger.warning("write content:" + content)
        self.tallysheet_id.message_post(body=content)

        return res


class WarehouseContainerSurveyLine(models.Model):
    """Warehouse Operation Line Model."""

    _name = 'warehouse.container.survey.line'
    _description = 'Container Survey Line'
    _order = 'container_survey_line_id, sequence, id'
    # _rec_name = 'warehouse_container_id'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    container_survey_line_id = fields.Many2one('warehouse.tally.sheet', string='Container', required=True,
                                               ondelete='cascade', index=True,
                                               copy=False)
    container_survey_line_id2 = fields.Many2one(
         'warehouse.container.line', 'Container Survey', index=True, copy=False, required=True, ondelete='cascade')
    sequence = fields.Integer(string="sequence")
    #container_no = fields.Char(string="Container No.", track_visibility='onchange')
    #container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')

    container_door = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Door',
                                      track_visibility='onchange')
    container_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Panel',
                                       track_visibility='onchange')
    front_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Front Panel',
                                   track_visibility='onchange')
    internal_floor = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Internal Floor',
                                      track_visibility='onchange')
    remark_line = fields.Text(string='Remark', track_visibility='onchange')


class WarehouseGatePassLine(models.Model):
    """Warehouse Gate Pass Line Model."""

    _name = 'warehouse.gate.pass.line'
    _description = 'Gate Pass Line'
    _order = 'container_gatepass_line_id, sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    container_gatepass_line_id = fields.Many2one('warehouse.tally.sheet', string='Job Sheet Reference', required=True,
                                               ondelete='cascade', index=True, copy=False)
    container_gatepass_id2 = fields.Many2one(
         'warehouse.container.line', 'Container GatePass', index=True, copy=False, required=True, ondelete='cascade')
    sequence = fields.Integer(string="sequence")
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    #container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')
    job_no = fields.Char(string='Gate Pass No', copy=False, readonly=True, index=True)
    time_in = fields.Datetime(string='Time In', track_visibility='onchange', index=True)
    time_out = fields.Datetime(string='Time Out', track_visibility='onchange', index=True)
    transporter = fields.Many2one('res.partner', string='Transporter Company', help="The Party who transport the goods from one place to another",
                              track_visibility='onchange')
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    driver = fields.Char(string="Driver", track_visibility='onchange')
    prepared_by = fields.Many2one('res.users', string="Prepared By", default=lambda self: self.env.user.id, track_visibility='onchange')
    received_by = fields.Many2one('res.users', string="Received By", track_visibility='onchange')
    security = fields.Char(string="Security InCharge", track_visibility='onchange')
    # ts_reference = fields.Many2one('warehouse.tally.sheet', string='Tally Sheet Ref', track_visibility='onchange', copy=False,
    #                                index=True)
    remark_line = fields.Text(string='Remark', track_visibility='onchange')
    job_status = fields.Selection([('01', 'Draft'),
                                    ('03', 'Done'), ('02', 'In Progress'), ('04', 'Cancelled')],
                                  string="Status",
                                  default="01", copy=False,
                                  track_visibility='onchange', store=True)


    @api.model
    def create(self, vals):
        vals['job_no'] = self.env['ir.sequence'].next_by_code('gatepass')
        res = super(WarehouseGatePassLine, self).create(vals)
        return res




