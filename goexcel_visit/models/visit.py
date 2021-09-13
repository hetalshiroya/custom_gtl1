from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class Visit(models.Model):
    _name = 'visit'
    _description = 'Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    color = fields.Integer('Color Index', default=0)
    _order = 'visit_id desc'

    @api.model
    def _default_visit_purpose(self):
        visit_purpose = self.env['visit.purpose'].search([('code', '=', '01')])
        return visit_purpose

    visit_status = fields.Selection([
        ('01', 'Open'),
        ('02', 'In Process'),
        ('03', 'Done'),
    ], copy=False, default='01')
    sequence = fields.Integer(string="sequence")
    customer_name = fields.Many2one('res.partner', string='Customer', track_visibility='onchange')
    contact = fields.Many2one('res.partner', string='Contact', track_visibility='onchange')
    visit_purpose = fields.Many2one('visit.purpose', default=_default_visit_purpose, string="Visit Purpose",
                                    track_visibility='onchange')
    visit_planned_start_date_time = fields.Datetime(string='Planned Start Date Time', track_visibility='onchange')
    visit_planned_end_date_time = fields.Datetime(string='Planned End Date Time', track_visibility='onchange')
    sales_person = fields.Many2one('res.users', string="Salesperson", readonly=True,
                                   default=lambda self: self.env.user.id, track_visibility='onchange')
    priority = fields.Selection([('0', 'Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High'), ('4', 'Very High')],
                                string='Priority', select=True, default='2', track_visibility='onchange')
    visit_id = fields.Char(string='Visit ID', copy=False, readonly=True, index=True)
    check_in_date_time = fields.Datetime(string='Check In Date & Time', readonly=True)
    check_out_date_time = fields.Datetime(string='Check Out Date & Time', readonly=True)
    visit_duration = fields.Float(string='Visit Duration (min)', compute="_compute_visit_duration", readonly=True,
                                  store=True)
    visit_count = fields.Integer(string='Visit Count', default=1, store=True)
    visit_duration_char = fields.Char(string='Visit Duration', readonly=True, store=True)
    destination = fields.Char(string='Destination', compute="_compute_address")
    current_location = fields.Char(string='Current Location', copy=False)
    check_in_gps_location = fields.Char(string='Check In Location')
    check_out_gps_location = fields.Char(string='Check Out Location')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, readonly=1,
                                 default=lambda self: self.env.user.company_id.id, track_visibility='onchange')
    last_visit_remark = fields.Text(string="Last Visit Remark", readonly=True)
    remark = fields.Text(string="Remark", track_visibility='onchange')
    visit_reference = fields.Char(string='Visit Reference', copy=False, readonly=True, index=True)
    next_visit_count = fields.Integer(compute='_compute_next_visit_count', store=True)
    visit_latitude = fields.Float(string='WG Latitude', related='customer_name.partner_latitude')
    visit_longitude = fields.Float(string='WG Longitude', related='customer_name.partner_longitude')
    visit_display_name = fields.Char(string='WG Name', related='customer_name.name')
    visit_phone = fields.Char(string='Phone', related='customer_name.phone')
    visit_is_company = fields.Boolean(string='Is Company', related='customer_name.is_company')
    visit_email = fields.Char(string='Email', related='customer_name.email')
    visit_street = fields.Char(string='Street', related='customer_name.street')
    visit_street2 = fields.Char(string='Street2', related='customer_name.street2')
    visit_zip = fields.Char(string='Postcode', related='customer_name.zip')
    visit_city = fields.Char(string='City', related='customer_name.city')
    visit_country_id = fields.Many2one(string='Country', related='customer_name.country_id')
    visit_state_id = fields.Many2one(string='State', related='customer_name.state_id')
    visit_type = fields.Selection(string='Type', related='customer_name.type')
    visit_image_small = fields.Binary(string='Type', related='customer_name.image_small')
    visit_image = fields.Binary(string='Type', related='customer_name.image')
    visit_color = fields.Integer(string='Color', related='customer_name.color')

    # define the format and sequence of visit ID in the visit_view.xml
    @api.model
    def create(self, vals):
        vals['visit_id'] = self.env['ir.sequence'].next_by_code('visit')
        contact = vals.get("contact")
        customer_name = vals.get("customer_name")
        last_visit_remark = vals.get("last_visit_remark")
        visit = False
        if (contact):
            visit = self.env['visit'].search([('contact', '=', contact), ('visit_status', '=', '03')]
                                             , order="check_out_date_time desc", limit=1)
        elif (customer_name):
            visit = self.env['visit'].search([('customer_name', '=', customer_name), ('visit_status', '=', '03')]
                                             , order="check_out_date_time desc", limit=1)
        if visit:
            if visit.remark and not last_visit_remark:
                vals['last_visit_remark'] = visit.remark
        res = super(Visit, self).create(vals)
        return res

    @api.multi
    def action_check_in(self):
        self.visit_status = '02'
        self.check_in_date_time = datetime.today()

    @api.multi
    def action_check_out(self):
        self.visit_status = '03'
        self.check_out_date_time = datetime.today()
        t1 = self.check_out_date_time - self.check_in_date_time
        t2 = t1.total_seconds()
        self.visit_duration = float(t2 / 60)
        days = int(t2 / 86400)
        print(days)
        daysinmin = days * 1440
        mins = int((t2 / 60) - daysinmin)
        duration = ''
        if days > 0:
            duration = duration + str(days) + ' day(s) '
        if mins > 0:
            duration = duration + str(mins) + ' min(s) '
        if days == 0 and mins == 0:
            duration = '0'
        self.visit_duration_char = duration

    @api.multi
    def action_reset_status(self):
        self.visit_status = '01'
        self.check_in_date_time = ''
        self.check_out_date_time = ''
        self.visit_duration = ''
        self.visit_duration_char = ''

    @api.multi
    def name_get(self):
        result = []
        for visit in self:
            name = str(visit.visit_id)
        result.append((visit.id, name))
        return result

    @api.one
    @api.depends('check_out_date_time')
    def _compute_visit_duration(self):
        if self.check_in_date_time and self.check_out_date_time:
            t1 = self.check_out_date_time - self.check_in_date_time
            t2 = t1.total_seconds()
            self.visit_duration = float(t2 / 60)

    @api.multi
    def _compute_next_visit_count(self):
        for visit in self:
            next_visit = self.env['visit'].search([('visit_reference', '=', visit.visit_id)])
            visit.next_visit_count = len(next_visit)

    @api.multi
    def action_next_visit(self):
        if self:
            current_date = datetime.now()
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
            date_format = datetime.strptime(str(current_date), DATETIME_FORMAT)
            visit_frequency = self.customer_name.partner_visit_frequency
            if visit_frequency:
                if visit_frequency == '01':
                    visit_planned_start_date_time = date_format + timedelta(days=7)
                if visit_frequency == '02':
                    visit_planned_start_date_time = date_format + timedelta(days=14)
                if visit_frequency == '03':
                    visit_planned_start_date_time = date_format + relativedelta(months=1)
                if visit_frequency == '04':
                    visit_planned_start_date_time = date_format + relativedelta(months=2)
                if visit_frequency == '06':
                    visit_planned_start_date_time = date_format + relativedelta(months=3)
                if visit_frequency == '07':
                    visit_planned_start_date_time = date_format + relativedelta(months=6)
                if visit_frequency == '08':
                    visit_planned_start_date_time = date_format + relativedelta(years=1)
            else:
                visit_planned_start_date_time = ''

            return {
                'name': 'Create Next Visit',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'visit',
                'target': 'new',
                'context': {'default_customer_name': self.customer_name.id,
                            'default_contact': self.contact.id,
                            'default_visit_purpose': self.visit_purpose.id,
                            'default_visit_planned_start_date_time': visit_planned_start_date_time,
                            'default_priority': self.priority,
                            'default_last_visit_remark': self.remark,
                            'default_sales_person': self.sales_person.id,
                            'default_company_id': self.company_id.id,
                            'default_destination': self.destination,
                            'default_visit_reference': self.visit_id,
                            },
            }

    @api.model
    def update_check_in_location(self, gps_location, record_id):
        #context = self.env.context
        visits = self.env['visit'].search([('id', '=', record_id)])
        for visit in visits:
            visit.check_in_gps_location = gps_location
            if visit.customer_name.partner_latitude:
                return
            else:
                coordinates = [x.strip() for x in gps_location.split(',')]
                visit.customer_name.partner_latitude = float(coordinates[0])
                visit.customer_name.partner_longitude = float(coordinates[1])


    @api.model
    def update_check_out_location(self, gps_location, record_id):
        visits = self.env['visit'].search([('id', '=', record_id)])
        for visit in visits:
            visit.check_out_gps_location = gps_location

    @api.multi
    def open_customer_map(self):
        destination = ''

    @api.multi
    def open_check_in_location(self):
        url = "https://maps.google.com/?q=" + self.check_in_gps_location
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    @api.multi
    def open_check_out_location(self):
        url = "https://maps.google.com/?q=" + self.check_out_gps_location
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    @api.one
    def _compute_address(self):
        destination = ''
        if self.customer_name:
            if self.customer_name.street:
                destination += self.customer_name.street.replace(' ', '%20')
            if self.customer_name.street2:
                destination += '%20' + self.customer_name.street2.replace(' ', '%20')
            if self.customer_name.city:
                destination += '%20' + self.customer_name.city.replace(' ', '%20')
            if self.customer_name.zip:
                destination += '%20' + self.customer_name.zip.replace(' ', '%20')
            if self.customer_name.state_id:
                destination += '%20' + self.customer_name.state_id.name.replace(' ', '%20')
            if self.customer_name.country_id:
                destination += '%20' + self.customer_name.country_id.name.replace(' ', '%20')
        self.destination = destination

    @api.onchange('visit_planned_start_date_time')
    def _onchange_visit_planned_start_date_time(self):
        if self.visit_planned_start_date_time:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            visit_planned_start_date_time = datetime.strptime(str(self.visit_planned_start_date_time), DATETIME_FORMAT)
            self.visit_planned_end_date_time = visit_planned_start_date_time + timedelta(minutes=30)

    @api.multi
    def view_next_visit(self):
        next_visit = self.env['visit'].search([
            ('visit_reference', '=', self.visit_id),
        ])
        print(next_visit)
        if len(next_visit) > 1:
            views = [(self.env.ref('goexcel_visit.view_tree_visit').id, 'tree'),
                     (self.env.ref('goexcel_visit.view_form_visit').id, 'form')]
            print("1")
            return {
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'visit',
                'views': views,
                'domain': [('id', 'in', next_visit.ids)],
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'visit',
                'res_id': next_visit.id or False,
                'type': 'ir.actions.act_window',
                'target': 'popup',
            }
