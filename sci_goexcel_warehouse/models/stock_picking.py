# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tallysheet_reference = fields.Many2one('warehouse.tally.sheet', string='JobSheet Ref.', track_visibility='onchange')
    #attention = fields.Char(string='ATTN', track_visibility='onchange')
    owner_id = fields.Many2one('res.partner', string='Customer', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Customer")
    scheduled_date = fields.Datetime(string='Receipt/Loading Date', related='tallysheet_reference.receipt_date')
    pickup_date = fields.Datetime(string='Pickup Date', track_visibility='onchange')
    owner = fields.Many2one('res.users', string="Owner", track_visibility='onchange')
    #delivered = fields.Date(string='Delivered', track_visibility='onchange')
    date_arrived = fields.Date(string='Date Delivered', track_visibility='onchange', help='Expected Delivered Time')
    delivery_to = fields.Many2one('res.partner', string='Delivery To', track_visibility='onchange')
    delivery_to_address_input = fields.Text(string='Delivery To Address', track_visibility='onchange')
    delivery_to_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    pickup_from = fields.Many2one('res.partner', string='Pick-Up From', track_visibility='onchange')
    pickup_from_address_input = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    pickup_from_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    delivery_instruction = fields.Text('Delivery Instruction', track_visibility='onchange')
    customer_reference_no = fields.Char(string='Customer Ref. No', related='tallysheet_reference.customer_reference_no')
    shipment_type = fields.Selection(string='Shipment Type', related='tallysheet_reference.shipment_type')
    packing_type = fields.Many2one(string='Packing Type', related='tallysheet_reference.packing_type')
    job_scope = fields.Many2one(string='Job Scope', related='tallysheet_reference.job_scope')
    packing_on_pallet = fields.Many2one(string='Packing on Pallet', related='tallysheet_reference.packing_on_pallet')
    container_product_id = fields.Many2one(string='Container Size', related='tallysheet_reference.container_product_id')
    container_qty = fields.Integer(string='Container Qty', related='tallysheet_reference.container_qty')
    #total_packages = fields.Integer(string='Total Packages', related='tallysheet_reference.total_packages')
    cargo_type = fields.Selection(string='Cargo Type', related='tallysheet_reference.cargo_type')
    unstuff_date = fields.Datetime(string='Unstuff Date', track_visibility='onchange', copy=False,
                                   index=True)
    date_done = fields.Datetime(string='Completion Date', copy=False, readonly=True, help="Date at which the transfer has been processed or cancelled.")
    transporter = fields.Many2one('res.partner', string='Transporter Company',
                                  help="The Party who transport the goods from one place to another",
                                  track_visibility='onchange')
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    driver = fields.Char(string="Driver", track_visibility='onchange')
    google_drive_attachments_ids = fields.One2many('google.drive.attachments', 'stock_picking_id', string="Documents")
    folder_id = fields.Char()

    @api.onchange('delivery_to')
    def onchange_delivery_to(self):
        adr = ''
        if self.delivery_to:
            adr += self.delivery_to.name + "\n"
            if self.delivery_to.street:
                adr += self.delivery_to.street
            if self.delivery_to.street2:
                adr += ' ' + self.delivery_to.street2
            if self.delivery_to.zip:
                adr += ' ' + self.delivery_to.zip
            if self.delivery_to.city:
                adr += ' ' + self.delivery_to.city
            if self.delivery_to.state_id:
                adr += ', ' + self.delivery_to.state_id.name
            if self.delivery_to.country_id:
                adr += ', ' + self.delivery_to.country_id.name + "\n"
            if not self.delivery_to.country_id:
                adr += "\n"
            if self.delivery_to.phone:
                adr += 'Phone: ' + self.delivery_to.phone
            elif self.delivery_to.mobile:
                adr += '. Mobile: ' + self.delivery_to.mobile
            # if self.delivery_to.country_id:
            #     adr += ', ' + self.delivery_to.country_id.name
            # _logger.warning("adr" + adr)
            self.delivery_to_address_input = adr


    @api.onchange('date_done', 'unstuff_date')
    def _onchange_unstuff_date(self):
        if self.unstuff_date or self.date_done:
            tallysheet = self.env['warehouse.tally.sheet'].browse(self.tallysheet_reference.id)
            if tallysheet:
                for move_line in self.move_ids_without_package:
                    for line in tallysheet.container_line_ids:
                        if move_line.product_id.id == line.product.id:
                            value = {
                                'container_no': move_line.container_no,
                                'seal_no': move_line.seal_no,
                                'marking': move_line.marking,
                                'inventory_marking': move_line.inventory_marking,
                                'receipt_date': self.date_done,
                                'unstuff_date': self.unstuff_date,
                                'dim_length': move_line.dim_length,
                                'dim_width': move_line.dim_width,
                                'dim_height': move_line.dim_height,
                            }
                            if tallysheet:
                                tallysheet.write({
                                    'container_line_ids': [
                                        (1, line.id, value),
                                    ]
                                })


    @api.multi
    def auto_fill_done_qty_from_reserved_qty(self):
        print('auto_fill_done_qty_from_reserved_qty')
        for picking in self:
            for move_line in picking.move_ids_without_package:
                if move_line.product_uom_qty and move_line.product_uom_qty > 0:
                    #print('product_uom_qty: ' + str(move_line.product_uom_qty))
                    #move_line._action_confirm()
                    #move_line._action_assign()
                    move_line_id = {
                        'move_id': move_line.id,
                        'picking_id': picking.id,
                        'product_id': move_line.product_id.id,
                        'product_uom_id': move_line.product_uom.id,
                        #'product_uom_qty': move_line.product_uom_qty,
                        'qty_done': move_line.product_uom_qty,
                         'location_id': move_line.location_id.id,
                         'location_dest_id': move_line.location_dest_id,
                         'owner_id': move_line.picking_id.owner_id.id,
                    }
                    move_line.move_line_ids = [(0, 0, move_line_id)]
                    #move_line._action_done()
        #picking._action_confirm()
        #picking._action_assign()
        self.write({'date_done': fields.Datetime.now()})
                    #move._action_done()
                #if move_line.product_uom_qty and move_line.product_uom_qty > 0:
                    #print('product_uom_qty: ' + str(move_line.product_uom_qty))
                    #move_line.qty_done = move_line.product_uom_qty
                    #print('qty_done: ' + str(move_line.qty_done))
                # for move_line_id in move_line.move_line_ids:
                #     print('product_uom_qty 1: ' + str(move_line.product_uom_qty))
                #     print('product_uom_qty 2: ' + str(move_line_id.product_uom_qty))
                #     if move_line.product_uom_qty and move_line.product_uom_qty > 0:
                #         move_line_id.qty_done = move_line.product_uom_qty
                #     elif move_line_id.product_uom_qty and move_line_id.product_uom_qty > 0:
                #         move_line_id.qty_done = move_line_id.product_uom_qty
                        # for move_line_id in move_line.move_line_ids:
                        #     if move_line_id.product_uom_qty and move_line_id.product_uom_qty > 0:
                        #         print('product_uom_qty: ' + str(move_line_id.product_uom_qty))
                        #         move_line_id.qty_done = move_line_id.product_uom_qty
                        #         print('qty_done: ' + str(move_line_id.qty_done))


    # @api.multi
    # def write(self, vals):
    #     print('stockpicking write')
    #     if self.picking_type_id == 2:
    #         vals['note'] = self.with_context().env.user.company_id.invoice_note
    #         print('write DO note')
    #     res = super(StockPicking, self).write(vals)
    #     return res

    @api.model
    def create(self, vals):
        #print('stockpicking create')
        #if self.picking_type_id.id == 2:
        if vals.get("picking_type_id") is not None:
            pick_up_id = vals.get("picking_type_id")
            #print('pick_up_id=' + str(pick_up_id))
            if pick_up_id == 2:
                vals['note'] = self.with_context().env.user.company_id.do_note
                #print('write DO note=' + self.with_context().env.user.company_id.do_note)

        res = super(StockPicking, self).create(vals)
        return res

    # @api.multi
    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     # do the things here
    #     _logger.warning('button_validate')
    #     tallysheet = self.env['stock.picking'].search([
    #         ('tallysheet_reference', '=', self.tallysheet_reference.id),
    #     ])
    #     for container_lines in tallysheet.container_line_ids:
    #
    #
    #     return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    container_product_id = fields.Many2one('product.product', string='Container Size', track_visibility='onchange')
    container_no = fields.Char(string="Container No.", track_visibility='onchange')

    marking = fields.Text(string="Marking/Label", track_visibility='onchange')
    inventory_marking = fields.Text(string="Inventory Marking", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    dim_length = fields.Float(string='Length', help="Length", default="0.00", track_visibility='onchange')
    dim_width = fields.Float(string='Width', default="0.00", help="Width", track_visibility='onchange')
    dim_height = fields.Float(string='Height', default="0.00", help="Height", track_visibility='onchange')

    volume = fields.Float(string="Volume",
                          help="Volume", track_visibility='onchange')
    volume_uom = fields.Many2one('uom.uom', string="Vol. UoM", track_visibility='onchange')
    total_volume = fields.Float(string="Total Vol.", compute="_compute_total_volume",
                                help="Total Volume", track_visibility='onchange')
    total_volume_uom = fields.Many2one('uom.uom', string="UoM", track_visibility='onchange')
    remark_line = fields.Text(string='Remark', track_visibility='onchange')


    @api.depends('volume', 'quantity_done', 'dim_length', 'dim_width', 'dim_height')
    def _compute_total_volume(self):
        for line in self:
            if line.volume or line.quantity_done:
                # _logger.warning("_compute_volume length:" + str(line.actual_dim_width_uom.name))
                # _logger.warning("_compute_volume volume:" + str(line.volume_uom.name))
                line.total_volume = line.volume * line.quantity_done
            if line.dim_length or line.dim_width or line.dim_height:
                line.total_volume = line.dim_length * line.dim_width * line.dim_height * line.quantity_done

    @api.multi
    @api.depends('move_line_ids.product_qty')
    def _compute_reserved_availability(self):
        # print(' _compute_reserved_availability')
        for rec in self:
            rec.reserved_availability = rec.product_uom_qty


    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        # print(' _compute_reserved_availability')
        if self.product_uom_qty and self.product_uom_qty > 0:
            self.reserved_availability = self.product_uom_qty



    def _action_done(self):
        self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = self.exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_todo = self.env['stock.move']

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or move.quantity_done <= 0:
                continue
            # extra move will not be merged in mrp
            if not move.picking_id:
                moves_todo |= move
            moves_todo |= move._create_extra_move()

        # Split moves where necessary and move quants
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move = move._split(qty_split)
                for move_line in move.move_line_ids:
                    if move_line.product_qty and move_line.qty_done:
                        # FIXME: there will be an issue if the move was partially available
                        # By decreasing `product_qty`, we free the reservation.
                        # FIXME: if qty_done > product_qty, this could raise if nothing is in stock
                        try:
                            move_line.write({'product_uom_qty': move_line.qty_done})
                        except UserError:
                            pass
                move._unreserve_initial_demand(new_move)
        moves_todo.mapped('move_line_ids')._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})
        moves_todo.mapped('move_dest_ids')._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        # if picking:
        #     picking._create_backorder()
        return moves_todo