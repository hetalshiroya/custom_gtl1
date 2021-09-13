from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

class GatePassWizard(models.TransientModel):
    _name = 'gate.pass.wizard'

    #split_booking_no = fields.Char(string='Split Booking No', index=True)
    container_line_gatepass_ids2 = fields.One2many('gate.pass.line.wizard', 'container_gatepass_line_id2',
                                                 string="Gate Pass Form")
    warehouse_container_line_id2 = fields.Many2one('warehouse.container.line')

    @api.model
    def default_get(self, fields):
        # _logger.warning('in default_get')
        result = super(GatePassWizard, self).default_get(fields)
        container_line_id = self.env.context.get('container_line_id')
        container_line = self.env['warehouse.container.line'].browse(container_line_id)
        result.update({'container_line_gatepass_ids2': container_line,
                       })
        container_line_list = []
        for container_line_gatepass in container_line.container_line_gatepass_ids2:
            container_line_list.append({
                'time_in': container_line_gatepass.time_in,
                'time_out': container_line_gatepass.time_out,
                'transporter': container_line_gatepass.transporter,
                'truck_no': container_line_gatepass.truck_no,
                'driver': container_line_gatepass.driver,
                'prepared_by': container_line_gatepass.prepared_by,
                'received_by': container_line_gatepass.received_by,
                'security': container_line_gatepass.security,
                'remark_line': container_line_gatepass.remark_line,
                # 'container_no': container_line.container_no,
                # 'seal_no': container_line.seal_no,

            })
        result['container_line_gatepass_ids2'] = container_line_list
        result = self._convert_to_write(result)
        return result

    @api.multi
    def action_create_gate_pass(self):
        container_line_id = self.env.context.get('container_line_id')
        tally_sheet_id = self.env.context.get('tally_sheet_id')
        tally_sheet = self.env['warehouse.tally.sheet'].browse(tally_sheet_id)
        container_line = self.env['warehouse.container.line'].browse(container_line_id)
        container_gatepass_line_obj = self.env['warehouse.gate.pass.line']
        for line in container_line.container_line_gatepass_ids2:
            line.unlink()
        for container_line_gatepass in self.container_line_gatepass_ids2:
            if not container_line_gatepass.created:
                container_line_gatepass_val = {
                    'container_gatepass_id2': container_line.id,
                    'container_gatepass_line_id': tally_sheet.id,
                    'time_in': container_line_gatepass.time_in,
                    'time_out': container_line_gatepass.time_out,
                    'transporter': container_line_gatepass.transporter.id or False,
                    'truck_no': container_line_gatepass.truck_no,
                    'driver': container_line_gatepass.driver,
                    'prepared_by': container_line_gatepass.prepared_by.id or False,
                    'received_by': container_line_gatepass.received_by.id or False,
                    'security': container_line_gatepass.security,
                    'remark_line': container_line_gatepass.remark_line,
                    'container_no': container_line.container_no,
                    'seal_no': container_line.seal_no,
                    #'ts_reference': tally_sheet.id,
                    'created':True,
                    }
                container_gatepass_line_obj.create(container_line_gatepass_val)


class GatePassLineWizard(models.TransientModel):
    """Split Booking Model."""

    _name = 'gate.pass.line.wizard'
    container_gatepass_line_id2 = fields.Many2one('gate.pass.wizard', 'Container Gate Pass')

    sequence = fields.Integer(string="sequence")
    time_in = fields.Datetime(string='Time In', track_visibility='onchange', index=True)
    time_out = fields.Datetime(string='Time Out', track_visibility='onchange', index=True)
    container_no = fields.Char(string="Container No.", track_visibility='onchange')
    seal_no = fields.Char(string="Seal No.", track_visibility='onchange')
    transporter = fields.Many2one('res.partner', string='Transporter Company',
                                  help="The Party who transport the goods from one place to another",
                                  track_visibility='onchange')
    truck_no = fields.Char(string="Truck No.", track_visibility='onchange')
    driver = fields.Char(string="Driver", track_visibility='onchange')
    prepared_by = fields.Many2one('res.users', string="Prepared By", default=lambda self: self.env.user.id,
                                  track_visibility='onchange')
    received_by = fields.Many2one('res.users', string="Received By", track_visibility='onchange')
    security = fields.Char(string="Security InCharge", track_visibility='onchange')

    remark_line = fields.Text(string='Remark', track_visibility='onchange')
    created = fields.Boolean('Created', default=False)
    ts_reference = fields.Many2one('warehouse.tally.sheet', string='Job Sheet Ref', track_visibility='onchange',
                                   copy=False,
                                   index=True)
    job_status = fields.Selection([('01', 'Draft'),
                                   ('03', 'Done'), ('02', 'In Progress'), ('04', 'Cancelled')],
                                  string="Status",
                                  default="01", copy=False,
                                  track_visibility='onchange', store=True)
