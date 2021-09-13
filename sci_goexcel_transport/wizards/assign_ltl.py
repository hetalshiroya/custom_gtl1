from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo import exceptions

#transient model
class AssignLTL(models.TransientModel):

    _name = 'rft.assign.ltl'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # = fields.Many2one('transport.rft', string='RFT Reference')
    #trip_lines = fields.Many2one('dispatch.trip', string="Trip", track_visibility='onchange')
    trip_lines = fields.One2many('ltl.trip.line', 'ltl_trip_line', string="LTL Line", copy=False, auto_join=True)
    #required_date_time = fields.Datetime(string='Required Date Time', track_visibility='onchange')
    #manifest_line_ids_ltl = fields.One2many('trip.manifest.line.ltl', string="LTL")
    #
    #
    # @api.onchange('required_date_time', 'vehicle', 'driver_id')
    # def _get_lines(self):
    @api.model
    def default_get(self, fields):
        #_logger.warning('in default_get')
        result = super(AssignLTL, self).default_get(fields)
        trip_lines = self.env['dispatch.trip'].search([('dispatch_trip_status', '=', '01'),
                ('load_type', '=', 'ltl'),])
        # rtf_assign_ltl = self.env['rft.assign.ltl']
        # rtf_assign_ltl_val = {
        #     'trip_status': '01',
        #
        # }
        # rtf_assign = rtf_assign_ltl.create(rtf_assign_ltl_val)

        trip_list = []
        for trip_line in trip_lines:
            trip_list.append({
                'ltl_trip_line': self.id,
                'trip_no': trip_line.trip_no,
                'required_date_time': trip_line.required_date_time,
                'plan_departure_date_time': trip_line.plan_departure_date_time,
                'plan_arrival_date_time': trip_line.plan_arrival_date_time,
                'pickup_from_address_input': trip_line.pickup_from_address_input,
                'delivery_to_address_input': trip_line.delivery_to_address_input,
                'vehicle': trip_line.vehicle,
                'driver_id': trip_line.driver_id,
                'trip_route': trip_line.trip_route,
                'elapsed_day': trip_line.elapsed_day,
                'dispatch_trip_status': trip_line.dispatch_trip_status,
            })
        #_logger.warning('trip_list len=' + str(len(trip_list)))
        # result.update({
        #     'trip_lines': trip_list
        # })
        result['trip_lines'] = trip_list
        result = self._convert_to_write(result)
        return result

    #
    #
    # @api.multi
    # def action_assign_trip_ltl(self):

        #get the rft
        # rft = self.env['transport.rft'].browse(self.env.context.get('rft_id'))
        # _logger.warning("RFT line len: " + str(len(rft.container_line_ids)))
        # add_to_trip_checked = False
        # _logger.warning("self.trip_lines len: " + str(len(self.trip_lines)))
        #
        # #get the selected ltl trip in the wizard
        # for trip_line in self.trip_lines:
        #     _logger.warning("trip no: " + str(trip_line.trip_no))
        #     _logger.warning("trip_line: " + str(trip_line))
        #     if trip_line.add_to_trip is True:
        #         add_to_trip_checked = True
        #         _logger.warning("trip no: " + str(trip_line.trip_no))
        #         trips = self.env['dispatch.trip'].search([('trip_no', '=', trip_line.trip_no)])
        #         _logger.warning("trips len: " + str(len(trips)))
        #         _logger.warning("trip id: " + str(trips.id))
        #         for line in rft.container_line_ids:
        #             _logger.warning("RFT line id: " + str(line.id))
        #             #get the trip load
        #             trip_load_list = []
        #             trip_ltl_line = trips.manifest_line_ids_ltl
        #             trip_load_list.append({
        #                 'rft_reference_line': rft.id,
        #                 'manifest_line_id_ltl': trips.id,
        #                 'pickup_from_line': rft.pickup_from.id or False,
        #                 'pickup_from_address_input_line': rft.pickup_from_address_input or '',
        #                 'delivery_to_line': rft.delivery_to.id or False,
        #                 'delivery_to_address_input_line': rft.delivery_to_address_input or '',
        #                 'packages_no': line.packages_no or 0,
        #                 'exp_gross_weight': line.exp_gross_weight or 0,
        #                 'required_date_time_line': line.required_date_time_line or False,
        #                 'accept_hour_line': line.accept_hour_line.id or False,
        #                 'remark_line': line.remark_line or '',
        #             })
        #             trip_ltl_line.write({'manifest_line_ids_ltl': trip_load_list or False})
        #        # trips[0].manifest_line_ids_ltl = trip_ltl_line
        #             line.trip_reference = trips.id
        # if add_to_trip_checked is False:
        #     raise exceptions.ValidationError('Please select at least 1 trip to Add !')
        # else:
        #     rft.rft_status = '03'


    @api.multi
    def action_do_nothing(self):
        _logger.warning('Do nothing')


