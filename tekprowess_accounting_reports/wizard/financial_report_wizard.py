# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FinancialReportWizard(models.TransientModel):
    _name = 'financial.report.wizard'
    _description = 'Financial Report Wizard'

    report_type = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow Statement'),
        ('trial_balance', 'Trial Balance'),
        ('general_ledger', 'General Ledger'),
        ('partner_ledger', 'Partner Ledger'),
        ('aged_receivable', 'Aged Receivable'),
        ('aged_payable', 'Aged Payable'),
        ('tax_report', 'Tax Report'),
    ], string='Report Type', required=True, default='profit_loss')

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True, default=fields.Date.context_today)
    
    comparison = fields.Boolean('Enable Comparison')
    comparison_type = fields.Selection([
        ('previous_period', 'Previous Period'),
        ('same_last_year', 'Same Period Last Year'),
    ], string='Compare With', default='previous_period')

    all_entries = fields.Boolean('Include Unposted Entries', default=False)
    unfold_all = fields.Boolean('Unfold All', default=False)
    
    journal_ids = fields.Many2many('account.journal', string='Journals')
    
    # Partner ledger specific
    partner_type = fields.Selection([
        ('customer', 'Customers'),
        ('supplier', 'Suppliers'),
        ('all', 'All Partners'),
    ], string='Partner Type', default='all')

    @api.onchange('report_type')
    def _onchange_report_type(self):
        """Set default date range based on report type"""
        today = fields.Date.context_today(self)
        fiscal_dates = self.env.company.compute_fiscalyear_dates(today)
        
        # Balance sheet needs a single date (as of date)
        if self.report_type == 'balance_sheet':
            self.date_from = fiscal_dates['date_from']
            self.date_to = today
        else:
            self.date_from = fiscal_dates['date_from']
            self.date_to = fiscal_dates['date_to']

    @api.model
    def default_get(self, fields_list):
        """Set default dates"""
        res = super().default_get(fields_list)
        
        if 'date_from' in fields_list or 'date_to' in fields_list:
            today = fields.Date.context_today(self)
            fiscal_dates = self.env.company.compute_fiscalyear_dates(today)
            
            if 'date_from' in fields_list:
                res['date_from'] = fiscal_dates['date_from']
            if 'date_to' in fields_list:
                res['date_to'] = fiscal_dates['date_to']
        
        return res

    def generate_report(self):
        """Generate and display the selected report"""
        self.ensure_one()
        
        # Build options
        options = self._build_options()
        
        # Get the report model
        report_model = self._get_report_model()
        
        if not report_model:
            raise UserError(_('Invalid report type selected'))
        
        # Store in context for the tree view
        context = {
            'report_options': options,
            'report_name': dict(self._fields['report_type'].selection)[self.report_type],
        }
        
        # Return action to open report view
        return {
            'type': 'ir.actions.client',
            'tag': 'financial_report',
            'name': dict(self._fields['report_type'].selection)[self.report_type],
            'res_model': report_model,
            'context': context,
            'params': {
                'options': options,
            }
        }

    def export_pdf(self):
        """Export report to PDF"""
        self.ensure_one()
        
        options = self._build_options()
        report_model = self._get_report_model()
        
        report = self.env[report_model].create({})
        return report.export_to_pdf(options)

    def export_xlsx(self):
        """Export report to Excel"""
        self.ensure_one()
        
        options = self._build_options()
        report_model = self._get_report_model()
        
        report = self.env[report_model].create({})
        return report.export_to_xlsx(options)

    def _build_options(self):
        """Build options dictionary from wizard fields"""
        options = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'comparison': self.comparison,
            'comparison_type': self.comparison_type if self.comparison else False,
            'all_entries': self.all_entries,
            'unfold_all': self.unfold_all,
            'journals': self.journal_ids.ids,
            'company_id': self.env.company.id,
        }
        
        # Add report-specific options
        if self.report_type == 'partner_ledger':
            options['partner_type'] = self.partner_type
        elif self.report_type in ['aged_receivable', 'aged_payable']:
            options['report_type'] = 'receivable' if self.report_type == 'aged_receivable' else 'payable'
        
        return options

    def _get_report_model(self):
        """Get the report model name based on report type"""
        report_models = {
            'profit_loss': 'tekprowess.profit.loss.report',
            'balance_sheet': 'tekprowess.balance.sheet.report',
            'cash_flow': 'tekprowess.cash.flow.report',
            'trial_balance': 'tekprowess.trial.balance.report',
            'general_ledger': 'tekprowess.general.ledger.report',
            'partner_ledger': 'tekprowess.partner.ledger.report',
            'aged_receivable': 'tekprowess.aged.partner.report',
            'aged_payable': 'tekprowess.aged.partner.report',
            'tax_report': 'tekprowess.tax.report',
        }
        
        return report_models.get(self.report_type)
