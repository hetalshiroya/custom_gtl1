from odoo import models, fields, api
from odoo.exceptions import Warning


class TransportDepot(models.Model):
    _name = 'transport.depot'
    _description = 'Depot'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    address = fields.Text(string='Address')
    contact = fields.Char(string='Contact')

    active = fields.Boolean(string='Active', default=True)


class TransportAcceptHour(models.Model):
    _name = 'transport.accept.hour'
    _description = 'Accept_Hour'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)


class VehicleLocation(models.Model):
    _name = 'vehicle.location'
    _description = 'Vehicle_Location'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)


class TripRoute(models.Model):
    _name = 'trip.route'
    _description = 'trip_route'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)


