from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo import exceptions
import logging
_logger = logging.getLogger(__name__)


class DispatchTrip(models.Model):
    _name = 'dispatch.trip'
    _description = 'Dispatch Trip'
    #_rec_name = 'Trip'
    _order = 'required_date_time desc, write_date desc'
    color = fields.Integer('Color Index', default=0, store=False)
    _inherit = ['mail.thread', 'mail.activity.mixin']

    trip_status = fields.Selection([('01', 'Draft'),
                                   ('02', 'Confirmed'),
                                   ('03', 'In Transit'),
                                   ('04', 'Done'), ('05', 'Cancelled')], string="Trip Status", default="01", copy=False,
                                  track_visibility='onchange')
    dispatch_trip_status = fields.Selection(related='trip_status', copy=False)
    load_type = fields.Selection([('ftl', 'FTL'), ('ltl', 'LTL')], string='Load Type', default="ftl",
                                    track_visibility='onchange')

    # origin = fields.Char(string='Source Document',
    #                      help="Reference of the document that generated trip.")
    rft_reference = fields.Many2one('transport.rft', string='RFT Reference', track_visibility='onchange', copy=False)
    trip_no = fields.Char(string='Trip No', copy=False, readonly=True, index=True)
    required_date_time = fields.Datetime(string='Required Date Time', track_visibility='onchange', index=True)
    plan_departure_date_time = fields.Datetime(string='Planned Departure Date Time', track_visibility='onchange', index=True)
    plan_arrival_date_time = fields.Datetime(string='Planned Arrival Date Time', track_visibility='onchange', index=True)
    plan_trip_duration = fields.Char(string='Planned Trip Duration', track_visibility='onchange')
    #plan_departure_date = fields.Date(string='Planned Departure Date')
    #plan_arrival_date = fields.Date(string='Planned Arrival Date', index=True, track_visibility='onchange')
    actual_departure_date_time = fields.Datetime(string='Actual Departure Date Time', track_visibility='onchange')
    actual_arrival_date_time = fields.Datetime(string='Actual Arrival Date Time', track_visibility='onchange')
    actual_trip_duration = fields.Char(string='Actual Trip Duration', track_visibility='onchange')

    pickup_from = fields.Many2one('res.partner', string='Pick-Up From', track_visibility='onchange')
    pickup_from_address_input = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    #pickup_from_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    delivery_to = fields.Many2one('res.partner', string='Delivery To', track_visibility='onchange')
    delivery_to_address_input = fields.Text(string='Delivery To Address', track_visibility='onchange')
    #delivery_to_contact_name = fields.Many2one('res.partner', string='Contact Person', track_visibility='onchange')
    mileage = fields.Float(string="Mileage (KM)",
                           help="Estimated Mileage", track_visibility='onchange')
    vehicle = fields.Many2one('fleet.vehicle', string='Vehicle', track_visibility='onchange')
    driver_id = fields.Many2one('res.partner', string='Driver')
    co_driver = fields.Many2one('res.partner', string='Co-Driver', track_visibility="onchange", help='Co-Driver of the vehicle')
    trip_route = fields.Many2one('trip.route', string='Trip Route', track_visibility='onchange')
    departure_location = fields.Many2one('vehicle.location', string='Departure Location', track_visibility='onchange')
    return_location = fields.Many2one('vehicle.location', string='Return Location', track_visibility='onchange')
    elapsed_day = fields.Char(string='Elapsed Days', copy=False, store=True)
    shipping_instruction = fields.Text(string='Shipping Instruction', track_visibility='onchange', copy=False)

    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')
    manifest_line_ids = fields.One2many('trip.manifest.line', 'manifest_line_id', string="FTL", copy=False, auto_join=True, track_visibility='always')
    manifest_line_ids_ltl = fields.One2many('trip.manifest.line.ltl', 'manifest_line_id_ltl', string="LTL", copy=False, auto_join=True, track_visibility='always')
    ftl_pod_signature_attachment = fields.Binary(string="POD Signature", track_visibility='onchange', copy=False)

    packaging_line_ids = fields.One2many('trip.packaging.line', 'packaging_line_id', string="Container", copy=True,
                                         auto_join=True, track_visibility='always')
    equipment_line_ids = fields.One2many('trip.equipment.line', 'equipment_line_id', string="Equipment", copy=True,
                                         auto_join=True, track_visibility='always')
    manpower_line_ids = fields.One2many('trip.manpower.line', 'manpower_line_id', string="Manpower", copy=True,
                                        auto_join=True, track_visibility='always')
    use_packaging = fields.Boolean(string='use packaging', compute="_get_use_packaging",
                                   default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                       "sci_goexcel_transport.use_packaging"))
    use_manpower = fields.Boolean(string='use manpower', compute="_get_use_manpower",
                                  default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                      "sci_goexcel_transport.use_manpower"))
    use_equipment = fields.Boolean(string='use equipment', compute="_get_use_equipment",
                                   default=lambda self: self.env["ir.config_parameter"].sudo().get_param(
                                       "sci_goexcel_transport.use_equipment"))

    owner = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user.id,
                            track_visibility='onchange')
   # sales_person = fields.Many2one('res.users', string="Salesperson", track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        vals['trip_no'] = self.env['ir.sequence'].next_by_code('trip')
        res = super(DispatchTrip, self).create(vals)
        return res


    ### Cannot create name because web timeline doesnt support it
    # @api.multi
    # def name_get(self):
    #     result = []
    #     for trip in self:
    #         name = str(trip.trip_no)
    #     result.append((trip.id, name))
    #     return result



    @api.onchange('dispatch_trip_status')
    def onchange_dispatch_trip_status(self):
        self.trip_status = self.dispatch_trip_status
        if self.dispatch_trip_status == '03':  #In Transit
            if self.load_type == 'ftl' and self.rft_reference:
                rfts = self.env['transport.rft'].search([
                    ('id', '=', self.rft_reference.id),
                ])
                #_logger.warning('ftl rfts len=' + str(len(rfts)))
                for rft in rfts:
                    rft.write({'rft_status': '04'})
            elif self.load_type == 'ltl':
                # trip_manifest_lines = self.env['trip.manifest.line.ltl'].search([
                #     ('manifest_line_id_ltl', '=', self.id),
                # ])   #manifest_line_id_ltl
                for trip_load in self.manifest_line_ids_ltl:
                #_logger.warning('ltl trip line len=' + str(len(trip_manifest_lines)))
                    rfts = self.env['transport.rft'].search([
                        ('id', '=', trip_load.rft_reference_line.id),
                    ])
                    for rft in rfts:
                        rft.write({'rft_status': '04'})
        elif self.dispatch_trip_status == '04':  # Done
            if self.load_type == 'ftl' and self.rft_reference:
                rfts = self.env['transport.rft'].search([
                    ('id', '=', self.rft_reference.id),
                ])
                #_logger.warning('ftl rfts len=' + str(len(rfts)))
                for rft in rfts:
                    rft.write({'rft_status': '05'})
            elif self.load_type == 'ltl':
                # trip_manifest_lines = self.env['trip.manifest.line.ltl'].search([
                #     ('manifest_line_id_ltl', '=', self.id),
                # ])   #manifest_line_id_ltl
                for trip_load in self.manifest_line_ids_ltl:
                #_logger.warning('ltl trip line len=' + str(len(trip_manifest_lines)))
                    rfts = self.env['transport.rft'].search([
                        ('id', '=', trip_load.rft_reference_line.id),
                    ])
                    for rft in rfts:
                        rft.write({'rft_status': '05'})

    @api.multi
    def action_cancel_trip(self):
        self.trip_status = '05'

    @api.onchange('required_date_time')
    def _onchange_required_date_time(self):
        if self.required_date_time:
            # days = self.booking_date_time - datetime.now().date()
            diff = self.required_date_time - datetime.now()
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            self.elapsed_day = total_day

    @api.onchange('vehicle')
    def _onchange_vehicle(self):
        if self.vehicle:
            vehicles = self.env['fleet.vehicle'].search([
                ('id', '=', self.vehicle.id),
            ])
            #_logger.warning('vehicle len=' + str(len(vehicles)))
            for vehicle in vehicles:
                self.driver_id = vehicle.driver_id.id



    @api.model
    def _cron_elapsed_day_hourly(self):
        # yesterday_date = datetime.now().date()
        trips = self.env['dispatch.trip'].search([
            ('required_date_time', '>', datetime.now()),
        ])
        #_logger.warning('len rfts=' + str(len(rfts)))
        for trip in trips:
            if trip.required_date_time:
                diff = trip.required_date_time - datetime.now()
                #_logger.warning('diff:' + str(diff))
                diff_str = str(diff)
                end_pos = diff_str.find('.')
                total_day = diff_str[0:end_pos]
                trip.elapsed_day = total_day


    @api.onchange('plan_departure_date_time')
    def _onchange_plan_departure_date_time(self):
        if self.plan_departure_date_time and self.plan_arrival_date_time:
            diff = self.plan_arrival_date_time - self.plan_departure_date_time
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            self.plan_trip_duration = total_day

        if self.plan_departure_date_time is False:
            self.plan_arrival_date_time = self.plan_departure_date_time


    @api.onchange('plan_arrival_date_time')
    def _onchange_plan_arrival_date_time(self):
        if self.plan_departure_date_time and self.plan_arrival_date_time:
            diff = self.plan_arrival_date_time - self.plan_departure_date_time
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            self.plan_trip_duration = total_day



    @api.onchange('actual_departure_date_time')
    def _onchange_actual_departure_date_time(self):
        if self.actual_departure_date_time and self.actual_arrival_date_time:
            diff = self.actual_arrival_date_time - self.actual_departure_date_time
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            self.actual_trip_duration = total_day

        if self.actual_departure_date_time is False:
            self.actual_arrival_date_time = self.actual_departure_date_time

    @api.onchange('actual_arrival_date_time')
    def _onchange_actual_arrival_date_time(self):
        if self.actual_departure_date_time and self.actual_arrival_date_time:
            diff = self.actual_arrival_date_time - self.actual_departure_date_time
            diff_str = str(diff)
            end_pos = diff_str.find('.')
            total_day = diff_str[0:end_pos]
            self.actual_trip_duration = total_day

    # @api.onchange('driver_id')
    # def _onchange_driver_id(self):
    #     trips = self.env['dispatch.trip'].search(['|',
    #         ('plan_departure_date_time', '>=', self.plan_arrival_date_time), '&',
    #         ('plan_arrival_date_time', '<=', self.plan_departure_date_time),
    #         ('driver_id', '=', self.driver_id.id),
    #     ])
    #     _logger.warning('len trip=' + str(len(trips)))
    #     if len(trips) > 0:
    #         raise exceptions.ValidationError('Driver already scheduled in another trip!!!')
        #https: // www.soliantconsulting.com / blog / determining - two - date - ranges - overlap /

    @api.multi
    def _get_use_packaging(self):
        use_packaging = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_packaging")
        for record in self:
            record.use_packaging = use_packaging

    @api.multi
    def _get_use_manpower(self):
        use_manpower = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_manpower")
        #_logger.warning("use_manpower=" + str(use_manpower))
        for record in self:
            record.use_manpower = use_manpower

    @api.multi
    def _get_use_equipment(self):
        use_equipment = self.env["ir.config_parameter"].sudo().get_param("sci_goexcel_transport.use_equipment")
        #_logger.warning("use_equipment=" + str(use_equipment))
        for record in self:
            record.use_equipment = use_equipment


    @api.multi
    def action_pod_sign(self):
            view = self.env.ref('sci_goexcel_transport.pod_signature_view_form')
            return {
                # 'name': self.booking_no,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trip.pod.signature',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'type': 'ir.actions.act_window',
                'target': 'popup',  # readonly mode
            }

