# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProfitLossReport(models.TransientModel):
    _name = 'tekprowess.profit.loss.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Profit & Loss Statement'

    def _get_report_name(self):
        return "Profit & Loss"

    def _get_lines(self, options):
        lines = []
        
        # Revenue Section
        revenue_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['income', 'income_other']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        revenue_total = self._add_section(
            lines, _('Revenue'), revenue_accounts, options, negative=True
        )
        
        # Cost of Revenue (COGS)
        cogs_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense_direct_cost'),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        cogs_total = self._add_section(
            lines, _('Cost of Revenue'), cogs_accounts, options
        )
        
        # Gross Profit
        gross_profit = revenue_total - cogs_total
        lines.append(self._make_total_line(
            _('Gross Profit'), gross_profit, level=0, bold=True
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # Operating Expenses
        expense_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        expense_total = self._add_section(
            lines, _('Operating Expenses'), expense_accounts, options
        )
        
        # Operating Income
        operating_income = gross_profit - expense_total
        lines.append(self._make_total_line(
            _('Operating Income'), operating_income, level=0, bold=True
        ))
        
        lines.append({'name': ''})  # Blank line
        
        # Depreciation
        depreciation_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense_depreciation'),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        depreciation_total = self._add_section(
            lines, _('Depreciation'), depreciation_accounts, options
        )
        
        # Other Income/Expenses
        other_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['income_other', 'expense_direct_cost']),
            ('company_ids', 'in', [self.env.company.id]),
        ])
        
        # Net Income Before Tax
        net_before_tax = operating_income - depreciation_total
        lines.append(self._make_total_line(
            _('Net Income Before Tax'), net_before_tax, level=0, bold=True
        ))
        
        # Net Income (Final)
        lines.append({'name': ''})  # Blank line
        lines.append(self._make_total_line(
            _('NET INCOME'), net_before_tax, level=0, bold=True, class_name='total o_account_reports_domain_total'
        ))
        
        return lines

    def _add_section(self, lines, title, accounts, options, negative=False):
        """Add a section with accounts and return total"""
        lines.append({
            'name': title,
            'level': 0,
            'class': 'o_account_reports_level0',
            'columns': self._get_blank_columns(options),
        })
        
        total = 0.0
        comparison_total = 0.0
        
        for account in accounts:
            balance_data = self._compute_account_balance(
                account, 
                options.get('date_from'), 
                options.get('date_to'),
                state='all' if options.get('all_entries') else 'posted'
            )
            balance = balance_data['balance'] * (-1 if negative else 1)
            
            # Skip zero balances unless unfold_all
            if balance == 0 and not options.get('unfold_all'):
                continue
            
            total += balance
            
            # Comparison if enabled
            comparison_balance = 0.0
            if options.get('comparison'):
                comp_data = self._get_comparison_data(options)
                comp_balance_data = self._compute_account_balance(
                    account,
                    comp_data['date_from'],
                    comp_data['date_to'],
                    state='all' if options.get('all_entries') else 'posted'
                )
                comparison_balance = comp_balance_data['balance'] * (-1 if negative else 1)
                comparison_total += comparison_balance
            
            columns = self._format_account_columns(balance, comparison_balance, options)
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 2,
                'columns': columns,
                'caret_options': 'account',
            })
        
        # Section total
        comp_cols = []
        if options.get('comparison'):
            variation = total - comparison_total
            variation_pct = (variation / comparison_total * 100) if comparison_total else 0
            comp_cols = [
                {'name': self._format_value(comparison_total)},
                {'name': self._format_value(variation)},
                {'name': self._format_value(variation_pct, 'percentage')},
            ]
        
        lines.append({
            'name': f"{_('Total')} {title}",
            'level': 1,
            'class': 'total',
            'columns': [{'name': self._format_value(total)}] + comp_cols,
        })
        
        return total

    def _format_account_columns(self, balance, comparison_balance, options):
        """Format columns for account line"""
        columns = [{'name': self._format_value(balance)}]
        
        if options.get('comparison'):
            variation = balance - comparison_balance
            variation_pct = (variation / comparison_balance * 100) if comparison_balance else 0
            
            columns.extend([
                {'name': self._format_value(comparison_balance)},
                {'name': self._format_value(variation)},
                {'name': self._format_value(variation_pct, 'percentage')},
            ])
        
        return columns

    def _make_total_line(self, name, amount, level=1, bold=False, class_name='total'):
        """Create a total line"""
        return {
            'name': name,
            'level': level,
            'class': class_name,
            'columns': [{'name': self._format_value(amount)}],
        }

    def _get_blank_columns(self, options):
        """Get blank columns matching the structure"""
        count = 1
        if options.get('comparison'):
            count = 4  # Current + Comparison + Variation + Variation %
        return [{'name': ''}] * count