class LTLTripLine(models.TransientModel):
    _name = "ltl.trip.line"

    ltl_trip_line = fields.Many2one('rft.assign.ltl', string='Trip Manifest Line', required=True, ondelete='cascade',
                                    index=True, copy=False)

    add_to_trip = fields.Boolean('Add to Trip?', default=False)
    trip_no = fields.Char(string='Trip No')
    required_date_time = fields.Datetime(string='Required Date Time')
    plan_departure_date_time = fields.Datetime(string='Planned Departure Date Time')
    plan_arrival_date_time = fields.Datetime(string='Planned Arrival Date Time')
    pickup_from_address_input = fields.Text(string='Pick-Up Address')
    delivery_to_address_input = fields.Text(string='Delivery To Address')
    vehicle = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', string='Driver')
    trip_route = fields.Many2one('trip.route', string='Trip Route')
    elapsed_day = fields.Char(string='Elapsed Days')
    dispatch_trip_status = fields.Selection([('01', 'Draft'),
                                    ('02', 'Confirmed'),
                                    ('03', 'In Transit'),
                                    ('04', 'Done'), ('05', 'Cancelled')], string="Trip Status")


    # @api.onchange('add_to_trip')
    # def onchange_add_to_trip(self):
    #     _logger.warning("trip no: " + str(self.trip_no))
    #     trips = self.env['dispatch.trip'].search([('trip_no', '=', self.trip_no)])
    #     _logger.warning("trips len: " + str(len(trips)))
    #     if len(trips) > 0:
    #         #self.ltl_trip_line.trip_lines = trips
    #         # get the rft
    #         rft = self.env['transport.rft'].browse(self.env.context.get('rft_id'))
    #         _logger.warning("RFT line len: " + str(len(rft.container_line_ids)))
    #         trip_manifest_obj = self.env['trip.manifest.line.ltl']
    #         for line in rft.container_line_ids:
    #             _logger.warning("RFT line id: " + str(line.id))
    #             # get the trip load
    #             trip_load_list = []
    #             trip_ltl_line = trips.manifest_line_ids_ltl.ids
    #             trip_ltl = trip_manifest_obj.create({
    #                 'rft_reference_line': rft.id,
    #                 'manifest_line_id_ltl': trips.id,
    #                 'pickup_from_line': rft.pickup_from.id or False,
    #                 'pickup_from_address_input_line': rft.pickup_from_address_input or '',
    #                 'delivery_to_line': rft.delivery_to.id or False,
    #                 'delivery_to_address_input_line': rft.delivery_to_address_input or '',
    #                 'packages_no': line.packages_no or 0,
    #                 'exp_gross_weight': line.exp_gross_weight or 0,
    #                 'required_date_time_line': line.required_date_time_line or False,
    #                 'accept_hour_line': line.accept_hour_line.id or False,
    #                 'remark_line': line.remark_line or '',
    #             })
    #
    #             trip_ltl_line.append(trip_ltl.id)
    #             trips.manifest_line_ids_ltl = [(6,0,trip_ltl_line)]
    #             # trips[0].manifest_line_ids_ltl = trip_ltl_line
    #             line.trip_reference = trips.id
    #         # if add_to_trip_checked is False:
    #         #     raise exceptions.ValidationError('Please select at least 1 trip to Add !')
    #         # else:
    #             rft.rft_status = '03'

    @api.onchange('add_to_trip')
    def onchange_add_to_trip(self):
        #_logger.warning("trip no: " + str(self.trip_no))
        trips = self.env['dispatch.trip'].search([('trip_no', '=', self.trip_no)])
        if len(trips) > 0:
           # trip_obj = self.env['dispatch.trip']
            trip_manifest_obj = self.env['trip.manifest.line.ltl']
            rft = self.env['transport.rft'].browse(self.env.context.get('rft_id'))
            #_logger.warning("RFT line len: " + str(len(rft.container_line_ids)))
            #trip = trip_obj.create(trip_val)
            for line in rft.container_line_ids:
                # _logger.warning('action_copy_to_booking 1')
                #           if line.container_product_id:
                # _logger.warning('action_copy_to_booking 2')
                trip_ltl_line = trips.manifest_line_ids_ltl.ids
                trip_manifest_line = trip_manifest_obj.create({
                    'rft_reference_line': rft.id,
                    'manifest_line_id_ltl': trips.id,
                    'pickup_from_line': rft.pickup_from.id or False,
                    'pickup_from_address_input_line': rft.pickup_from_address_input or '',
                    'delivery_to_line': rft.delivery_to.id or False,
                    'delivery_to_address_input_line': rft.delivery_to_address_input or '',
                    'packages_no': line.packages_no or 0,
                    'exp_gross_weight': line.exp_gross_weight or 0,
                    'required_date_time_line': line.required_date_time_line or False,
                    'accept_hour_line': line.accept_hour_line.id or False,
                    'remark_line': line.remark_line or '',

                })
                # trip.write({'manifest_line_ids': trip_manifest_line or False})
            #    trips.write({'manifest_line_ids_ltl': trip_manifest_line or False})
                trip_ltl_line.append(trip_manifest_line.id)
                trips.manifest_line_ids_ltl = [(6, 0, trip_ltl_line)]
                #line.trip_reference = trips.id
                line.write({'trip_reference': trips.id or False})
           #rft.rft_status = '03'
            rft.write({'rft_status': '03'})