class TripManifestLine(models.Model):
    _name = 'trip.manifest.line'
    _description = 'Manifest Line'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    sequence = fields.Integer(string="sequence")
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    container_id = fields.Many2one('product.product', string="Container Type", track_visibility='onchange')
    manifest_line_id = fields.Many2one('dispatch.trip', string='Trip Manifest Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    # manifest_cn_no = fields.Char(string='CN', default=lambda self: self.env['ir.sequence'].next_by_code('manifest_cn'),
    #                                   copy=False, readonly=True, index=True)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')
    manifest_product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    manifest_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="No. of Packages", help="Eg, Carton", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)",
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_vol = fields.Float(string="Volume",
                           help="Volume/Dimension", track_visibility='onchange')
    container_operator_line = fields.Many2one('res.partner', string="Container Operator")
    accept_hour_line = fields.Many2one('transport.accept.hour', string="Accept Hour",
                                  help="Customer Working Hours",
                                  track_visibility='onchange')
    remark_line = fields.Text(string='Remarks', track_visibility='onchange')
    #pod_signature_file_name = fields.Char(string="POD Signature File name", track_visibility='onchange', copy=False)
    #pod_signature_attachment = fields.Binary(string="POD Signature", track_visibility='onchange',
    #                                         copy=False)
   # signature_count = fields.Integer(string='Signature Count', compute='_compute_signature_count', readonly=True)

    # @api.multi
    # def _compute_signature_count(self):
    #     if self.pod_signature_attachment:
    #         self.signature_count = 1


