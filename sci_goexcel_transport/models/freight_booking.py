from odoo import api, fields, models,exceptions
import logging
_logger = logging.getLogger(__name__)


class FreightBooking(models.Model):
    _inherit = "freight.booking"

    booking_rft_count = fields.Integer(string='RFT Count', compute='_get_booking_rft_count', readonly=True)
    empty_pick_up_depot = fields.Many2one('transport.depot', string='Empty Pick Up Depot')
    empty_pick_up_depot_address = fields.Text(string='Address')
    empty_pick_up_depot_contact = fields.Char(string='Contact')
    #sq_description = fields.Char(string='SQ Description', track_visibility='onchange')

    @api.onchange('empty_pick_up_depot')
    def onchange_empty_pick_up_depot(self):
        if self.empty_pick_up_depot:
            self.empty_pick_up_depot_address = self.empty_pick_up_depot.address
            self.empty_pick_up_depot_contact = self.empty_pick_up_depot.contact


    def _get_booking_rft_count(self):
        for operation in self:
            rfts = self.env['transport.rft'].search([
                ('booking_reference', '=', operation.id),
            ])

        self.update({
            'booking_rft_count': len(rfts),
        })

    @api.multi
    def action_copy_to_rft(self):
        rft_obj = self.env['transport.rft']
        rft_container_obj = self.env['rft.container.line']
        bl_no = ''
        container_type = ''
        if self.obl_no:
            bl_no = self.obl_no
        elif self.hbl_no:
            bl_no = self.hbl_no
        if not bl_no:
            bl_no = self.booking_no
        if self.cargo_type == 'lcl':
            container_type = self.lcl_container
        elif self.cargo_type == 'fcl':
            container_type = self.container_qty
            if self.container_product_id:
                container_type = str(container_type) + 'X' + self.container_product_id.name
        if self.direction == 'export':
            rft_val = {
                'rft_status': '01',
                'shipper': self.shipper.id or False,
                'direction': self.direction or False,
                'billing_address': self.billing_address.id or False,
                'booking_reference': self.id,
                # 'pickup_from': self.shipper.id or False,
                # 'pickup_from_address_input': self.shipper_address_input or '',
                'delivery_to': self.consignee.id or False,
                'delivery_to_address_input': self.place_of_receipt or '',
                'consignee': self.consignee.id or False,
                'booking_no': bl_no,
                'scn_code': self.scn_code or '',
                'port':  self.port_of_loading.id or False,
                'commodity_type1': self.commodity_type.id or '',
                'commodity1': self.commodity1.id or '',
                'voyage_no': self.voyage_no,
                'vessel_name': self.vessel_name.id,
                'vessel_code': self.vessel_id,
                'vessel_eta_etd': self.port_of_loading_eta,
                'vessel_etd': self.port_of_discharge_eta,
                'lcl_container': container_type,
            }
        elif self.direction == 'import':
            # delivery_to = self.consignee,
            #  if self.place_of_delivery:
            #      pickup_from_address_input = self.place_of_delivery,
            #  if self.consignee_addres_input:
            #      delivery_to_address_input = self.consignee_address_input,
            # _logger.warning('action_copy_to_booking 1')
            rft_val = {
                'rft_status': '01',
                'shipper': self.shipper.id or False,
                'direction': self.direction or False,
                'billing_address': self.billing_address.id or False,
                'booking_reference': self.id,
                # 'pickup_from': self.shipper.id or False,
                # 'pickup_from_address_input': self.place_of_delivery or '',
                'delivery_to': self.consignee.id or False,
                'delivery_to_address_input': self.consignee_address_input or '',
                'port': self.port_of_discharge.id or False,
                'booking_no': bl_no,
                'scn_code': self.scn_code or '',
                'consignee': self.consignee.id or False,
                'commodity_type1': self.commodity_type.id or '',
                'commodity1': self.commodity1.id or '',
                'voyage_no': self.voyage_no,
                'vessel_name': self.vessel_name.id,
                'vessel_eta_etd': self.port_of_discharge_eta,
                'vessel_code': self.vessel_id,
                'vessel_etd': self.port_of_loading_eta,
                'lcl_container': container_type,
            }
        if self.direction == 'export':
            rft_val['pickup_from'] = self.shipper.id,
        elif self.direction == 'import':
            rft_val['delivery_to'] = self.consignee.id,

        rft = rft_obj.create(rft_val)
        if self.cargo_type == 'fcl':
            container_line = self.operation_line_ids
        else:
            # _logger.warning('action_copy_to_booking operation_line_ids2')
            container_line = self.operation_line_ids2

        for line in container_line:
            if line.container_product_id or line.container_no:
                rft_container_line = rft_container_obj.create({
                    'container_id': line.container_product_id.id or False,
                    'container_product_name': line.container_product_name or False,
                    'container_product_id': line.container_commodity_id.id or False,
                    'container_line_id': rft.id or '',
                    'container_no': line.container_no or '',
                    # 'container_product_name': line.freight_currency.id,
                    'packages_no': line.packages_no or 0.0,
                    'exp_gross_weight': line.exp_gross_weight or 0.0,
                    'exp_vol': line.exp_vol or 0.0,
                    'remark_line': line.remark or '',
                    'packages_no_uom': line.packages_no_uom.id or '',
                })
                rft.write({'container_line_ids': rft_container_line or False})




