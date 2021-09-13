from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions


class FreightBookingSubJob(models.Model):
    _name = 'freight.booking.subjob'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_name = fields.Many2one('res.partner', string='Customer')
    new_booking = fields.Selection([('new', 'Create New SubJob Booking'), ('old', 'Select Existing Booking Request')], string='Master Job or SubJob'
                                   , default='old')

    #booking_job_lines = fields.One2many('freight.booking', 'booking_job_line', string="Booking Job Line", copy=False, auto_join=True)

    @api.multi
    def action_booking_subjob(self):

 #       booking = self.env['freight.booking'].browse(self.env.context.get('master_booking_id'))
        booking_id = self.env.context.get('master_booking_id')
        booking = self.env['freight.booking'].search([('id', '=', booking_id)])
        #_logger.warning('action_booking_subjob booking id' + str(booking.id))
        if booking.booking_type == 'sub':
            raise exceptions.ValidationError('Cannot create SubJob in the SubJob!!!')
        else:
            if self.customer_name is not False:
                #_logger.warning('in action_booking_subjob')
                booking_obj = self.env['freight.booking']
                freight_booking_val = {
                    'shipment_booking_status': '01',
                    'service_type': booking.service_type or False,
                    'cargo_type': booking.cargo_type or False,
                    'direction': booking.direction or False,
                    'carrier_booking_no': booking.carrier_booking_no or False,
                    'obl_no': booking.obl_no or False,
                    'customer_name': self.customer_name.id,
                    'carrier': booking.carrier.id or False,
                    'company_id': booking.company_id.id,
                    'booking_type': 'sub',
                    'master_booking': booking.id,
                    'place_of_receipt': booking.place_of_receipt or False,
                    'port_of_loading': booking.port_of_loading.id or False,
                    'port_of_tranship': booking.port_of_tranship.id or False,
                    'port_of_discharge': booking.port_of_discharge.id or False,
                    'place_of_delivery': booking.place_of_delivery or False,
                    'place_of_receipt_ata': booking.place_of_receipt_ata or False,
                    'port_of_loading_eta': booking.port_of_loading_eta or False,
                    'port_of_tranship_eta': booking.port_of_tranship_eta or False,
                    'port_of_discharge_eta': booking.port_of_discharge_eta or False,
                    'shipment_close_date_time': booking.shipment_close_date_time or False,
                    'vessel_name': booking.vessel_name.id or False,
                    'psa_code': booking.psa_code or False,
                    'scn_code': booking.scn_code or False,
                    'vessel_id': booking.vessel_id or False,
                    'voyage_no': booking.voyage_no or False,
                    'feeder_vessel_name': booking.feeder_vessel_name or False,
                    'terminal': booking.terminal or False,
                    'principal_agent_code': booking.principal_agent_code.id or False,
                    'principal_agent_smk_code': booking.principal_agent_smk_code or False,
                    'shipping_agent_code': booking.shipping_agent_code.id or False,
                    'shipping_agent_smk_code': booking.shipping_agent_smk_code or False,
                    #'company_id': self.env.user.company_id.id,
                    # 'sales_person': self.user_id.id
                }
                subbooking = booking_obj.create(freight_booking_val)
                _logger.warning('subbooking:' + str(subbooking.booking_no))
                # #booking.booking_type = 'master'
                booking.write({'booking_type': 'master'})
                # subbooking_line = booking.subbooking_ids.ids
                # freight_subbooking_obj = self.env['freight.subbooking.line']
                # freight_subbooking_line = freight_subbooking_obj.create({
                #     'subbooking_id': subbooking.id,
                #     'cargo_type': booking.cargo_type,
                #     'customer_name': self.customer_name.id,
                # })
                # #
                # subbooking_line.append(freight_subbooking_line.id)
                # booking.subbooking_ids = [(6, 0, subbooking_line)]
                #self.write({'subbooking_ids': freight_subbooking_line or False})
            else:
                raise exceptions.ValidationError('Must Select the Customer!!!')

    @api.multi
    def _get_default_booking_list(self):
    #def _get_lines(self):
        #_logger.warning('_get_lines')
        master_booking_id = self.env.context.get('master_booking_id')
        #master_booking = self.env['freight.booking'].search([('id', '=', booking_id.id)])
        booking_lines = self.env['freight.booking'].search([('shipment_booking_status', '=', '01'),
                                                       ('direction', '=', 'export'), ('cargo_type', '=', 'lcl'),
                                                         ('booking_type', '=', False),('id', '!=', master_booking_id),])
        #('booking_type', '=', False),
        #_logger.warning('bookings len=' + str(len(booking_lines)))
        return booking_lines
        #self.booking_job_lines = booking_lines
        # booking_list = []
        # for booking_line in booking_lines:
        #     booking_list.append({
        #         'booking_job_line': booking_line.id,
        #         'shipment_booking_status': booking_line.shipment_booking_status or '',
        #         'booking_no': booking_line.booking_no or '',
        #         'direction': booking_line.direction or '',
        #         'service_type': booking_line.service_type or '',
        #         'cargo_type': booking_line.cargo_type or '',
        #         'customer_name': booking_line.customer_name.id or False,
        #         'shipper': booking_line.shipper.id or False,
        #         'consignee': booking_line.consignee or False,
        #         'booking_date_time': booking_line.booking_date_time or False,
        #         'create_date': booking_line.create_date or False,
        #         'port_of_loading': booking_line.port_of_loading.id or False,
        #         'port_of_discharge': booking_line.port_of_discharge.id or False,
        #         'sq_reference': booking_line.sq_reference.id or False,
        #         'elapsed_day_booking': booking_line.elapsed_day_booking or '',
        #     })
        #
        # result['booking_job_lines'] = booking_list
        # result = self._convert_to_write(result)
        # return result

    booking_job_lines = fields.One2many('freight.booking', 'subjob_id', default=_get_default_booking_list)


    def action_add_subjob(self):
        _logger.warning('Action add subjob')
        self.ensure_one()
        booking_id = self.env.context.get('master_booking_id')
        master_booking = self.env['freight.booking'].search([('id', '=', booking_id)])
        #_logger.warning('master booking=' + master_booking.booking_no)
        #_logger.warning('bookings len=' + str(len(self.booking_job_lines)))
        for booking_job_line in self.booking_job_lines:
            #_logger.warning('booking_job_line no=' + str(booking_job_line.booking_no))
            #_logger.warning('booking_job_line add_to_master=' + str(booking_job_line.add_to_master))
            if booking_job_line.add_to_master is True:
                #_logger.warning('add to master')
                #booking_job_line.booking_type = 'sub'
                #booking_job_line.master_booking = master_booking.id
                #booking_job_line.write({'booking_type': 'sub'})

                vals = {}
                vals['booking_type'] = 'sub'
                vals['master_booking'] = master_booking.id or False
                booking_job_line.write(vals)
                for subjob_container_line in booking_job_line.operation_line_ids2:
                    #_logger.warning('subjob_container_line')
                    operation_line_obj = self.env['freight.operations.line2']
                    master_lines = master_booking.operation_line_ids2.ids
                    op_line = operation_line_obj.create({
                       # 'operation_id2': master_booking.id,
                        'container_product_id': subjob_container_line.container_product_id.id or False,
                        'container_product_name': subjob_container_line.container_product_name or '',
                        #'subjob_no': booking_job_line.booking_no,
                        'subjob': booking_job_line.id,
                        'packages_no': subjob_container_line.packages_no or '',
                        'exp_vol': subjob_container_line.exp_vol or '',
                        'exp_gross_weight': subjob_container_line.exp_gross_weight or '',
                        'exp_net_weight': subjob_container_line.exp_net_weight or '',
                        'shipping_mark': subjob_container_line.shipping_mark or '',
                    })
                    #master_booking.operation_line_ids2 = op_line
                    #master_booking.write({'operation_line_ids2': op_line})
                    master_lines.append(op_line.id)
                    master_booking.operation_line_ids2 = [(6, 0, master_lines)]
                    #booking_job_line.write({'master_booking': master_booking.id or False})
        master_booking.write({'booking_type': 'master'})

    @api.one
    @api.depends('booking_job_lines.add_to_master')
    def _add_to_master(self):
        for booking_line in self.booking_job_lines:
            _logger.warning('add_to_master=', str(booking_line.add_to_master))


class FreightBookingLine(models.Model):
    _inherit = "freight.booking"

    add_to_master = fields.Boolean(string='Add to master', default=False, copy=False)
    subjob_id = fields.Many2one('freight.booking.subjob', 'Subjob', copy=False)

    # @api.onchange('add_to_master')
    # def onchange_add_to_master(self):
    #     _logger.warning('add_to_master=', str(self.add_to_master))