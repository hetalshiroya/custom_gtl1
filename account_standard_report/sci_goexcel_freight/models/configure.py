from odoo import models, fields, api
from odoo.exceptions import Warning


class CommodityType(models.Model):
    _name = 'freight.commodity'
    _description = 'Commodity'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class DangerousGoods(models.Model):
    _name = 'freight.dangerous.goods'
    _description = 'Dangerous Goods'

    name = fields.Char(string='DG Name')
    un_class = fields.Char(string='UN Class')
    division = fields.Char(string='Division')
    classification = fields.Char(string='Classification')

    active = fields.Boolean(string='Active', default=True)

    @api.multi
    def name_get(self):
        result = []
        #name = ''
        for dg in self:
            name = dg.un_class + ' ' + dg.division + ' ' + dg.classification
            print("name_get=" + name)
            result.append((dg.id, name))

        return result

class ShipmentBookingStatus(models.Model):
    _name = 'freight.status.shipment'
    _description = 'Shipment Booking Status'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class LinerBookingStatus(models.Model):
    _name = 'freight.status.liner'
    _description = 'Liner Booking Status'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class Port(models.Model):
    _name = 'freight.ports'
    _description = 'Ports'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    country_id = fields.Many2one('res.country', string="Country")
    active = fields.Boolean(string='Active', default=True)

    # @api.constrains('is_ocean', 'is_air')
    # def _check_port(self):
    #     for port in self:
    #         if not port.is_ocean and not port.is_air:
    #             raise Warning("Please Check at least one port!!")


class FreightAirport(models.Model):
    _name = 'freight.airport'
    _description = 'Airport'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    country_id = fields.Many2one('res.country', string="Country")
    # icao = fields.Char(string="ICAO",
    #                    help="International Civil Aviation Organization")
    active = fields.Boolean(string='Active', default=True)

class AirlineFlight(models.Model):
    _name = 'airline.flight'
    _description = 'flight'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    airline = fields.Many2one('res.partner', string="Airline")
    #airline = fields.Many2one('freight.airlines', string="Airline")
    # icao = fields.Char(string="ICAO",
    #                    help="International Civil Aviation Organization")
    active = fields.Boolean(string='Active', default=True)


class Incoterm(models.Model):
    _name = 'freight.incoterm'
    _description = 'Incoterm'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class Containers(models.Model):
    _name = 'freight.containers'
    _description = 'Containers'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    status = fields.Selection([('available', 'Available'),
                               ('reserve', 'Reserve')],
                              default='available')
    size = fields.Float(string='Size',
                        help="Maximum Size Handling Capacity")
    size_uom_id = fields.Many2one('uom.uom', string="Size UOM")
    volume = fields.Float(string='Volume',
                          help="Maximum Volume(M3) Handling Capacity")
    weight = fields.Float(string="Weight",
                          help="Maximum Weight(KG) Handling Capacity")
    #is_container = fields.Boolean(string='Is Container?', default=True)

    @api.constrains('size', 'volume', 'weight')
    def _check_container_capacity(self):
        for cont in self:
            if cont.size < 0.0 or cont.volume < 0.0 or cont.weight < 0.0:
                raise Warning("You can't enter negative value!!")


class Vessels(models.Model):
    _name = 'freight.vessels'
    _description = 'Vessels(Boat) Details.'

    name = fields.Char(string='Name')
    code = fields.Char(string='ID')
    liner_vessel = fields.Many2one('res.partner', string="Liner")
    country_id = fields.Many2one('res.country', string="Country")
    note = fields.Text(string='Note')
    active = fields.Boolean(string='Active', default=True)
    # transport = fields.Selection([('land', 'Land'),
    #                               ('ocean', 'Ocean'),
    #                               ('air', 'Air')],
    #                              default="Ocean")


class AcceptHour(models.Model):
    _name = 'accept.hour'
    _description = 'Accept_Hour'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)


class FreightProductCategory(models.Model):
    _name = 'freight.product.category'
    _description = 'Product Category'

    type = fields.Char(string='Type', help="Container, Commodity, etc")
    product_category = fields.Many2one('product.category', string='Product Category')
    active = fields.Boolean(string='Active', default=True)


class BookingConfirmationRemark(models.Model):
    _name = 'freight.booking.confirmation.remark'
    _description = 'Booking Confirmation Remark'

    type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string='Cargo Type')
    booking_confirmation_remark = fields.Text(string='Booking Confirmation Remark')