from odoo import models, fields, api
from odoo.exceptions import Warning


class WarehouseJobScope(models.Model):
    _name = 'warehouse.job.scope'
    _description = 'Job Scope'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)



class WarehousePackingType(models.Model):
    _name = 'warehouse.packing.type'
    _description = 'Packing Type'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class WarehousePackingOnPallet(models.Model):
    _name = 'warehouse.packing.on.pallet'
    _description = 'Packing on Pallet'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)


class WarehouseSortingBy(models.Model):
    _name = 'warehouse.sorting.by'
    _description = 'Sorting By'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)



