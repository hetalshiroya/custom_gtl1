# _*_ coding: utf-8
from odoo import models, fields, api, _

from datetime import datetime
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object

DATE_DICT = {
    '%m/%d/%Y' : 'mm/dd/yyyy',
    '%Y/%m/%d' : 'yyyy/mm/dd',
    '%m/%d/%y' : 'mm/dd/yy',
    '%d/%m/%Y' : 'dd/mm/yyyy',
    '%d/%m/%y' : 'dd/mm/yy',
    '%d-%m-%Y' : 'dd-mm-yyyy',
    '%d-%m-%y' : 'dd-mm-yy',
    '%m-%d-%Y' : 'mm-dd-yyyy',
    '%m-%d-%y' : 'mm-dd-yy',
    '%Y-%m-%d' : 'yyyy-mm-dd',
    '%f/%e/%Y' : 'm/d/yyyy',
    '%f/%e/%y' : 'm/d/yy',
    '%e/%f/%Y' : 'd/m/yyyy',
    '%e/%f/%y' : 'd/m/yy',
    '%f-%e-%Y' : 'm-d-yyyy',
    '%f-%e-%y' : 'm-d-yy',
    '%e-%f-%Y' : 'd-m-yyyy',
    '%e-%f-%y' : 'd-m-yy'
}

class InsAnalyticReportXlsx(models.AbstractModel):
    _name = 'report.dynamic_xlsx.ins_analytic_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            #'border': True
        })
        self.content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'border': True,
            'text_wrap': True,
        })
        self.content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        self.line_header_left = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        self.line_header_right = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'bottom': True,
        })
        self.line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            #'top': True,
            #'bottom': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })
        self.line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            #'top': True,
            #'bottom': True,
            'font': 'Arial',
            'align': 'center',
        })
        self.line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'bottom': True,
            'text_wrap': True,
            'valign': 'top'
        })
        self.line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
            'text_wrap': True,
            'valign': 'top'
        })

    def prepare_report_filters(self, filter):
        """It is writing under second page"""
        self.row_pos_2 += 2
        if filter:
            # Date from
            self.sheet_2.write_string(self.row_pos_2, 0, _('Date from'),
                                    self.format_header)
            self.sheet_2.write_datetime(self.row_pos_2, 1, self.convert_to_date(str(filter['date_from']) or ''),
                                    self.content_header_date)
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Date to'),
                                    self.format_header)
            self.sheet_2.write_datetime(self.row_pos_2, 1, self.convert_to_date(str(filter['date_to']) or ''),
                                    self.content_header_date)
            self.row_pos_2 += 1

            # Partners
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Partners'),
                                                 self.format_header)
            p_list = ', '.join([lt or '' for lt in filter.get('partners')])
            self.sheet_2.write_string(self.row_pos_2, 1, p_list,
                                      self.content_header)

            # Analytic Accounts
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Analytic Accounts'),
                                      self.format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('analytics')])
            self.sheet_2.write_string(self.row_pos_2, 1, a_list,
                                      self.content_header)

            # Analytic Tags
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Analytic Tags'),
                                      self.format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('analytic_tags')])
            self.sheet_2.write_string(self.row_pos_2, 1, a_list,
                                      self.content_header)

    def prepare_report_contents(self, data, acc_lines, filter, final_balance):
        data = data[0]
        self.row_pos += 3

        self.sheet.merge_range(self.row_pos, 0, self.row_pos, 5, _('Analytic Name'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 6, _('Reference'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 7, _('Partner'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 8, _('Sales'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 9, _('Cost'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 10, _('Profit'),
                                self.format_header)

        if acc_lines:
            for line in acc_lines:
                self.row_pos += 1
                self.sheet.merge_range(self.row_pos, 0, self.row_pos, 5, '            ' + acc_lines[line].get('name'), self.line_header_left)
                self.sheet.write_string(self.row_pos, 6, acc_lines[line].get('reference', '') or '', self.line_header)
                self.sheet.write_string(self.row_pos, 7, acc_lines[line].get('partner', '') or '', self.line_header)
                self.sheet.write_number(self.row_pos, 8, float(acc_lines[line].get('credit', 0.0)) or 0.0,
                                        self.line_header)
                self.sheet.write_number(self.row_pos, 9, float(acc_lines[line].get('debit', 0.0)) or 0.0,
                                        self.line_header)
                self.sheet.write_number(self.row_pos, 10, float(acc_lines[line].get('balance', 0.0)) or 0.0, self.line_header)
            self.row_pos += 1
            self.sheet.merge_range(self.row_pos, 0, self.row_pos, 9, _('Total'),
                                   self.line_header_right)
            self.sheet.write_number(self.row_pos, 10, final_balance or 0.0, self.line_header)

    def _format_float_and_dates(self, currency_id, lang_id):

        self.line_header.num_format = currency_id.excel_format
        self.line_header_light.num_format = currency_id.excel_format
        self.line_header_light_initial.num_format = currency_id.excel_format
        self.line_header_light_ending.num_format = currency_id.excel_format


        self.line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        self.content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

    def convert_to_date(self, datestring=False):
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(self.language_id.date_format)
            return datetime.strptime(datestring, self.language_id.date_format)
        else:
            return False

    def generate_xlsx_report(self, workbook, data, record):

        self._define_formats(workbook)
        self.row_pos = 0
        self.row_pos_2 = 0

        self.record = record # Wizard object

        self.sheet = workbook.add_worksheet('Analytic Report')
        self.sheet_2 = workbook.add_worksheet('Filters')
        self.sheet.set_column(0, 0, 15)
        self.sheet.set_column(6, 6, 18)
        self.sheet.set_column(7, 7, 18)
        self.sheet.set_column(8, 8, 12)

        self.sheet_2.set_column(0, 0, 35)
        self.sheet_2.set_column(1, 1, 25)
        self.sheet_2.set_column(2, 2, 25)
        self.sheet_2.set_column(3, 3, 25)
        self.sheet_2.set_column(4, 4, 25)
        self.sheet_2.set_column(5, 5, 25)
        self.sheet_2.set_column(6, 6, 25)

        self.sheet.freeze_panes(4, 0)

        self.sheet.screen_gridlines = False
        self.sheet_2.screen_gridlines = False
        self.sheet_2.protect()

        # For Formating purpose
        lang = self.env.user.lang
        self.language_id = self.env['res.lang'].search([('code','=',lang)])[0]
        self._format_float_and_dates(self.env.user.company_id.currency_id, self.language_id)

        if record:
            data = record.read()
            self.sheet.set_zoom(100)
            self.sheet.merge_range(0, 0, 0, 8, 'Analytic Report'+' - '+data[0]['company_id'][1], self.format_title)
            self.dateformat = self.env.user.lang
            filters, account_lines, final_balance = record.get_report_datas()
            # Filter section
            self.prepare_report_filters(filters)
            # Content section
            self.prepare_report_contents(data, account_lines, filters, final_balance)
