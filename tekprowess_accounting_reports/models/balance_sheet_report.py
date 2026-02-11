# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class BalanceSheetReport(models.TransientModel):
    _name = 'tekprowess.balance.sheet.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Balance Sheet'

    def _get_report_name(self):
        return "Balance Sheet"

    def _get_lines(self, options):
        lines = []
        
        # ==================
        # ASSETS
        # ==================
        lines.append(self._make_header(_('ASSETS')))
        
        # Current Assets
        current_asset_types = ['asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments']
        current_assets_total = self._add_asset_section(
            lines, _('Current Assets'), current_asset_types, options
        )
        
        # Non-Current Assets
        non_current_asset_types = ['asset_non_current', 'asset_fixed']
        non_current_assets_total = self._add_asset_section(
            lines, _('Non-Current Assets'), non_current_asset_types, options
        )
        
        # Total Assets
        total_assets = current_assets_total + non_current_assets_total
        lines.append(self._make_total_line(
            _('TOTAL ASSETS'), total_assets, level=0, class_name='total o_account_reports_domain_total'
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # LIABILITIES
        # ==================
        lines.append(self._make_header(_('LIABILITIES')))
        
        # Current Liabilities
        current_liab_types = ['liability_current', 'liability_payable']
        current_liab_total = self._add_liability_section(
            lines, _('Current Liabilities'), current_liab_types, options
        )
        
        # Non-Current Liabilities
        non_current_liab_types = ['liability_non_current']
        non_current_liab_total = self._add_liability_section(
            lines, _('Non-Current Liabilities'), non_current_liab_types, options
        )
        
        # Total Liabilities
        total_liabilities = current_liab_total + non_current_liab_total
        lines.append(self._make_total_line(
            _('TOTAL LIABILITIES'), total_liabilities, level=0, class_name='total o_account_reports_level0'
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # ==================
        # EQUITY
        # ==================
        lines.append(self._make_header(_('EQUITY')))
        
        equity_total = self._add_equity_section(lines, options)
        
        lines.append(self._make_total_line(
            _('TOTAL EQUITY'), equity_total, level=0, class_name='total o_account_reports_level0'
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # Total Liabilities + Equity
        total_liab_equity = total_liabilities + equity_total
        lines.append(self._make_total_line(
            _('TOTAL LIABILITIES + EQUITY'), 
            total_liab_equity, 
            level=0, 
            class_name='total o_account_reports_domain_total'
        ))
        
        return lines

    def _add_asset_section(self, lines, title, account_types, options):
        """Add asset section"""
        lines.append({
            'name': title,
            'level': 1,
            'class': 'o_account_reports_level1',
            'columns': self._get_blank_columns(options),
        })
        
        accounts = self.env['account.account'].search([
            ('account_type', 'in', account_types),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        total = 0.0
        
        for account in accounts:
            balance_data = self._compute_account_balance(
                account,
                date_from=None,  # Balance sheet is cumulative
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            balance = balance_data['balance']
            
            if balance == 0 and not options.get('unfold_all'):
                continue
            
            total += balance
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 3,
                'columns': [{'name': self._format_value(balance)}],
                'caret_options': 'account',
            })
        
        # Subtotal
        lines.append({
            'name': f"{_('Total')} {title}",
            'level': 2,
            'class': 'total',
            'columns': [{'name': self._format_value(total)}],
        })
        
        return total

    def _add_liability_section(self, lines, title, account_types, options):
        """Add liability section"""
        lines.append({
            'name': title,
            'level': 1,
            'class': 'o_account_reports_level1',
            'columns': self._get_blank_columns(options),
        })
        
        accounts = self.env['account.account'].search([
            ('account_type', 'in', account_types),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        total = 0.0
        
        for account in accounts:
            balance_data = self._compute_account_balance(
                account,
                date_from=None,  # Balance sheet is cumulative
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            # Liabilities are shown as positive (credit balance)
            balance = -balance_data['balance']
            
            if balance == 0 and not options.get('unfold_all'):
                continue
            
            total += balance
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 3,
                'columns': [{'name': self._format_value(balance)}],
                'caret_options': 'account',
            })
        
        # Subtotal
        lines.append({
            'name': f"{_('Total')} {title}",
            'level': 2,
            'class': 'total',
            'columns': [{'name': self._format_value(total)}],
        })
        
        return total

    def _add_equity_section(self, lines, options):
        """Add equity section"""
        accounts = self.env['account.account'].search([
            ('account_type', 'in', ['equity', 'equity_unaffected']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        total = 0.0
        
        for account in accounts:
            balance_data = self._compute_account_balance(
                account,
                date_from=None,
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            # Equity is shown as positive (credit balance)
            balance = -balance_data['balance']
            
            if balance == 0 and not options.get('unfold_all'):
                continue
            
            total += balance
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 2,
                'columns': [{'name': self._format_value(balance)}],
                'caret_options': 'account',
            })
        
        # Add current year earnings
        current_year_earnings = self._compute_current_year_earnings(options)
        if current_year_earnings != 0 or options.get('unfold_all'):
            lines.append({
                'name': _('Current Year Earnings'),
                'level': 2,
                'columns': [{'name': self._format_value(current_year_earnings)}],
            })
            total += current_year_earnings
        
        return total

    def _compute_current_year_earnings(self, options):
        """Compute current year unallocated earnings"""
        # Get profit/loss for the period
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
                date_from=self.env.company.compute_fiscalyear_dates(
                    fields.Date.from_string(options['date_to'])
                )['date_from'],
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            income_total -= balance_data['balance']  # Income is credit
        
        expense_total = 0.0
        for account in expense_accounts:
            balance_data = self._compute_account_balance(
                account,
                date_from=self.env.company.compute_fiscalyear_dates(
                    fields.Date.from_string(options['date_to'])
                )['date_from'],
                date_to=options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            expense_total += balance_data['balance']  # Expense is debit
        
        return income_total - expense_total

    def _make_header(self, name):
        """Create a header line"""
        return {
            'name': name,
            'level': 0,
            'class': 'o_account_reports_level0',
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

    def _get_blank_columns(self, options):
        """Get blank columns"""
        return [{'name': ''}]

    def _get_columns(self, options):
        """Override columns for balance sheet"""
        date_str = options.get('date_to', fields.Date.context_today(self))
        return [
            {'name': 'Account'},
            {'name': f"As of {date_str}"},
        ]
