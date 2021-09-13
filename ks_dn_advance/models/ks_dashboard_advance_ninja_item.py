from odoo import models, api, fields, _ , sql_db
from odoo.exceptions import ValidationError
from psycopg2 import ProgrammingError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

import json

class KsDashboardNinjaItemAdvance(models.Model):
    _inherit = 'ks_dashboard_ninja.item'

    ks_custom_query = fields.Text(string="Custom Query")
    ks_data_calculation_type = fields.Selection([('custom', 'Custom'),
                                                 ('query', 'Query')], string="Data Calculation Type", default="custom")
    ks_query_result = fields.Char(compute='ks_run_query', string="Result")
    ks_xlabels = fields.Char(string="X-Labels")
    ks_ylabels = fields.Char(string="Y-Labels")
    ks_model_id = fields.Many2one('ir.model', string='Model', required=False,
                                  domain="[('access_ids','!=',False),('transient','=',False),"
                                         "('model','not ilike','base_import%'),('model','not ilike','ir.%'),"
                                         "('model','not ilike','web_editor.%'),('model','not ilike','web_tour.%'),"
                                         "('model','!=','mail.thread'),('model','not ilike','ks_dash%')]")

    ks_list_view_layout = fields.Selection([('layout_1','Default layout'),
                                            ('layout_2','Layout 1'),
                                            ('layout_3','Layout 2'),
                                            ('layout_4','Layout 3')], string="List View Layout",
                                           default="layout_1")

    @api.depends('ks_custom_query', 'ks_data_calculation_type', 'ks_query_result', 'ks_xlabels', 'ks_ylabels',
                 'ks_bar_chart_stacked')
    def ks_get_chart_data(self):
        for rec in self:
            if rec.ks_dashboard_item_type and rec.ks_dashboard_item_type not in ['ks_tile', 'ks_list_view', 'ks_kpi']:
                if rec.ks_data_calculation_type != 'query':
                    return super(KsDashboardNinjaItemAdvance, self).ks_get_chart_data()
                else:
                    if rec.ks_query_result:
                        records = json.loads(rec.ks_query_result)
                        ks_chart_data = {'labels': [], 'domains': [], 'datasets': []}
                        if records:
                            if rec.ks_unit and rec.ks_unit_selection == 'monetary':
                                ks_chart_data['ks_selection'] = rec.ks_unit_selection
                                ks_chart_data['ks_currency'] = rec.env.user.company_id.currency_id.id
                            elif rec.ks_unit and rec.ks_unit_selection == 'custom':
                                ks_chart_data['ks_selection'] = rec.ks_unit_selection
                                if rec.ks_chart_unit:
                                    ks_chart_data['ks_field'] = rec.ks_chart_unit
                            if rec.ks_xlabels and rec.ks_ylabels:
                                ks_yaxis = json.loads(rec.ks_ylabels)

                                y_labels = []
                                for y_axis in ks_yaxis.keys():
                                    data_row = {'data':[],'label':ks_yaxis[y_axis]['measure']}

                                    if rec.ks_dashboard_item_type in ['ks_bar_chart', 'ks_horizontalBar_chart',
                                                                      'ks_line_chart']:
                                        chart_type = ks_yaxis[y_axis]['chart_type']
                                        if chart_type in ['bar', 'line']:
                                            data_row['type'] = chart_type
                                        if rec.ks_bar_chart_stacked:
                                            data_row['stack'] = ks_yaxis[y_axis]['group']
                                        if ks_yaxis[y_axis]['chart_type'] == 'line':
                                            y_labels.insert(0, y_axis)
                                            ks_chart_data['datasets'].insert(0, data_row)
                                        else:
                                            y_labels.append(y_axis)
                                            ks_chart_data['datasets'].append(data_row)
                                    else:
                                        y_labels.append(y_axis)
                                        ks_chart_data['datasets'].append(data_row)

                                for res in records.get('records'):
                                    ks_chart_data['labels'].append(res[rec.ks_xlabels])
                                    counter = 0
                                    for y_axis in y_labels:
                                        ks_chart_data['datasets'][counter]['data'].append(res[y_axis])
                                        counter += 1
                        rec.ks_chart_data = json.dumps(ks_chart_data)

                    else:
                        rec.ks_chart_data = False
            else:
                rec.ks_chart_data = False

    @api.depends('ks_custom_query', 'ks_data_calculation_type')
    def ks_get_list_view_data(self):
        for rec in self:
            if rec.ks_list_view_type and rec.ks_dashboard_item_type and rec.ks_dashboard_item_type == 'ks_list_view':
                ks_list_view_data = {'label': [], 'data_rows': [], 'date_index': [], 'type':'query'}
                if rec.ks_data_calculation_type != 'query':
                    return super(KsDashboardNinjaItemAdvance, self).ks_get_list_view_data()
                elif rec.ks_data_calculation_type == 'query' and rec.ks_query_result:

                    query_result = json.loads(rec.ks_query_result)
                    if query_result:
                        ks_list_fields = query_result.get('header')

                        for field in ks_list_fields:
                            field = field.replace("_", " ")
                            ks_list_view_data['label'].append(field.title())
                        for res in query_result.get('records'):
                            data_row = {'data': []}
                            for field in ks_list_fields:
                                data_row['data'].append(res[field])
                            ks_list_view_data['data_rows'].append(data_row)

                        rec.ks_list_view_data = json.dumps(ks_list_view_data)
                    else:
                        rec.ks_list_view_data = json.dumps(ks_list_view_data)
                else:
                    rec.ks_list_view_data = False
            else:
                rec.ks_list_view_data = False

    @api.depends('ks_custom_query','ks_data_calculation_type')
    def ks_run_query(self):
        for rec in self:
            with api.Environment.manage():
                if rec.ks_data_calculation_type == 'query' and rec.ks_dashboard_item_type not in ['ks_tile','ks_kpi']\
                        and rec.ks_custom_query:
                    ks_query = rec.ks_custom_query
                    try:
                        conn = sql_db.db_connect(self.env.cr.dbname)
                        new_env = api.Environment(conn.cursor(), self.env.uid,
                                                  self.env.context)
                        new_env.cr.execute(ks_query)
                        header = [col.name for col in new_env.cr.description]

                        records = new_env.cr.dictfetchall()

                    except ProgrammingError as e:
                        if e.args[0] == 'no results to fetch':
                            raise ValidationError(_("You can only read the Data from Database"))
                        else:
                            raise ValidationError(_(e))
                    except Exception as e:
                        raise ValidationError(_(e))
                    finally:
                        new_env.cr.close()

                    for res in records:
                        for key in res:
                            if type(res[key]).__name__ == 'datetime':
                                res[key] = res[key].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            elif type(res[key]).__name__ == 'date':
                                res[key] = res[key].strftime(DEFAULT_SERVER_DATE_FORMAT)
                    rec.ks_query_result = json.dumps({'header': header,
                                                      'records': records})
                else:
                    rec.ks_query_result = False

    @api.onchange('ks_custom_query')
    def ks_empty_labels(self):
        for rec in self:
            rec.ks_xlabels = False
            rec.ks_ylabels = False