class TripManifestLineLTL(models.Model):
    _name = 'trip.manifest.line.ltl'
    _description = 'Manifest Line LTL'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    sequence = fields.Integer(string="sequence")
    manifest_line_id_ltl = fields.Many2one('dispatch.trip', string='Trip Manifest Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    manifest_cn_no = fields.Char(string='CN', default=lambda self: self.env['ir.sequence'].next_by_code('manifest_cn'),
                                      copy=False, readonly=True, index=True)
    rft_reference_line = fields.Many2one('transport.rft', string='RFT Reference', track_visibility='onchange',copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')
    pickup_from_line = fields.Many2one('res.partner', string='Pick-Up From', track_visibility='onchange')
    pickup_from_address_input_line = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    delivery_to_line = fields.Many2one('res.partner', string='Delivery To', track_visibility='onchange')
    delivery_to_address_input_line = fields.Text(string='Delivery To Address', track_visibility='onchange')
    #manifest_product_id = fields.Many2one('product.product', string='Product', track_visibility='onchange')
    #manifest_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="No. of Packages", help="Eg, Carton", track_visibility='onchange')
    exp_gross_weight = fields.Float(string="Gross Weight(KG)",
                                    help="Expected Weight in kg.", track_visibility='onchange')
    exp_vol = fields.Float(string="Volume",
                            help="Volume/Dimension", track_visibility='onchange')
    #container_operator_line = fields.Many2one('res.partner', string="Container Operator")
    accept_hour_line = fields.Many2one('transport.accept.hour', string="Accept Hour",
                                  help="Customer Working Hours",
                                  track_visibility='onchange')
    remark_line = fields.Text(string='Remarks', track_visibility='onchange')
    pod_signature = fields.Boolean(string='Sign', track_visibility='onchange')
    #pod_signature_file_name = fields.Char(string="POD Signature File name", track_visibility='onchange', copy=False)
    pod_signature_attachment = fields.Binary(string="POD Signature", track_visibility='onchange', copy=False)
    #signature_count = fields.Integer(string='Signature Count', compute='_compute_signature_count', readonly=True)

    # @api.multi
    # def _compute_signature_count(self):
    #     if self.pod_signature_attachment:
    #         self.signature_count = 1

    @api.multi
    @api.onchange('pod_signature')
    def onchange_pod_signature(self):
        #_logger.warning("onchange_pod_signature call wizard")
        res = self.env['ir.actions.act_window'].for_xml_id('sci_goexcel_transport', 'pod_signature_wizard')
        return res

        # return {
        #     'name': 'POD Signature',
        #     'type': 'ir.actions.act_window',
        #     'view_id': 'pod_signature_view_form',
        #     'view_mode': 'form',
        #     'res_model': 'trip.pod.signature',
        #     'target': 'new',
        # }




class TripPackagingLine(models.Model):
    _name = 'trip.packaging.line'
    _description = 'Trip Packaging Line'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    #rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    packaging_line_id = fields.Many2one('dispatch.trip', string='Trip Packaging Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    packaging_product_id = fields.Many2one('product.product', string='Packaging', track_visibility='onchange')
    packaging_product_name = fields.Text(string='Description', track_visibility='onchange')
    packages_no = fields.Integer(string="Qty", track_visibility='onchange')
    rft_reference = fields.Many2one('transport.rft', string="RFT reference", track_visibility='onchange', copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')

    @api.onchange('packaging_product_id')
    def _onchange_packaging_product_id(self):
        vals = {}
        vals['packaging_product_name'] = self.packaging_product_id.name
        self.update(vals)


class TripEquipmentLine(models.Model):
    _name = 'trip.equipment.line'
    _description = 'Trip Equipment Line'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    #rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    equipment_line_id = fields.Many2one('dispatch.trip', string='Trip Equipment Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    equipment_id = fields.Many2one('fleet.vehicle', string='Equipment & Tools', track_visibility='onchange')
    equipment_name = fields.Text(string='Description', track_visibility='onchange')
    qty = fields.Integer(string="Qty", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    rft_reference = fields.Many2one('transport.rft', string="RFT reference", track_visibility='onchange', copy=False)
    pickup_from_address_input_line = fields.Text(string='Pick-Up Address', track_visibility='onchange')
    delivery_to_address_input_line = fields.Text(string='Delivery To Address', track_visibility='onchange')
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')


    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        vals = {}
        vals['equipment_name'] = self.equipment_id.name
        self.update(vals)


class TripManPowerLine(models.Model):
    _name = 'trip.manpower.line'
    _description = 'Manpower Line'
    #_inherit = ['mail.thread', 'mail.activity.mixin']

    #rec_name = 'container_line_id'
    sequence = fields.Integer(string="sequence")
    manpower_line_id = fields.Many2one('dispatch.trip', string='Trip Manpower Line', required=True, ondelete='cascade',
                                    index=True, copy=False)
    manpower_id = fields.Many2one('product.product', string='ManPower', track_visibility='onchange')
    manpower_name = fields.Text(string='Description', track_visibility='onchange')
    qty = fields.Integer(string="Qty", track_visibility='onchange')
    vendor_id = fields.Many2one('res.partner', string="Vendor", track_visibility='onchange')
    rft_reference = fields.Many2one('transport.rft', string="RFT reference", track_visibility='onchange', copy=False)
    required_date_time_line = fields.Datetime(string='Required Date Time', track_visibility='onchange')

    remark_line = fields.Text(string='Remarks', track_visibility='onchange')

    @api.onchange('manpower_id')
    def _onchange_manpower_id(self):
        vals = {}
        vals['manpower_name'] = self.manpower_id.name
        self.update(vals)
