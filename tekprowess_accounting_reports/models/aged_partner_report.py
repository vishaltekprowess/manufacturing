# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta


class AgedPartnerReport(models.TransientModel):
    _name = 'tekprowess.aged.partner.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Aged Partner Balance'

    report_type = fields.Selection([
        ('receivable', 'Aged Receivable'),
        ('payable', 'Aged Payable'),
    ], string='Report Type', default='receivable', required=True)

    def _get_report_name(self):
        if self.report_type == 'receivable':
            return "Aged Receivable"
        return "Aged Payable"

    def _get_lines(self, options):
        lines = []
        
        # Determine account type and invoice types
        if options.get('report_type', 'receivable') == 'receivable':
            account_type = 'asset_receivable'
            invoice_types = ['out_invoice', 'out_refund']
        else:
            account_type = 'liability_payable'
            invoice_types = ['in_invoice', 'in_refund']
        
        # Get partners with outstanding balances
        partners = self._get_partners_with_balance(account_type, options)
        
        total_buckets = {
            'total': 0.0,
            'current': 0.0,
            '1_30': 0.0,
            '31_60': 0.0,
            '61_90': 0.0,
            '91_120': 0.0,
            'older': 0.0,
        }
        
        as_of_date = fields.Date.from_string(options.get('date_to'))
        
        for partner in partners:
            # Get unpaid/partially paid invoices
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('move_type', 'in', invoice_types),
                ('invoice_date', '<=', options.get('date_to')),
            ])
            
            if not invoices:
                continue
            
            # Age buckets
            buckets = {
                'current': 0.0,
                '1_30': 0.0,
                '31_60': 0.0,
                '61_90': 0.0,
                '91_120': 0.0,
                'older': 0.0,
            }
            
            for invoice in invoices:
                amount_due = invoice.amount_residual
                
                # Handle refunds
                if invoice.move_type in ['out_refund', 'in_refund']:
                    amount_due = -amount_due
                
                if amount_due == 0:
                    continue
                
                # Calculate days overdue from due date
                due_date = invoice.invoice_date_due or invoice.invoice_date
                if not due_date:
                    continue
                
                days_due = (as_of_date - due_date).days
                
                # Categorize into buckets
                if days_due <= 0:
                    buckets['current'] += amount_due
                elif days_due <= 30:
                    buckets['1_30'] += amount_due
                elif days_due <= 60:
                    buckets['31_60'] += amount_due
                elif days_due <= 90:
                    buckets['61_90'] += amount_due
                elif days_due <= 120:
                    buckets['91_120'] += amount_due
                else:
                    buckets['older'] += amount_due
            
            partner_total = sum(buckets.values())
            if partner_total == 0:
                continue
            
            # Add partner line
            lines.append({
                'id': f'partner_{partner.id}',
                'name': partner.name,
                'level': 1,
                'columns': [
                    {'name': self._format_value(partner_total), 'no_format': partner_total},
                    {'name': self._format_value(buckets['current']), 'no_format': buckets['current']},
                    {'name': self._format_value(buckets['1_30']), 'no_format': buckets['1_30']},
                    {'name': self._format_value(buckets['31_60']), 'no_format': buckets['31_60']},
                    {'name': self._format_value(buckets['61_90']), 'no_format': buckets['61_90']},
                    {'name': self._format_value(buckets['91_120']), 'no_format': buckets['91_120']},
                    {'name': self._format_value(buckets['older']), 'no_format': buckets['older']},
                ],
                'caret_options': 'res.partner',
                'unfoldable': True,
                'unfolded': False,
            })
            
            # Accumulate totals
            total_buckets['total'] += partner_total
            for key in ['current', '1_30', '31_60', '61_90', '91_120', 'older']:
                total_buckets[key] += buckets[key]
        
        # Add total line
        if lines:
            lines.append({
                'name': _('Total'),
                'level': 0,
                'class': 'total o_account_reports_domain_total',
                'columns': [
                    {'name': self._format_value(total_buckets['total']), 'no_format': total_buckets['total']},
                    {'name': self._format_value(total_buckets['current']), 'no_format': total_buckets['current']},
                    {'name': self._format_value(total_buckets['1_30']), 'no_format': total_buckets['1_30']},
                    {'name': self._format_value(total_buckets['31_60']), 'no_format': total_buckets['31_60']},
                    {'name': self._format_value(total_buckets['61_90']), 'no_format': total_buckets['61_90']},
                    {'name': self._format_value(total_buckets['91_120']), 'no_format': total_buckets['91_120']},
                    {'name': self._format_value(total_buckets['older']), 'no_format': total_buckets['older']},
                ],
            })
        
        return lines

    def _get_partners_with_balance(self, account_type, options):
        """Get partners with outstanding balance"""
        # Determine invoice types
        if account_type == 'asset_receivable':
            invoice_types = ['out_invoice', 'out_refund']
        else:
            invoice_types = ['in_invoice', 'in_refund']
        
        # Find invoices with residual amount
        invoices = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('move_type', 'in', invoice_types),
            ('invoice_date', '<=', options.get('date_to')),
            ('amount_residual', '!=', 0),
        ])
        
        partner_ids = invoices.mapped('partner_id').filtered(lambda p: p)
        return partner_ids.sorted('name')

    def _get_columns(self, options):
        """Define columns for aged partner report"""
        return [
            {'name': _('Partner'), 'class': 'text-left'},
            {'name': _('Total Due'), 'class': 'number'},
            {'name': _('Not Due'), 'class': 'number'},
            {'name': _('1-30 Days'), 'class': 'number'},
            {'name': _('31-60 Days'), 'class': 'number'},
            {'name': _('61-90 Days'), 'class': 'number'},
            {'name': _('91-120 Days'), 'class': 'number'},
            {'name': _('120+ Days'), 'class': 'number'},
        ]
