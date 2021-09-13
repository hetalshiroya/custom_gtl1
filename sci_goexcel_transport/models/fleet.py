from odoo import models, fields


class FleetVehicle(models.Model):

    _inherit = 'fleet.vehicle'

    # plan_departure_date_time = fields.Datetime(string='Planned Departure Date Time', track_visibility='onchange')
    # plan_arrival_date_time = fields.Datetime(string='Planned Arrival Date Time', track_visibility='onchange')

