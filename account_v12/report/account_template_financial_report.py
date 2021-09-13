# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime

from odoo import fields, models, api, _


class AccountBalanceInherit(models.AbstractModel):
    _name = "report.account_v12.financial_report_balance_full_temp"
    _description = "Account Balance Inherit"

    def _compute_account_balance(self, accounts):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) \
               as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
            'ytd_bal': "0 as ytd_bal",
        }
        res = {}
        move_line_obj = self.env['account.move.line']
        for account in accounts:
            res[account.id] = dict((fn, 0.0) for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = move_line_obj._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + \
                      ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row

        if accounts:
            for account in accounts:
                ytd_credit = ytd_debit = 0.0
                domain = [('account_id', '=', account.id)]
                current_date = datetime.today()
                year_first_date = current_date.replace(day=1, month=1)
                if current_date and year_first_date:
                    domain += [('date', '>=', year_first_date.date()), ('date', '<=', current_date.date())]
                account_mv_ids = self.env['account.move.line'].search(domain)
                for account_mv_rec in account_mv_ids:
                    ytd_credit += account_mv_rec.credit or 0.0
                    ytd_debit += account_mv_rec.debit or 0.0
                res[account.id]['ytd_bal'] = ytd_debit - ytd_credit
        return res

    def _compute_report_balance(self, reports):
        res = {}
        fields = ['credit', 'debit', 'balance', 'ytd_bal']
        account_obj = self.env['account.account']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                #  it's the sum of the linked accounts
                res[report.id]['account'] = \
                    self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                #  it's the sum the leaf accounts with such an account type
                accounts = account_obj.search([('user_type_id', 'in',
                                                report.account_type_ids.ids)])
                res[report.id]['account'] = \
                    self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                #  it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                #  it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        domain = [('id', '=', data['account_report_id'][0])]
        account_report = self.env['account.financial.report'].search(domain)
        child_reports = account_report._get_children_by_order()

        res = self.with_context(data.get('used_context')
                                )._compute_report_balance(child_reports)

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * report.sign,
                'type': 'report',
                'level': bool(report.style_overwrite) and
                         report.style_overwrite or report.level,
                'account_type': report.type or False,
                'ytd': res[report.id].get('ytd_bal', 0) * report.sign or 0
            }
            if data['columns'] in ('two', 'five', 'four'):
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']
                vals['ytd'] = res[report.id]['ytd_bal']
            lines.append(vals)

            if report.display_detail == 'no_detail':
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * report.sign or 0.0,
                        'type': 'account',
                        'level': report.display_detail == \
                                 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                        'ytd': value.get('ytd_bal', 0) * report.sign or 0
                    }
                    if data['columns'] in ('two', 'four', 'five'):
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not \
                                account.company_id.currency_id.is_zero(
                                    vals['credit']):
                            flag = True

                    if data['columns'] == 'five' and not account.company_id.currency_id.is_zero(value['ytd_bal']):
                        flag = True

                    if data['columns'] in ('one', 'four', 'five'):
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True

                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda \
                        sub_line: sub_line['name'])
        return lines

    @api.multi
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        return {'doc_ids': self.ids,
                'doc_model': self.model,
                'data': data,
                'docs': docs,
                'time': time,
                'get_account_lines': self.get_account_lines(data.get('form')),
                }


