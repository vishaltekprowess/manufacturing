# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import date_utils
from datetime import datetime, timedelta
import io
import base64
from collections import defaultdict


class FinancialReportAbstract(models.AbstractModel):
    """Base class for all financial reports"""
    _name = 'tekprowess.financial.report.abstract'
    _description = 'Financial Report Base Class'

    def _get_report_name(self):
        """Override in child classes"""
        return "Financial Report"

    def _get_columns(self, options):
        """Return column definitions for the report"""
        columns = [{'name': 'Account'}]
        
        # Add date columns
        if options.get('date_from') and options.get('date_to'):
            columns.append({'name': f"{options['date_from']} to {options['date_to']}"})
        
        # Add comparison columns if enabled
        if options.get('comparison'):
            columns.append({'name': 'Previous Period'})
            columns.append({'name': 'Variation'})
            columns.append({'name': 'Variation %'})
        
        return columns

    @api.model
    def get_report_data(self, options):
        """Get report data for client action"""
        report = self.create({})
        return {
            'lines': report._get_lines(options),
            'columns': report._get_columns(options),
            'report_name': report._get_report_name(),
        }

    @api.model
    def action_open_line(self, line_id, options):
        """Open underlying records for a report line"""
        if not line_id:
            return None
            
        domain = [('company_id', '=', self.env.company.id)]
        model = 'account.move.line'
        name = _('Journal Items')
        
        # Parse line_id
        if isinstance(line_id, str):
            if line_id.startswith('account_'):
                account_id = int(line_id.split('_')[1])
                domain.append(('account_id', '=', account_id))
            elif line_id.startswith('partner_'):
                partner_id = int(line_id.split('_')[1])
                domain.append(('partner_id', '=', partner_id))
            elif line_id.startswith('aml_'):
                aml_id = int(line_id.split('_')[1])
                aml = self.env['account.move.line'].browse(aml_id)
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': aml.move_id.id,
                    'view_mode': 'form',
                    'views': [(False, 'form')],
                }
        
        # Add filters
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        
        if options.get('all_entries'):
            domain.append(('parent_state', '!=', 'cancel'))
        else:
            domain.append(('parent_state', '=', 'posted'))
            
        if options.get('journals'):
            domain.append(('journal_id', 'in', options['journals']))
            
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
        }

    def _get_lines(self, options):
        """Override in child classes to generate report lines"""
        return []

    def _format_value(self, value, figure_type='monetary'):
        """Format values for display"""
        if figure_type == 'monetary':
            return self.env.company.currency_id.format(value) if value else '-'
        elif figure_type == 'percentage':
            return f"{value:.2f}%" if value else '-'
        else:
            return str(value) if value else '-'

    def _get_account_move_lines(self, options, accounts=None):
        """Get account move lines based on options"""
        domain = [('company_id', '=', self.env.company.id)]
        
        # Date filtering
        if options.get('date_from'):
            domain.append(('date', '>=', options['date_from']))
        if options.get('date_to'):
            domain.append(('date', '<=', options['date_to']))
        
        # State filtering
        if options.get('all_entries'):
            domain.append(('parent_state',  '!=', 'cancel'))
        else:
            domain.append(('parent_state', '=', 'posted'))
        
        # Account filtering
        if accounts:
            domain.append(('account_id', 'in', accounts.ids))
        
        # Journal filtering
        if options.get('journals'):
            domain.append(('journal_id', 'in', options['journals']))
        
        return self.env['account.move.line'].search(domain)

    def _compute_account_balance(self, account, date_from=None, date_to=None, state='posted'):
        """Compute balance for an account"""
        domain = [
            ('account_id', '=', account.id),
            ('company_id', '=', self.env.company.id),
        ]
        
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        
        if state == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        else:
            domain.append(('parent_state', '!=', 'cancel'))
        
        move_lines = self.env['account.move.line'].search(domain)
        
        balance = sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))
        debit = sum(move_lines.mapped('debit'))
        credit = sum(move_lines.mapped('credit'))
        
        return {
            'balance': balance,
            'debit': debit,
            'credit': credit,
        }

    def _compute_initial_balance(self, account, date_from):
        """Compute initial balance before date_from"""
        if not date_from:
            return 0.0
        
        domain = [
            ('account_id', '=', account.id),
            ('company_id', '=', self.env.company.id),
            ('date', '<', date_from),
            ('parent_state', '=', 'posted'),
        ]
        
        move_lines = self.env['account.move.line'].search(domain)
        return sum(move_lines.mapped('debit')) - sum(move_lines.mapped('credit'))

    def get_pdf(self, options):
        """Get report as PDF file content"""
        # Construct template name dynamically
        model_parts = self._name.split('.')[1:-1]
        report_name = "_".join(model_parts)
        template_name = f"tekprowess_accounting_reports.report_{report_name}_document"
        
        # Create report instance and calculate data
        report = self.create({})
        lines = report._get_lines(options)
        columns = report._get_columns(options)
        
        data = {
            'options': options,
            'lines': lines,
            'columns': columns,
            'report_name': report._get_report_name(),
            'date_from': options.get('date_from'),
            'date_to': options.get('date_to'),
            'company_name': self.env.company.name,
        }
        
        # We need to find the report action to get the report object
        report_action = self.env['ir.actions.report'].search([('report_name', '=', template_name)], limit=1)
        if not report_action:
             # Fallback or error
             raise UserError(_("Report template not found: %s", template_name))

        # Render PDF
        # We use strict=False to avoid errors if qweb context is slightly different
        pdf_content, _ = report_action._render_qweb_pdf(report_action.id, res_ids=report.ids, data=data)
        return pdf_content

    def get_xlsx(self, options):
        """Get report as Excel file content"""
        try:
            from io import BytesIO
            import xlsxwriter
        except ImportError:
            raise UserError(_("The 'xlsxwriter' Python module is not installed. Please install it with: pip install xlsxwriter"))
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self._get_report_name())
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1
        })
        
        # Write headers
        columns = self._get_columns(options)
        for col_idx, column in enumerate(columns):
            sheet.write(0, col_idx, column['name'], header_format)
        
        # Write data
        lines = self._get_lines(options)
        row = 1
        for line in lines:
            # Column 0: Name (with indentation)
            indent = line.get('level', 0)
            name_format = workbook.add_format({'indent': indent})
            sheet.write(row, 0, line.get('name', ''), name_format)

            # Columns 1+: Data
            for col_idx, col_data in enumerate(line.get('columns', [])):
                sheet.write(row, col_idx + 1, col_data.get('name', ''))
            row += 1
        
        workbook.close()
        output.seek(0)
        return output.read()

    def _get_options(self, previous_options=None):
        """Build default options"""
        options = previous_options or {}
        
        # Default date range: current fiscal year
        today = fields.Date.context_today(self)
        fiscal_dates = self.env.company.compute_fiscalyear_dates(today)
        
        if not options.get('date_from'):
            options['date_from'] = fiscal_dates['date_from']
        if not options.get('date_to'):
            options['date_to'] = fiscal_dates['date_to']
        
        # Default settings
        options.setdefault('all_entries', False)
        options.setdefault('comparison', False)
        options.setdefault('journals', [])
        options.setdefault('unfold_all', False)
        
        return options

    def _get_comparison_data(self, options):
        """Get data for comparison period"""
        if not options.get('comparison'):
            return None
        
        date_from = fields.Date.from_string(options['date_from'])
        date_to = fields.Date.from_string(options['date_to'])
        
        # Calculate previous period
        delta = date_to - date_from
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - delta
        
        return {
            'date_from': prev_date_from,
            'date_to': prev_date_to,
        }
