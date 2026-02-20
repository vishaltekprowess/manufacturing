{
    'name': 'Purchase Order Preview',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Adds a Preview button to Purchase Orders',
    'description': """
        This module adds a "Preview" button to the Purchase Order form view,
        similar to the one in Sale Orders and Invoices, allowing users to quickly
        view the portal representation of the document.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['purchase', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_preview_wizard_views.xml',
        'views/purchase_order_views.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
