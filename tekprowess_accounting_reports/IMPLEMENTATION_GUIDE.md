# Tekprowess Accounting Reports - Implementation Guide

## 📋 Overview

This document guides you through creating community-compatible accounting reports inspired by Enterprise features but with clean-room implementation.

---

## 🏗️ Module Structure

```
tekprowess_accounting_reports/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── financial_report.py (Abstract base class) ✅ Created
│   ├── profit_loss_report.py
│   ├── balance_sheet_report.py
│   ├── cash_flow_report.py
│   ├── trial_balance_report.py
│   ├── general_ledger_report.py
│   ├── partner_ledger_report.py
│   ├── aged_partner_report.py
│   └── tax_report.py
├── wizard/
│   ├── __init__.py
│   └── financial_report_wizard.py
├── views/
│   ├── report_templates.xml
│   ├── profit_loss_views.xml
│   ├── balance_sheet_views.xml
│   ├── cash_flow_views.xml
│   ├── trial_balance_views.xml
│   ├── general_ledger_views.xml
│   ├── partner_ledger_views.xml
│   ├── aged_partner_views.xml
│   ├── tax_report_views.xml
│   ├── financial_report_wizard_views.xml
│   └── menuitems.xml
├──security/
│   └── ir.model.access.csv
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── financial_reports.js
│   │   └── css/
│   │       └── reports.css
│   └── description/
│       ├── icon.png
│       └── index.html
└── README.md
```

---

## 🎯 Key Implementation Patterns (From Enterprise Analysis)

### 1. **Report Structure Pattern**

Each report inherits from the abstract base and implements:

```python
class ProfitLossReport(models.TransientModel):
    _name = 'tekprowess.profit.loss.report'
    _inherit = 'tekprowess.financial.report.abstract'
    _description = 'Profit & Loss Statement'

    def _get_report_name(self):
        return "Profit & Loss"

    def _get_lines(self, options):
        # 1. Get account data
        # 2. Group by account types (Revenue, COGS, Expenses)
        # 3. Calculate totals
        # 4. Return formatted lines
        pass
```

### 2. **Options Pattern** (From account_report.py analysis)

Reports use an `options` dictionary for configuration:

```python
options = {
    'date_from': '2024-01-01',
    'date_to': '2024-12-31',
    'comparison': {
        'enabled': True,
        'periods': 1,
        'type': 'previous_period',  # or 'same_last_year'
    },
    'journals': [1, 2, 3],  # Journal IDs
    'all_entries': False,  # Posted only
    'unfold_all': False,
    'company_id': 1,
    'multi_company': False,
}
```

### 3. **Line Structure Pattern**

```python
line = {
    'id': 'account_1000',
    'name': '1000 - Cash',
    'level': 2,  # Indentation level
    'unfoldable': True,
    'unfolded': False,
    'columns': [
        {'name': '\u200f1,000.00', 'no_format': 1000.00},
        {'name': '\u200f900.00', 'no_format': 900.00},
        {'name': '\u200f100.00', 'no_format': 100.00},
        {'name': '11.11%', 'no_format': 11.11},
    ],
    'caret_options': 'account_id',  # For drill-down
}
```

---

## 📊 Report Implementations

### **1. Profit & Loss (P&L)**

