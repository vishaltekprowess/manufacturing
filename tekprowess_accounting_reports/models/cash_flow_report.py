# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict


class CashFlowReport(models.TransientModel):
    _name = 'tekprowess.cash.flow.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Cash Flow Statement'

    def _get_report_name(self):
        return "Cash Flow Statement"

    def _get_lines(self, options):
        lines = []
        
        # Get cash accounts
        cash_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['asset_cash', 'liability_credit_card']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        if not cash_accounts:
            return [{
                'name': _('No cash accounts found'),
                'columns': [{'name': ''}],
            }]
        
        # Beginning Cash Balance
        beginning_balance = self._get_beginning_cash_balance(cash_accounts, options)
        lines.append({
            'name': _('Beginning Cash Balance'),
            'level': 0,
            'class': 'o_account_reports_level0',
            'columns': [{'name': self._format_value(beginning_balance)}],
        })
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # OPERATING ACTIVITIES
        # ==================
        lines.append(self._make_header(_('Cash Flow from Operating Activities')))
        
        operating_cash = self._add_operating_activities(lines, options)
        
        lines.append(self._make_total_line(
            _('Net Cash from Operating Activities'), operating_cash, level=1
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # INVESTING ACTIVITIES
        # ==================
        lines.append(self._make_header(_('Cash Flow from Investing Activities')))
        
        investing_cash = self._add_investing_activities(lines, options)
        
        lines.append(self._make_total_line(
            _('Net Cash from Investing Activities'), investing_cash, level=1
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # FINANCING ACTIVITIES
        # ==================
        lines.append(self._make_header(_('Cash Flow from Financing Activities')))
        
        financing_cash = self._add_financing_activities(lines, options)
        
        lines.append(self._make_total_line(
            _('Net Cash from Financing Activities'), financing_cash, level=1
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # NET CHANGE & ENDING BALANCE
        # ==================
        net_change = operating_cash + investing_cash + financing_cash
        lines.append(self._make_total_line(
            _('Net Change in Cash'), net_change, level=0, class_name='total'
        ))
        
        ending_balance = beginning_balance + net_change
        lines.append(self._make_total_line(
            _('Ending Cash Balance'), 
            ending_balance, 
            level=0, 
            class_name='total o_account_reports_domain_total'
        ))
        
        return lines

    def _get_beginning_cash_balance(self, cash_accounts, options):
        """Get cash balance at start of period"""
        total = 0.0
        for account in cash_accounts:
            balance = self._compute_initial_balance(
                account, options.get('date_from')
            )
            total += balance
        return total

    def _add_operating_activities(self, lines, options):
        """Add operating activities section"""
        total = 0.0
        
        # Net Income (from P&L)
        net_income = self._get_net_income(options)
        lines.append({
            'name': _('Net Income'),
            'level': 2,
            'columns': [{'name': self._format_value(net_income)}],
        })
        total += net_income
        
        # Adjustments for non-cash items
        lines.append({
            'name': _('Adjustments for Non-Cash Items:'),
            'level': 2,
            'columns': [{'name': ''}],
        })
        
        # Depreciation
        depreciation_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense_depreciation'),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        depreciation_total = 0.0
        for account in depreciation_accounts:
            balance_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            depreciation_total += balance_data['balance']
        
        if depreciation_total != 0:
            lines.append({
                'name': _('  Depreciation and Amortization'),
                'level': 3,
                'columns': [{'name': self._format_value(depreciation_total)}],
            })
            total += depreciation_total
        
        # Changes in Working Capital
        lines.append({
            'name': _('Changes in Working Capital:'),
            'level': 2,
            'columns': [{'name': ''}],
        })
        
        # Accounts Receivable
        receivable_change = self._get_working_capital_change(
            ['asset_receivable'], options
        )
        if receivable_change != 0:
            lines.append({
                'name': _('  Accounts Receivable'),
                'level': 3,
                'columns': [{'name': self._format_value(-receivable_change)}],
            })
            total -= receivable_change
        
        # Accounts Payable
        payable_change = self._get_working_capital_change(
            ['liability_payable'], options
        )
        if payable_change != 0:
            lines.append({
                'name': _('  Accounts Payable'),
                'level': 3,
                'columns': [{'name': self._format_value(payable_change)}],
            })
            total += payable_change
        
        return total

    def _add_investing_activities(self, lines, options):
        """Add investing activities section"""
        total = 0.0
        
        # Fixed Assets purchases/sales
        fixed_asset_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['asset_fixed', 'asset_non_current']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        for account in fixed_asset_accounts:
            balance_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            balance = balance_data['balance']
            
            if balance == 0:
                continue
            
            lines.append({
                'name': f"{account.code} {account.name}",
                'level': 2,
                'columns': [{'name': self._format_value(-balance)}],
            })
            total -= balance
        
        if total == 0:
            lines.append({
                'name': _('No investing activities'),
                'level': 2,
                'columns': [{'name': '-'}],
            })
        
        return total

    def _add_financing_activities(self, lines, options):
        """Add financing activities section"""
        total = 0.0
        
        # Loans and equity
        financing_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['liability_non_current', 'equity']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        for account in financing_accounts:
            balance_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            balance = balance_data['balance']
            
            if balance == 0:
                continue
            
            lines.append({
                'name': f"{account.code} {account.name}",
                'level': 2,
                'columns': [{'name': self._format_value(-balance)}],
            })
            total -= balance
        
        if total == 0:
            lines.append({
                'name': _('No financing activities'),
                'level': 2,
                'columns': [{'name': '-'}],
            })
        
        return total

    def _get_net_income(self, options):
        """Calculate net income for the period"""
        income_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['income', 'income_other']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        expense_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        income_total = 0.0
        for account in income_accounts:
            balance_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            income_total -= balance_data['balance']
        
        expense_total = 0.0
        for account in expense_accounts:
            balance_data = self._compute_account_balance(
                account,
                options.get('date_from'),
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            expense_total += balance_data['balance']
        
        return income_total - expense_total

    def _get_working_capital_change(self, account_types, options):
        """Get change in working capital accounts"""
        accounts = self.env['account.account'].search([
            ('account_type', 'in', account_types),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        beginning_balance = 0.0
        ending_balance = 0.0
        
        for account in accounts:
            beginning_balance += self._compute_initial_balance(
                account, options.get('date_from')
            )
            
            balance_data = self._compute_account_balance(
                account,
                date_from=None,
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            ending_balance += balance_data['balance']
        
        return ending_balance - beginning_balance

    def _make_header(self, name):
        """Create a header line"""
        return {
            'name': name,
            'level': 1,
            'class': 'o_account_reports_level1',
            'columns': [{'name': ''}],
        }

    def _make_total_line(self, name, amount, level=1, class_name='total'):
        """Create a total line"""
        return {
            'name': name,
            'level': level,
            'class': class_name,
            'columns': [{'name': self._format_value(amount)}],
        }

    def _get_columns(self, options):
        """Override columns for cash flow"""
        return [
            {'name': 'Cash Flow'},
            {'name': f"{options.get('date_from')} to {options.get('date_to')}"},
        ]