class AccountBalanceInheritQtr(models.AbstractModel):
    _name = "report.account_v12.account_full_qtr_balance_cols"
    _description = "Account Balance Inherit Qtr"

    def get_account_lines_qtr(self, data):
        lines = []
        res = {}
        lines = []
        domain = [('id', '=', data['account_report_id'][0])]
        account_report = self.env['account.financial.report'].search(domain)
        acc_bal_obj = self.env['report.scs_account_report.financial_report_balance_full_temp']
        child_reports = account_report._get_children_by_order()
        if data['qtr_dates'] and data['quat_num']:
            for qtr in range(int(data['quat_num'])):
                res1 = {}
                data['used_context']['date_from'] = data['qtr_dates'] \
                    ['qtr' + str(qtr + 1)] \
                    ['date_from']
                data['used_context']['date_to'] = data['qtr_dates'] \
                    ['qtr' + str(qtr + 1)] \
                    ['date_to']
                res1 = acc_bal_obj.with_context(data.get('used_context')
                                                )._compute_report_balance(child_reports)
                res.update({'qtn' + str(qtr + 1): res1})

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance1': res['qtn1'][report.id]['balance'] * report.sign \
                            or 0.0,
                'balance2': 0.0,
                'balance3': 0.0,
                'balance4': 0.0,
                'type': 'report',
                'level': bool(report.style_overwrite) and \
                         report.style_overwrite or report.level,
                'ytd': res['qtn1'][report.id].get('ytd_bal', 0) * report.sign or 0,
                'account_type': report.type or False,  # used to underline the financial report balances
            }
            if int(data['quat_num']) in (2, 3, 4):
                vals.update({
                    'balance2': res['qtn2'][report.id]
                                ['balance'] * report.sign or 0.0,
                })
            if int(data['quat_num']) in (3, 4):
                vals.update({
                    'balance3': res['qtn3'][report.id]
                                ['balance'] * report.sign or 0.0,
                })
            if int(data['quat_num']) == 4:
                vals.update({
                    'balance4': res['qtn4'][report.id]
                                ['balance'] * report.sign or 0.0,
                })
            lines.append(vals)

            if report.display_detail == 'no_detail':
                continue

            #             if res['qtn1'][report.id].get('account'):
            #                 for account_id, value in res['qtn1'][report.id]['account'].items():
            #                     flag = False
            #                     account = self.env['account.account'].browse(account_id)
            #                     vals = {
            #                         'name': account.code + ' ' + account.name,
            #                         'balance1': value['balance'] * report.sign or 0.0,
            #                         'balance2':0.0,
            #                         'balance3':0.0,
            #                         'balance4':0.0,
            #                         'type': 'account',
            #                         'level': report.display_detail == 'detail_with_hierarchy' and 4,
            #                         'ytd': value['ytd_bal'] * report.sign or 0.0,
            #                         'account_type': account.internal_type,
            #                     }
            #                     if int(data['quat_num']) in (2, 3, 4) :
            #                         if account_id in res['qtn2'][report.id]['account']:
            #                             vals.update({
            #                                 'balance2': res['qtn2'][report.id]['account']
            #                                             [account_id]['balance'] * \
            #                                             report.sign or 0.0,
            #                             })
            #                     if int(data['quat_num']) in (3, 4):
            #                         if account_id in res['qtn3'][report.id]['account']:
            #                             vals.update({
            #                                 'balance3': res['qtn3'][report.id]['account']
            #                                             [account_id]['balance'] * \
            #                                             report.sign or 0.0,
            #                             })
            #                     if int(data['quat_num']) == 4:
            #                         if account_id in res['qtn4'][report.id]['account']:
            #                             vals.update({
            #                                 'balance4': res['qtn4'][report.id]['account']
            #                                             [account_id]['balance'] * \
            #                                             report.sign or 0.0,
            #                             })
            #                     if not account.company_id.currency_id.is_zero(vals['balance1']) or \
            #                             not account.company_id.currency_id.is_zero(vals['balance2']) or \
            #                             not account.company_id.currency_id.is_zero(vals['balance3']) or \
            #                             not account.company_id.currency_id.is_zero(vals['balance4']) or \
            #                             not account.company_id.currency_id.is_zero(vals['ytd']):
            #                         flag = True
            #                     if flag:
            #                         lines.append(vals)

            if res['qtn1'][report.id].get('account'):
                for account_id, value in res['qtn1'][report.id]['account'].items():
                    account = self.env['account.account'].browse(account_id)

                    qtn1_flag = False
                    for qtn1_rec in lines:
                        if qtn1_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn1_rec['balance1'] = value['balance'] * report.sign or 0.0
                            qtn1_flag = True
                            break

                    if not qtn1_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance1': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'ytd': value['ytd_bal'] * report.sign or 0.0,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if int(data['quat_num']) in (2, 3, 4) and 'qtn2' in res and res['qtn2'][report.id].get('account'):
                for account_id, value in res['qtn2'][report.id]['account'].items():
                    account = self.env['account.account'].browse(account_id)
                    qtn2_flag = False
                    for qtn2_rec in lines:
                        if qtn2_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn2_rec['balance2'] = value['balance'] * report.sign or 0.0
                            qtn2_flag = True
                            break

                    if not qtn2_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance2': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'ytd': value['ytd_bal'] * report.sign or 0.0,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if int(data['quat_num']) in (3, 4) and 'qtn3' in res and res['qtn3'][report.id].get('account'):
                for account_id, value in res['qtn3'][report.id]['account'].items():
                    account = self.env['account.account'].browse(account_id)

                    qtn3_flag = False
                    for qtn3_rec in lines:
                        if qtn3_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn3_rec['balance3'] = value['balance'] * report.sign or 0.0
                            qtn3_flag = True
                            break

                    if not qtn3_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance3': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'ytd': value['ytd_bal'] * report.sign or 0.0,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if int(data['quat_num']) == 4 and 'qtn4' in res and res['qtn4'][report.id].get('account'):
                for account_id, value in res['qtn4'][report.id]['account'].items():
                    account = self.env['account.account'].browse(account_id)

                    qtn4_flag = False
                    for qtn4_rec in lines:
                        if qtn4_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn4_rec['balance4'] = value['balance'] * report.sign or 0.0
                            qtn4_flag = True
                            break

                    if not qtn4_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance4': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'ytd': value['ytd_bal'] * report.sign or 0.0,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)
        return lines

    @api.multi
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        return {'doc_ids': self.ids,
                'doc_model': self.model,
                'data': data,
                'docs': docs,
                'time': time,
                'get_account_lines_qtr': self.get_account_lines_qtr(data.get('form')),
                }


