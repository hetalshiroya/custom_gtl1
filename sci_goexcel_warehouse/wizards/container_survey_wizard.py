from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

class ContainerSurveyWizard(models.TransientModel):
    _name = 'container.survey.wizard'

    #split_booking_no = fields.Char(string='Split Booking No', index=True)
    container_line_survey_ids2 = fields.One2many('container.survey.line.wizard', 'container_survey_line_id2',
                                                 string="Container Survey Form")
    warehouse_container_line_id2 = fields.Many2one('warehouse.container.line')

    @api.model
    def default_get(self, fields):
        # _logger.warning('in default_get')
        result = super(ContainerSurveyWizard, self).default_get(fields)
        container_line_id = self.env.context.get('container_line_id')
        container_line = self.env['warehouse.container.line'].browse(container_line_id)
        result.update({'container_line_survey_ids2': container_line,
                       })
        container_line_list = []
        for container_line_survey in container_line.container_line_survey_ids2:
            container_line_list.append({
                'container_door': container_line_survey.container_door,
                'container_panel': container_line_survey.container_panel,
                'front_panel': container_line_survey.front_panel,
                'internal_floor': container_line_survey.internal_floor,
                'remark_line': container_line_survey.remark_line,
            })
        result['container_line_survey_ids2'] = container_line_list
        result = self._convert_to_write(result)
        return result

    @api.multi
    def action_create_container_survey(self):
        container_line_id = self.env.context.get('container_line_id')
        tally_sheet_id = self.env.context.get('tally_sheet_id')
        tally_sheet = self.env['warehouse.tally.sheet'].browse(tally_sheet_id)
        container_line = self.env['warehouse.container.line'].browse(container_line_id)
        container_survey_line_obj = self.env['warehouse.container.survey.line']
        for line in container_line.container_line_survey_ids2:
            line.unlink()
        for container_line_survey in self.container_line_survey_ids2:
            if not container_line_survey.created:
                container_line_survey_val = {
                    'container_survey_line_id2': container_line.id,
                    'container_survey_line_id': tally_sheet.id,
                    'container_door': container_line_survey.container_door,
                    'container_panel': container_line_survey.container_panel,
                    'front_panel': container_line_survey.front_panel,
                    'internal_floor': container_line_survey.internal_floor,
                    'remark_line': container_line_survey.remark_line,
                    'created':True,
                    }
                container_survey_line_obj.create(container_line_survey_val)


class ContainerSurveyLineWizard(models.TransientModel):
    """Split Booking Model."""

    _name = 'container.survey.line.wizard'
    container_survey_line_id2 = fields.Many2one('container.survey.wizard', 'Container Survey')

    sequence = fields.Integer(string="sequence")
    #container_no = fields.Char(string="Container No.", track_visibility='onchange')
    #container_product_id = fields.Many2one('product.product', string='Container', track_visibility='onchange')

    container_door = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Door',
                                      track_visibility='onchange')
    container_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Left/Right Panel',
                                       track_visibility='onchange')
    front_panel = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Front Panel',
                                   track_visibility='onchange')
    internal_floor = fields.Selection([('good', 'Good'), ('bad', 'Bad')], string='Internal Floor',
                                      track_visibility='onchange')
    remark_line = fields.Text(string='Remark', track_visibility='onchange')
    created = fields.Boolean('Created', default=False)