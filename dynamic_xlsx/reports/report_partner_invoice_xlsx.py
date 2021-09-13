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

class InsPartnerInvoiceXlsx(models.AbstractModel):
    _name = 'report.dynamic_xlsx.ins_partner_invoice_xlsx'
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
            'align': 'center',
            'font': 'Arial',
            #'border': True
        })
        self.content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'border': True,
            'font': 'Arial',
        })
        self.content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'border': True,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'bottom': True,
            'font': 'Arial',
            'bg_color': '#FFC7CE'
        })
        self.line_header_date = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'bottom': True,
            'font': 'Arial',
            'bg_color': '#FFC7CE'
        })
        self.line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'text_wrap': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        self.line_header_light_initial = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'bottom': True,
            'font': 'Arial',
            'valign': 'top'
        })
        self.line_header_light_ending = workbook.add_format({
            'italic': True,
            'font_size': 10,
            'align': 'center',
            'top': True,
            'font': 'Arial',
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
            self.sheet_2.write_string(self.row_pos_2, 0, _('Reconciled'),
                                    self.format_header)
            self.sheet_2.write_string(self.row_pos_2, 1, filter['reconciled'],
                                    self.content_header)

            # Journals
            self.row_pos_2 += 2
            self.sheet_2.write_string(self.row_pos_2, 0, _('Journals'),
                                    self.format_header)
            j_list = ', '.join([lt or '' for lt in filter.get('journals')])
            self.sheet_2.write_string(self.row_pos_2, 1, j_list,
                                      self.content_header)

            # Partners
            self.row_pos_2 += 1
            self.sheet_2.write_string(self.row_pos_2, 0, _('Partners'),
                                                 self.format_header)
            p_list = ', '.join([lt or '' for lt in filter.get('partners')])
            self.sheet_2.write_string(self.row_pos_2, 1, p_list,
                                      self.content_header)


    def prepare_report_contents(self, data, acc_lines, filter):
        data = data[0]
        self.row_pos += 3

        self.sheet.write_string(self.row_pos, 0, _('Date'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 1, _('Number'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 2, _('Partner'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 3, _('Journal'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 4, _('Journal Entry'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 5, _('Reconciled?'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 6, _('Amount'),
                                self.format_header)
        self.sheet.write_string(self.row_pos, 7, _('Unreconciled Amount'),
                                self.format_header)

        if acc_lines:
            for line in acc_lines:
                self.row_pos += 1
                self.sheet.write_datetime(self.row_pos, 0, self.convert_to_date(line.get('date_invoice')), self.line_header_date)
                self.sheet.write_string(self.row_pos, 1, line.get('lname'), self.line_header)
                self.sheet.write_string(self.row_pos, 2, line.get('partner_name', ''), self.line_header)
                self.sheet.write_string(self.row_pos, 3, line.get('journal_code', ''), self.line_header)
                self.sheet.write_string(self.row_pos, 4, line.get('journal_entry', ''), self.line_header)
                self.sheet.write_string(self.row_pos, 5, 'Yes' if line.get('reco_state') else 'No', self.line_header)
                self.sheet.write_number(self.row_pos, 6, line.get('amount_currency'), self.line_header)
                self.sheet.write_number(self.row_pos, 7, line.get('amount_unreconciled'), self.line_header)


                sub_lines = self.record.build_detailed_move_lines(invoice=line.get('invid'), fetch_range=1000000)
                self.row_pos += 1
                self.sheet.write_string(self.row_pos, 1, _('Date'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 2, _('Reference'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 3, _('Description'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 4, _('Analytic Account'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 5, _('Analytic Tags'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 6, _('Doc Amount'),
                                        self.format_header)
                self.sheet.write_string(self.row_pos, 7, _('Knock-off Amount'),
                                        self.format_header)
                for sub_line in sub_lines:
                    self.row_pos += 1
                    self.sheet.write_datetime(self.row_pos, 1, self.convert_to_date(sub_line.get('date')),
                                            self.line_header_light_date)
                    self.sheet.write_string(self.row_pos, 2, sub_line.get('ref'),
                                            self.line_header_light)
                    self.sheet.write_string(self.row_pos, 3, sub_line.get('description') or '',
                                            self.line_header_light)
                    self.sheet.write_string(self.row_pos, 4, sub_line.get('analytic_account_string') or '',
                                            self.line_header_light)
                    self.sheet.write_string(self.row_pos, 5, sub_line.get('analytic_tag_ids') or '',
                                            self.line_header_light)
                    # self.sheet.write_string(self.row_pos, 3, sub_line.get('lref') or '',
                    #                         self.line_header_light)
                    self.sheet.write_number(self.row_pos, 6, sub_line.get('doc_amount','0'),
                                            self.line_header_light)
                    self.sheet.write_number(self.row_pos, 7, sub_line.get('knock_off_amount','0') or 0,
                                            self.line_header_light)

    def _format_float_and_dates(self, currency_id, lang_id):

        self.line_header.num_format = currency_id.excel_format
        self.line_header_light.num_format = currency_id.excel_format
        self.line_header_light_initial.num_format = currency_id.excel_format
        self.line_header_light_ending.num_format = currency_id.excel_format


        self.line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        self.content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        self.line_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

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

        self.sheet = workbook.add_worksheet('Partner Invoices')
        self.sheet_2 = workbook.add_worksheet('Filters')
        self.sheet.set_column(0, 0, 12)
        self.sheet.set_column(1, 1, 18)
        self.sheet.set_column(2, 2, 30)
        self.sheet.set_column(3, 3, 18)
        self.sheet.set_column(4, 4, 30)
        self.sheet.set_column(5, 5, 18)
        self.sheet.set_column(6, 6, 12)
        self.sheet.set_column(7, 7, 15)
        self.sheet.set_column(8, 8, 10)
        self.sheet.set_column(9, 9, 10)

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
            self.sheet.set_zoom(86)
            self.sheet.merge_range(0, 0, 0, 8, 'Partner Invoices'+' - '+data[0]['company_id'][1], self.format_title)
            self.dateformat = self.env.user.lang
            filters, account_lines = record.get_report_datas()
            # Filter section
            self.prepare_report_filters(filters)
            # Content section
            self.prepare_report_contents(data, account_lines, filters)
