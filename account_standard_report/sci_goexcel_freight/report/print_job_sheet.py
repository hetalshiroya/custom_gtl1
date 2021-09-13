# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
import dateutil.relativedelta
from datetime import timedelta, date
import calendar
import math
import logging

_logger = logging.getLogger(__name__)
from odoo.tools.misc import formatLang


class PrintJobSheet(models.AbstractModel):
    _name = 'report.sci_goexcel_freight.report_job_sheet_details'
    _description = "Print Job Sheet"

    """
    Abstract Model specially for report template.
    _name = Use prefix `report.` along with `module_name.report_name`
    """

    @api.model
    def _get_report_values(self, docids, data=None):
        #print('_get_report_values docids=' + str(docids))
        #docs = self.env['freight.booking'].browse(docids)
        docs = self.env['freight.booking'].browse(data['form'])
        print('_get_report_values docs=' + str(docs))
        for doc in docs:
            print('_get_report_values doc=' + str(doc))


        return{
            'doc_ids': docs.ids,
            'doc_model': 'freight.booking',
            'docs': docs,
        }
