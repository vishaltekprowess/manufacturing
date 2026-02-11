# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from collections import defaultdict


class TaxReport(models.TransientModel):
    _name = 'tekprowess.tax.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Tax Report'

    def _get_report_name(self):
        return "Tax Report"

    def _get_lines(self, options):
        lines = []
        
        # Get all taxes
        taxes = self.env['account.tax'].search([
            ('company_id', '=', self.env.company.id)
        ], order='sequence, name')
        
        if not taxes:
            return [{
                'name': _('No taxes configured'),
                'columns': [{'name': ''}],
            }]
        
        # Group taxes by type
        sales_taxes = taxes.filtered(lambda t: t.type_tax_use == 'sale')
        purchase_taxes = taxes.filtered(lambda t: t.type_tax_use == 'purchase')
        
        # Sales Tax Section
        if sales_taxes:
            lines.append(self._make_header(_('Sales Tax')))
            sales_total_base, sales_total_tax = self._add_tax_section(
                lines, sales_taxes, options, 'sale'
            )
            
            lines.append(self._make_total_line(
                _('Total Sales Tax'),
                sales_total_base,
                sales_total_tax,
                level=1
            ))
            lines.append({'name': ''})  # Blank line
        
        # Purchase Tax Section
        if purchase_taxes:
            lines.append(self._make_header(_('Purchase Tax')))
            purchase_total_base, purchase_total_tax = self._add_tax_section(
                lines, purchase_taxes, options, 'purchase'
            )
            
            lines.append(self._make_total_line(
                _('Total Purchase Tax'),
                purchase_total_base,
                purchase_total_tax,
                level=1
            ))
            lines.append({'name': ''})  # Blank line
        
        # Net Tax Position
        if sales_taxes and purchase_taxes:
            net_tax = sales_total_tax - purchase_total_tax
            lines.append(self._make_total_line(
                _('Net Tax Position (Payable/Refundable)'),
                0,  # No base for net position
                net_tax,
                level=0,
                class_name='total o_account_reports_domain_total'
            ))
        
        return lines

    def _add_tax_section(self, lines, taxes, options, tax_type):
        """Add tax section and return totals"""
        total_base = 0.0
        total_tax = 0.0
        
        for tax in taxes:
            # Get tax data from account.move.line
            base_amount, tax_amount = self._compute_tax_amounts(tax, options)
            
            if base_amount == 0 and tax_amount == 0:
                if not options.get('unfold_all'):
                    continue
            
            total_base += base_amount
            total_tax += tax_amount
            
            lines.append({
                'id': f'tax_{tax.id}',
                'name': f"{tax.name} ({tax.amount}%)",
                'level': 2,
                'columns': [
                    {'name': self._format_value(base_amount), 'no_format': base_amount},
                    {'name': self._format_value(tax_amount), 'no_format': tax_amount},
                ],
                'caret_options': 'account.tax',
            })
        
        return total_base, total_tax

    def _compute_tax_amounts(self, tax, options):
        """Compute base and tax amounts for a tax"""
        domain = [
            ('company_id', '=', self.env.company.id),
            ('tax_line_id', '=', tax.id),
        ]
        
        # Date filtering
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        
        # State filtering
        if options.get('all_entries'):
            domain.append(('parent_state', '!=', 'cancel'))
        else:
            domain.append(('parent_state', '=', 'posted'))
        
        # Get tax lines
        tax_lines = self.env['account.move.line'].search(domain)
        
        # Tax amount is the balance of tax lines
        tax_amount = sum(tax_lines.mapped('balance'))
        
        # Get base amount from invoice lines with this tax
        base_domain = [
            ('company_id', '=', self.env.company.id),
            ('tax_ids', 'in', [tax.id]),
            ('tax_line_id', '=', False),  # Exclude tax lines
        ]
        
        if options.get('date_from'):
            base_domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            base_domain.append(('date', '<=', options['date_to']))
        
        if options.get('all_entries'):
            base_domain.append(('parent_state', '!=', 'cancel'))
        else:
            base_domain.append(('parent_state', '=', 'posted'))
        
        base_lines = self.env['account.move.line'].search(base_domain)
        base_amount = sum(base_lines.mapped('balance'))
        
        # For sales tax, use absolute values; for purchase, consider sign
        if tax.type_tax_use == 'sale':
            base_amount = abs(base_amount)
            tax_amount = abs(tax_amount)
        else:
            base_amount = -base_amount if base_amount < 0 else base_amount
            tax_amount = -tax_amount if tax_amount < 0 else tax_amount
        
        return base_amount, tax_amount

    def _make_header(self, name):
        """Create a header line"""
        return {
            'name': name,
            'level': 1,
            'class': 'o_account_reports_level1',
            'columns': [
                {'name': ''},
                {'name': ''},
            ],
        }

    def _make_total_line(self, name, base_amount, tax_amount, level=1, class_name='total'):
        """Create a total line"""
        return {
            'name': name,
            'level': level,
            'class': class_name,
            'columns': [
                {'name': self._format_value(base_amount) if base_amount != 0 else ''},
                {'name': self._format_value(tax_amount)},
            ],
        }

    def _get_columns(self, options):
        """Define columns for tax report"""
        period_str = f"{options.get('date_from', '')} to {options.get('date_to', '')}"
        return [
            {'name': _('Tax'), 'class': 'text-left'},
            {'name': _('Tax Base') + f' ({period_str})', 'class': 'number'},
            {'name': _('Tax Amount') + f' ({period_str})', 'class': 'number'},
        ]
