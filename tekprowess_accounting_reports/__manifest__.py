# -*- coding: utf-8 -*-
{
    'name': 'Tekprowess Accounting Reports',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Financial Reports for Odoo Community Edition',
    'description': """
Comprehensive Accounting Reports for Community Edition
=======================================================

This module provides enterprise-like financial reporting capabilities 
for Odoo Community Edition, including:

* Profit & Loss Statement
* Balance Sheet
* Cash Flow Statement
* Trial Balance
* General Ledger
* Partner Ledger
*Aged Receivable/Payable
* Tax Reports

All reports support:
- PDF and Excel export
- Date filtering and comparison
- Multi-company support
- Drill-down capabilities
    """,
    'author': 'Tekprowess',
    'website': 'https://www.tekprowess.com',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_templates.xml',
        'views/financial_report_wizard_views.xml',
        'views/menuitems.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tekprowess_accounting_reports/static/src/js/**/*',
            'tekprowess_accounting_reports/static/src/css/**/*',
            'tekprowess_accounting_reports/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
