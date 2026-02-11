# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PartnerLedgerReport(models.TransientModel):
    _name = 'tekprowess.partner.ledger.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Partner Ledger'

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
        ('all', 'All Partners'),
    ], string='Partner Type', default='all')

    def _get_report_name(self):
        return "Partner Ledger"

    def _get_lines(self, options):
        lines = []
        
        # Determine account types based on partner type
        if options.get('partner_type') == 'customer':
            account_types = ['asset_receivable']
        elif options.get('partner_type') == 'supplier':
            account_types = ['liability_payable']
        else:
            account_types = ['asset_receivable', 'liability_payable']
        
        # Get partners with transactions
        partners = self._get_partners_with_transactions(account_types, options)
        
        for partner in partners:
            # Partner header
            partner_initial_balance = self._get_partner_initial_balance(
                partner, account_types, options
            )
            
            # Get partner move lines
            move_lines = self._get_partner_move_lines(
                partner, account_types, options
            )
            
            if not move_lines and partner_initial_balance == 0:
                if not options.get('unfold_all'):
                    continue
            
            partner_final_balance = partner_initial_balance + sum(
                ml.debit - ml.credit for ml in move_lines
            )
            
            lines.append({
                'id': f'partner_{partner.id}',
                'name': partner.name,
                'level': 0,
                'class': 'o_account_reports_level0',
                'unfoldable': True,
                'unfolded': options.get('unfold_all', False),
                'columns': [
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': ''},
                    {'name': self._format_value(partner_final_balance)},
                ],
                'caret_options': 'res.partner',
            })
            
            # Initial balance
            if partner_initial_balance != 0:
                lines.append({
                    'name': _('Initial Balance'),
                    'level': 1,
                    'parent_id': f'partner_{partner.id}',
                    'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': ''},
                        {'name': self._format_value(partner_initial_balance if partner_initial_balance > 0 else 0)},
                        {'name': self._format_value(-partner_initial_balance if partner_initial_balance < 0 else 0)},
                        {'name': self._format_value(partner_initial_balance)},
                    ],
                })
            
            # Move lines
            running_balance = partner_initial_balance
            for move_line in move_lines.sorted('date'):
                running_balance += move_line.debit - move_line.credit
                
                lines.append({
                    'id': f'aml_{move_line.id}',
                    'name': move_line.move_id.name or '',
                    'level': 1,
                    'parent_id': f'partner_{partner.id}',
                    'caret_options': 'account.move.line',
                    'columns': [
                        {'name': move_line.date.strftime('%Y-%m-%d')},
                        {'name': move_line.account_id.code or ''},
                        {'name': move_line.move_id.name or ''},
                        {'name': move_line.name or ''},
                        {'name': self._format_value(move_line.debit)},
                        {'name': self._format_value(move_line.credit)},
                        {'name': self._format_value(running_balance)},
                    ],
                })
            
            # Partner total
            total_debit = sum(move_lines.mapped('debit'))
            total_credit = sum(move_lines.mapped('credit'))
            
            lines.append({
                'name': _('Total') + f" {partner.name}",
                'level': 1,
                'class': 'total',
                'parent_id': f'partner_{partner.id}',
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

    def _get_partners_with_transactions(self, account_types, options):
        """Get partners with transactions in the period"""
        domain = [
            ('company_id', '=', self.env.company.id),
            ('account_id.account_type', 'in', account_types),
        ]
        
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        
        if options.get('all_entries'):
            domain.append(('parent_state', '!=', 'cancel'))
        else:
            domain.append(('parent_state', '=', 'posted'))
        
        move_lines = self.env['account.move.line'].search(domain)
        partner_ids = move_lines.mapped('partner_id').filtered(lambda p: p)
        
        return partner_ids.sorted('name')

    def _get_partner_initial_balance(self, partner, account_types, options):
        """Get initial balance for a partner"""
        if not options.get('date_from'):
            return 0.0
        
        domain = [
            ('partner_id', '=', partner.id),
            ('company_id', '=', self.env.company.id),
            ('account_id.account_type', 'in', account_types),
            ('date', '<', options['date_from']),
            ('parent_state', '=', 'posted'),
        ]
        
        move_lines = self.env['account.move.line'].search(domain)
        return sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))

    def _get_partner_move_lines(self, partner, account_types, options):
        """Get move lines for a partner in the period"""
        domain = [
            ('partner_id', '=', partner.id),
            ('company_id', '=', self.env.company.id),
            ('account_id.account_type', 'in', account_types),
        ]
        
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        
        if options.get('all_entries'):
            domain.append(('parent_state', '!=', 'cancel'))
        else:
            domain.append(('parent_state', '=', 'posted'))
        
        return self.env['account.move.line'].search(domain)

    def _get_columns(self, options):
        """Define columns for partner ledger"""
        return [
            {'name': _('Partner'), 'class': 'text-left'},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Account'), 'class': 'text-center'},
            {'name': _('Ref'), 'class': 'text-left'},
            {'name': _('Label'), 'class': 'text-left'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'},
        ]