```python
# models/profit_loss_report.py
from odoo import models, api

class ProfitLossReport(models.TransientModel):
    _name = 'tekprowess.profit.loss.report'
    _inherit = 'tekprowess.financial.report.abstract'

    def _get_lines(self, options):
        lines = []
        
        # Revenue Section
        revenue_accounts = self.env['account.account'].search([
            ('account_type', 'in', ['income', 'income_other'])
        ])
        revenue_total = self._add_section(
            lines, 'Revenue', revenue_accounts, options, negative=True
        )
        
        # Cost of Goods Sold
        cogs_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense_direct_cost')
        ])
        cogs_total = self._add_section(
            lines, 'Cost of Goods Sold', cogs_accounts, options
        )
        
        # Gross Profit
        gross_profit = revenue_total - cogs_total
        lines.append(self._make_total_line(
            'Gross Profit', gross_profit, bold=True
        ))
        
        # Operating Expenses
        expense_accounts = self.env['account.account'].search([
            ('account_type', '=', 'expense')
        ])
        expense_total = self._add_section(
            lines, 'Operating Expenses', expense_accounts, options
        )
        
        # Net Income
        net_income = gross_profit - expense_total
        lines.append(self._make_total_line(
            'Net Income', net_income, bold=True, level=0
        ))
        
        return lines

    def _add_section(self, lines, title, accounts, options, negative=False):
        """Add a section with accounts"""
        lines.append({
            'name': title,
            'level': 0,
            'class': 'total',
            'columns': [{'name': ''}] * len(self._get_columns(options))
        })
        
        total = 0.0
        for account in accounts:
            balance_data = self._compute_account_balance(
                account, 
                options['date_from'], 
                options['date_to']
            )
            balance = balance_data['balance'] * (-1 if negative else 1)
            total += balance
            
            # Skip zero balances unless unfold_all
            if balance == 0 and not options.get('unfold_all'):
                continue
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 2,
                'columns': self._format_columns(balance, options),
                'caret_options': 'account',
            })
        
        # Section total
        lines.append({
            'name': f"Total {title}",
            'level': 1,
            'class': 'total',
            'columns': self._format_columns(total, options),
        })
        
        return total
```

### **2. Balance Sheet**

```python
# models/balance_sheet_report.py
class BalanceSheetReport(models.TransientModel):
    _name = 'tekprowess.balance.sheet.report'
    _inherit = 'tekprowess.financial.report.abstract'

    def _get_lines(self, options):
        lines = []
        
        # ASSETS
        lines.append(self._make_header('ASSETS'))
        
        # Current Assets
        current_assets = self._add_asset_section(
            lines, 'Current Assets', 
            ['asset_receivable', 'asset_cash', 'asset_current'], 
            options
        )
        
        # Non-Current Assets
        fixed_assets = self._add_asset_section(
            lines, 'Non-Current Assets',
            ['asset_non_current', 'asset_fixed'],
            options
        )
        
        total_assets = current_assets + fixed_assets
        lines.append(self._make_total_line('Total Assets', total_assets))
        
        # LIABILITIES
        lines.append(self._make_header('LIABILITIES'))
        
        # Current Liabilities
        current_liab = self._add_liability_section(
            lines, 'Current Liabilities',
            ['liability_current', 'liability_payable'],
            options
        )
        
        # Non-Current Liabilities
        long_term_liab = self._add_liability_section(
            lines, 'Non-Current Liabilities',
            ['liability_non_current'],
            options
        )
        
        total_liab = current_liab + long_term_liab
        
        # EQUITY
        equity = self._add_equity_section(lines, options)
        
        total_liab_equity = total_liab + equity
        lines.append(self._make_total_line(
            'Total Liabilities & Equity', total_liab_equity
        ))
        
        return lines
```

### **3.Trial Balance**

```python
# models/trial_balance_report.py
class TrialBalanceReport(models.TransientModel):
    _name = 'tekprowess.trial.balance.report'
    _inherit = 'tekprowess.financial.report.abstract'

    def _get_lines(self, options):
        lines = []
        accounts = self.env['account.account'].search([
            ('company_id', '=', self.env.company.id)
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
                account, options['date_from']
            )
            initial_debit = initial_balance if initial_balance > 0 else 0.0
            initial_credit = -initial_balance if initial_balance < 0 else 0.0
            
            # Period Movement
            period_data = self._compute_account_balance(
                account, options['date_from'], options['date_to']
            )
            period_debit = period_data['debit']
            period_credit = period_data['credit']
            
            # End Balance
            end_balance = initial_balance + period_data['balance']
            end_debit = end_balance if end_balance > 0 else 0.0
            end_credit = -end_balance if end_balance < 0 else 0.0
            
            # Skip if all zeros
            if all(v == 0 for v in [initial_debit, initial_credit, 
                                     period_debit, period_credit,
                                     end_debit, end_credit]):
                continue
            
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'columns': [
                    {'name': self._format_value(initial_debit)},
                    {'name': self._format_value(initial_credit)},
                    {'name': self._format_value(period_debit)},
                    {'name': self._format_value(period_credit)},
                    {'name': self._format_value(end_debit)},
                    {'name': self._format_value(end_credit)},
                ],
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
            'name': 'Total',
            'class': 'total',
            'level': 0,
            'columns': [
                {'name': self._format_value(total_initial_debit)},
                {'name': self._format_value(total_initial_credit)},
                {'name': self._format_value(total_period_debit)},
                {'name': self._format_value(total_period_credit)},
                {'name': self._format_value(total_end_debit)},
                {'name': self._format_value(total_end_credit)},
            ],
        })
        
        return lines

    def _get_columns(self, options):
        return [
            {'name': 'Account'},
            {'name': 'Initial Debit'},
            {'name': 'Initial Credit'},
            {'name': 'Period Debit'},
            {'name': 'Period Credit'},
            {'name': 'End Debit'},
            {'name': 'End Credit'},
        ]
```

