# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GeneralLedgerReport(models.TransientModel):
    _name = 'tekprowess.general.ledger.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'General Ledger'

    def _get_report_name(self):
        return "General Ledger"

    def _get_lines(self, options):
        lines = []
        
        accounts = self.env['account.account'].search([
            ('company_ids', 'in', [self.env.company.id])
        ], order='code')
        
        for account in accounts:
            # Initial balance
            initial_balance = self._compute_initial_balance(
                account, options.get('date_from')
            )
            
            # Get move lines
            move_lines = self._get_account_move_lines(
                options, accounts=account
            ).sorted('date')
            
            # Skip accounts with no activity and no initial balance
            if not move_lines and initial_balance == 0:
                if not options.get('unfold_all'):
                    continue
            
            # Account header
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 0,
                'class': 'o_account_reports_level0',
                'unfoldable': True,
                'unfolded': options.get('unfold_all', False),
                'columns': [
                    {'name': ''},  # Date
                    {'name': ''},  # Journal
                    {'name': ''},  # Partner
                    {'name': ''},  # Label
                    {'name': ''},  # Debit
                    {'name': ''},  # Credit
                    {'name': self._format_value(initial_balance + sum(
                        ml.debit - ml.credit for ml in move_lines
                    ))},  # Balance
                ],
            })
            
            # Initial balance line
            if initial_balance != 0:
                lines.append({
                    'name': _('Initial Balance'),
                    'level': 1,
                    'class': 'o_account_reports_initial_balance',
                    'parent_id': f'account_{account.id}',
                    'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': _('Initial Balance')},
                        {'name': self._format_value(initial_balance if initial_balance > 0 else 0)},
                        {'name': self._format_value(-initial_balance if initial_balance < 0 else 0)},
                        {'name': self._format_value(initial_balance)},
                    ],
                })
            
            # Move lines
            running_balance = initial_balance
            for move_line in move_lines:
                running_balance += move_line.debit - move_line.credit
                
                lines.append({
                    'id': f'aml_{move_line.id}',
                    'name': move_line.name or move_line.move_id.name or '',
                    'level': 1,
                    'parent_id': f'account_{account.id}',
                    'caret_options': 'account.move.line',
                    'columns': [
                        {'name': move_line.date.strftime('%Y-%m-%d')},
                        {'name': move_line.journal_id.code or ''},
                        {'name': move_line.partner_id.name or ''},
                        {'name': move_line.name or move_line.move_id.name or ''},
                        {'name': self._format_value(move_line.debit)},
                        {'name': self._format_value(move_line.credit)},
                        {'name': self._format_value(running_balance)},
                    ],
                })
            
            # Account total line
            total_debit = sum(move_lines.mapped('debit'))
            total_credit = sum(move_lines.mapped('credit'))
            
            lines.append({
                'name': _('Total') + f" {account.code} {account.name}",
                'level': 1,
                'class': 'total',
                'parent_id': f'account_{account.id}',
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': self._format_value(total_debit)},
                    {'name': self._format_value(total_credit)},
                    {'name': self._format_value(running_balance)},
                ],
            })
        
        return lines

    def _get_columns(self, options):
        """Define columns for general ledger"""
        return [
            {'name': _('Account'), 'class': 'text-left'},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Journal'), 'class': 'text-center'},
            {'name': _('Partner'), 'class': 'text-left'},
            {'name': _('Label'), 'class': 'text-left'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'},
        ]