class AccountBalanceInheritTwlv(models.AbstractModel):
    _name = "report.account_v12.account_full_13_balance_cols"
    _description = "Account Balance Inherit Twlv"

    def get_account_lines_twelve_month(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([
            ('id', '=', data['account_report_id'][0])
        ])
        acc_bal_obj = self.env['report.scs_account_report.financial_report_balance_full_temp']
        child_reports = account_report._get_children_by_order()
        res = {}

        if data['qtr_dates'] and data['quat_num']:
            for qtr in range(int(data['quat_num'])):
                res1 = {}
                data['used_context'
                ]['date_from'] = data['qtr_dates'
                ]['qtr' + str(qtr + 1)]['date_from'
                ]
                data['used_context'
                ]['date_to'] = data['qtr_dates']['qtr' + str(qtr + 1)
                                                 ]['date_to']
                res1 = acc_bal_obj.with_context(data.get('used_context')
                                                )._compute_report_balance(child_reports)
                res.update({'qtn' + str(qtr + 1): res1})

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance1': res['qtn1'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance2': res['qtn2'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance3': res['qtn3'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance4': res['qtn4'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance5': res['qtn5'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance6': res['qtn6'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance7': res['qtn7'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance8': res['qtn8'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance9': res['qtn9'][report.id]['balance'] * \
                            report.sign or 0.0,
                'balance10': res['qtn10'][report.id]['balance'] * \
                             report.sign or 0.0,
                'balance11': res['qtn11'][report.id]['balance'] * \
                             report.sign or 0.0,
                'balance12': res['qtn12'][report.id]['balance'] * \
                             report.sign or 0.0,
                'ytd': res['qtn1'][report.id].get('ytd_bal', 0) * report.sign or 0,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite \
                         or report.level,
                'account_type': report.type or False,  # used to underline the financial report balances
            }

            lines.append(vals)
            if report.display_detail == 'no_detail':
                continue

            if res['qtn1'][report.id].get('account'):
                for account_id, value in res['qtn1'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id)

                    qtn1_flag = False
                    for x_rec in lines:
                        if x_rec.get('name') == str(account.code + ' ' + account.name):
                            x_rec['balance1'] = value['balance'] * report.sign or 0.0
                            qtn1_flag = True
                            break

                    if not qtn1_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance1': value['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn2'][report.id].get('account'):
                for account_id2, value2 in res['qtn2'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id2)

                    qtn2_flag = False
                    for qtn2_rec in lines:
                        if qtn2_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn2_rec['balance2'] = value2['balance'] * report.sign or 0.0
                            qtn2_flag = True
                            break

                    if not qtn2_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance2': value2['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value2['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn3'][report.id].get('account'):
                for account_id3, value3 in res['qtn3'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id3)

                    qtn3_flag = False
                    for qtn3_rec in lines:
                        if qtn3_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn3_rec['balance3'] = value3['balance'] * report.sign or 0.0
                            qtn3_flag = True
                            break

                    if not qtn3_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance3': value3['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value3['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn4'][report.id].get('account'):
                for account_id4, value4 in res['qtn4'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id4)

                    qtn4_flag = False
                    for qtn4_rec in lines:
                        if str(qtn4_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn4_rec['balance4'] = value4['balance'] * report.sign or 0.0
                            qtn4_flag = True
                            break

                    if not qtn4_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance4': value4['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value4['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn5'][report.id].get('account'):
                for account_id5, value5 in res['qtn5'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id5)

                    qtn5_flag = False
                    for qtn5_rec in lines:
                        if qtn5_rec.get('name') == str(account.code + ' ' + account.name):
                            qtn5_rec['balance5'] = value5['balance'] * report.sign or 0.0
                            qtn5_flag = True
                            break

                    if not qtn5_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance5': value5['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value5['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn6'][report.id].get('account'):
                for account_id6, value6 in res['qtn6'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id6)

                    qtn6_flag = False
                    for qtn6_rec in lines:
                        if str(qtn6_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn6_rec['balance6'] = value6['balance'] * report.sign or 0.0
                            qtn6_flag = True
                            break

                    if not qtn6_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance6': value6['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value6['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn7'][report.id].get('account'):
                for account_id7, value7 in res['qtn7'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id7)

                    qtn7_flag = False
                    for qtn7_rec in lines:
                        if str(qtn7_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn7_rec['balance7'] = value7['balance'] * report.sign or 0.0
                            qtn7_flag = True
                            break

                    if not qtn7_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance7': value7['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value7['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn8'][report.id].get('account'):
                for account_id8, value8 in res['qtn8'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id8)

                    qtn8_flag = False
                    for qtn8_rec in lines:
                        if str(qtn8_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn8_rec['balance8'] = value8['balance'] * report.sign or 0.0
                            qtn8_flag = True
                            break

                    if not qtn8_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance8': value8['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value8['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn9'][report.id].get('account'):
                for account_id9, value9 in res['qtn9'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id9)

                    qtn9_flag = False
                    for qtn9_rec in lines:
                        if str(qtn9_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn9_rec['balance9'] = value9['balance'] * report.sign or 0.0
                            qtn9_flag = True
                            break

                    if not qtn9_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance9': value9['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value9['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn10'][report.id].get('account'):
                for account_id10, value10 in res['qtn10'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id10)

                    qtn10_flag = False
                    for qtn10_rec in lines:
                        if str(qtn10_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn10_rec['balance10'] = value10['balance'] * report.sign or 0.0
                            qtn10_flag = True
                            break

                    if not qtn10_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance10': value10['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value10['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn11'][report.id].get('account'):
                for account_id11, value11 in res['qtn11'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id11)

                    qtn11_flag = False
                    for qtn11_rec in lines:
                        if str(qtn11_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn11_rec['balance11'] = value11['balance'] * report.sign or 0.0
                            qtn11_flag = True
                            break

                    if not qtn11_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance11': value11['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value11['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)

            if res['qtn12'][report.id].get('account'):
                for account_id12, value12 in res['qtn12'][report.id]['account'].items():
                    flag = False
                    account = self.env['account.account'].browse(account_id12)

                    qtn12_flag = False
                    for qtn12_rec in lines:
                        if str(qtn12_rec.get('name')) == str(account.code + ' ' + account.name):
                            qtn12_rec['balance12'] = value12['balance'] * report.sign or 0.0
                            qtn12_flag = True
                            break

                    if not qtn12_flag:
                        vals = {
                            'name': account.code + ' ' + account.name,
                            'balance12': value12['balance'] * report.sign or 0.0,
                            'type': 'account',
                            'ytd': value12['ytd_bal'] * report.sign or 0.0,
                            'level': report.display_detail == 'detail_with_hierarchy' and 4,
                            'account_type': account.internal_type,
                        }
                        lines.append(vals)
        return lines

    @api.multi
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        return {'doc_ids': self.ids,
                'doc_model': self.model,
                'data': data,
                'docs': docs,
                'time': time,
                'get_account_lines_twelve_month': \
                    self.get_account_lines_twelve_month(data.get('form')),
                }