### **4. General Ledger**

```python
# models/general_ledger_report.py
class GeneralLedgerReport(models.TransientModel):
    _name = 'tekprowess.general.ledger.report'
    _inherit = 'tekprowess.financial.report.abstract'

    def _get_lines(self, options):
        lines = []
        accounts = self.env['account.account'].search([
            ('company_id', '=', self.env.company.id)
        ], order='code')
        
        for account in accounts:
            # Initial balance
            initial_balance = self._compute_initial_balance(
                account, options['date_from']
            )
            
            # Get moves
            move_lines = self._get_account_move_lines(
                options, accounts=account
            )
            
            if not move_lines and initial_balance == 0:
                continue
            
            # Account header
            lines.append({
                'id': f'account_{account.id}',
                'name': f"{account.code} {account.name}",
                'level': 0,
                'unfoldable': True,
                'unfolded': options.get('unfold_all'),
                'columns': self._format_columns(0, options),
            })
            
            # Initial balance line
            if initial_balance != 0:
                lines.append({
                    'name': 'Initial Balance',
                    'level': 1,
                    'columns': [
                        {'name': ''},
                        {'name': ''},
                        {'name': self._format_value(initial_balance)},
                    ],
                })
            
            # Move lines
            running_balance = initial_balance
            for move_line in move_lines.sorted('date'):
                running_balance += move_line.debit - move_line.credit
                
                lines.append({
                    'id': f'aml_{move_line.id}',
                    'name': move_line.name or move_line.move_id.name,
                    'level': 1,
                    'caret_options': 'account.move.line',
                    'columns': [
                        {'name': move_line.date.strftime('%Y-%m-%d')},
                        {'name': move_line.partner_id.name or ''},
                        {'name': self._format_value(move_line.debit)},
                        {'name': self._format_value(move_line.credit)},
                        {'name': self._format_value(running_balance)},
                    ],
                })
        
        return lines

    def _get_columns(self, options):
        return [
            {'name': 'Date'},
            {'name': 'Partner'},
            {'name': 'Debit'},
            {'name': 'Credit'},
            {'name': 'Balance'},
        ]
```

### **5. Aged Partner Balance (Receivable/Payable)**

```python
# models/aged_partner_report.py
class AgedPartnerReport(models.TransientModel):
    _name = 'tekprowess.aged.partner.report'
    _inherit = 'tekprowess.financial.report.abstract'

    report_type = fields.Selection([
        ('receivable', 'Aged Receivable'),
        ('payable', 'Aged Payable'),
    ], default='receivable')

    def _get_lines(self, options):
        lines = []
        
        # Determine account type
        account_type = 'asset_receivable' if options.get('report_type') == 'receivable' else 'liability_payable'
        
        # Get partners with outstanding balances
        partners = self.env['res.partner'].search([])
        
        as_of_date = fields.Date.from_string(options['date_to'])
        
        for partner in partners:
            # Get unpaid invoices
            invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('move_type', 'in', ['out_invoice', 'out_refund'] if options.get('report_type') == 'receivable' else ['in_invoice', 'in_refund']),
            ])
            
            if not invoices:
                continue
            
            # Age buckets: 0-30, 31-60, 61-90, 91-120, 120+
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
                days_due = (as_of_date - invoice.invoice_date).days
                
                if days_due <= 0:
                    buckets['current'] += amount_due
                elif days_due <= 30:
                    buckets['1_30'] += amount_due
                elif days_due <= 60:
                    buckets['31_60'] += amount_due
                elif  days_due <= 90:
                    buckets['61_90'] += amount_due
                elif days_due <= 120:
                    buckets['91_120'] += amount_due
                else:
                    buckets['older'] += amount_due
            
            total = sum(buckets.values())
            if total == 0:
                continue
            
            lines.append({
                'id': f'partner_{partner.id}',
                'name': partner.name,
                'columns': [
                    {'name': self._format_value(total)},
                    {'name': self._format_value(buckets['current'])},
                    {'name': self._format_value(buckets['1_30'])},
                    {'name': self._format_value(buckets['31_60'])},
                    {'name': self._format_value(buckets['61_90'])},
                    {'name': self._format_value(buckets['91_120'])},
                    {'name': self._format_value(buckets['older'])},
                ],
            })
        
        return lines

    def _get_columns(self, options):
        return [
            {'name': 'Partner'},
            {'name': 'Total'},
            {'name': 'Current'},
            {'name': '1-30 Days'},
            {'name': '31-60 Days'},
            {'name': '61-90 Days'},
            {'name': '91-120 Days'},
            {'name': '120+ Days'},
        ]
```

