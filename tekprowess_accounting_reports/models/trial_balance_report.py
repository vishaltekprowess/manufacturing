# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TrialBalanceReport(models.TransientModel):
    _name = 'tekprowess.trial.balance.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Trial Balance'

    def _get_report_name(self):
        return "Trial Balance"

    def _get_lines(self, options):
        lines = []
        
        accounts = self.env['account.account'].search([
            ('company_ids', 'in', [self.env.company.id])
        ], order='code')
        
        total_initial_debit = 0.0
        total_initial_credit = 0.0
        total_period_debit = 0.0
        total_period_credit = 0.0
        total_end_debit = 0.0
        total_end_credit = 0.0
        
        for account in accounts:
            # Initial Balance
            initial_balance = self._compute_initial_balance(
                account, options.get('date_from')
            )
            initial_debit = initial_balance if initial_balance > 0 else 0.0
            initial_credit = -initial_balance if initial_balance < 0 else 0.0
            
            # Period Movement
            period_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            period_debit = period_data['debit']
            period_credit = period_data['credit']
            
            # End Balance
            end_balance = initial_balance + period_data['balance']
            end_debit = end_balance if end_balance > 0 else 0.0
            end_credit = -end_balance if end_balance < 0 else 0.0
            
            # Skip accounts with no activity
            if all(v == 0 for v in [initial_debit, initial_credit, 
                                     period_debit, period_credit,
                                     end_debit, end_credit]):
                if not options.get('unfold_all'):
                    continue
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 1,
                'columns': [
                    {'name': self._format_value(initial_debit), 'no_format': initial_debit},
                    {'name': self._format_value(initial_credit), 'no_format': initial_credit},
                    {'name': self._format_value(period_debit), 'no_format': period_debit},
                    {'name': self._format_value(period_credit), 'no_format': period_credit},
                    {'name': self._format_value(end_debit), 'no_format': end_debit},
                    {'name': self._format_value(end_credit), 'no_format': end_credit},
                ],
                'caret_options': 'account',
            })
            
            # Accumulate totals
            total_initial_debit += initial_debit
            total_initial_credit += initial_credit
            total_period_debit += period_debit
            total_period_credit += period_credit
            total_end_debit += end_debit
            total_end_credit += end_credit
        
        # Total line
        lines.append({
            'name': _('Total'),
            'class': 'total o_account_reports_domain_total',
            'level': 0,
            'columns': [
                {'name': self._format_value(total_initial_debit), 'no_format': total_initial_debit},
                {'name': self._format_value(total_initial_credit), 'no_format': total_initial_credit},
                {'name': self._format_value(total_period_debit), 'no_format': total_period_debit},
                {'name': self._format_value(total_period_credit), 'no_format': total_period_credit},
                {'name': self._format_value(total_end_debit), 'no_format': total_end_debit},
                {'name': self._format_value(total_end_credit), 'no_format': total_end_credit},
            ],
        })
        
        return lines

    def _get_columns(self, options):
        """Define columns for trial balance"""
        return [
            {'name': _('Account'), 'class': 'text-left'},
            {'name': _('Initial Debit'), 'class': 'number'},
            {'name': _('Initial Credit'), 'class': 'number'},
            {'name': _('Period Debit'), 'class': 'number'},
            {'name': _('Period Credit'), 'class': 'number'},
            {'name': _('End Debit'), 'class': 'number'},
            {'name': _('End Credit'), 'class': 'number'},
        ]