---

## 🎨 Wizard for User Interface

```python
# wizard/financial_report_wizard.py
from odoo import models, fields, api

class FinancialReportWizard(models.TransientModel):
    _name = 'financial.report.wizard'
    _description = 'Financial Report Wizard'

    report_type = fields.Selection([
        ('profit_loss', 'Profit & Loss'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow'),
        ('trial_balance', 'Trial Balance'),
        ('general_ledger', 'General Ledger'),
        ('partner_ledger', 'Partner Ledger'),
        ('aged_receivable', 'Aged Receivable'),
        ('aged_payable', 'Aged Payable'),
    ], string='Report Type', required=True, default='profit_loss')

    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True, default=fields.Date.context_today)
    
    comparison = fields.Boolean('Enable Comparison')
    comparison_type = fields.Selection([
        ('previous_period', 'Previous Period'),
        ('same_last_year', 'Same Period Last Year'),
    ], string='Compare With')

    all_entries = fields.Boolean('Include Unposted Entries')
    unfold_all = fields.Boolean('Unfold All')
    
    journal_ids = fields.Many2many('account.journal', string='Journals')

    @api.onchange('report_type')
    def _onchange_report_type(self):
        """Set default date range based on report type"""
        today = fields.Date.context_today(self)
        fiscal_dates = self.env.company.compute_fiscalyear_dates(today)
        self.date_from = fiscal_dates['date_from']
        self.date_to = fiscal_dates['date_to']

    def generate_report(self):
        """Generate the selected report"""
        options = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'comparison': self.comparison,
            'comparison_type': self.comparison_type,
            'all_entries': self.all_entries,
            'unfold_all': self.unfold_all,
            'journals': self.journal_ids.ids,
        }

        # Get the appropriate report model
        report_models = {
            'profit_loss': 'tekprowess.profit.loss.report',
            'balance_sheet': 'tekprowess.balance.sheet.report',
            'trial_balance': 'tekprowess.trial.balance.report',
            'general_ledger': 'tekprowess.general.ledger.report',
            'aged_receivable': 'tekprowess.aged.partner.report',
            'aged_payable': 'tekprowess.aged.partner.report',
        }

        report = self.env[report_models[self.report_type]]
        
        # Return action to display report
        return {
            'type': 'ir.actions.act_window',
            'name': dict(self._fields['report_type'].selection)[self.report_type],
            'res_model': report_models[self.report_type],
            'view_mode': 'tree',
            'view_id': False,
            'target': 'current',
            'context': {'report_options': options},
        }

    def export_pdf(self):
        """Export to PDF"""
        # Implementation here
        pass

    def export_xlsx(self):
        """Export to Excel"""
        # Implementation here
        pass
```

---

## 📁 Next Steps

### **To Complete:**

1. **Create remaining report models** following the patterns above
2. **Create XML views** for each report
3. **Add security** (ir.model.access.csv)
4. **Add menu items**
5. **Test each report**

### **Would you like me to:**

1. ✅ Continue creating the remaining report models?
2. ✅ Create the XML views and templates?
3. ✅ Create the complete security file?
4. ✅ Add JavaScript for interactive features?

Let me know which part you'd like me to implement next! 🚀
