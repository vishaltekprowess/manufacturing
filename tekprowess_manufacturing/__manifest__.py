# -*- coding: utf-8 -*-
{
    'name': "Tekprowess Manufacturing",
    'summary': "Advanced Manufacturing Module with Integration",
    'description': """
        Tekprowess Manufacturing Module
        ================================
        
        This module provides comprehensive manufacturing features including:
        * Integration with Purchase Orders
        * Integration with Sales Orders
        * Manufacturing Order Management
        * Bill of Materials (BoM) Enhancements
        * Work Order Management
        * Quality Control
        * Production Planning
        * Material Requirements Planning (MRP)
        * Manufacturing Analytics
        * Automated Procurement
        * Cost Analysis
        * Production Scheduling
    """,
    'author': "Tekprowess",
    'category': 'Manufacturing',
    'version': '18.0.1.0.0',
    'depends': [
        'base',
        'product',
        'stock',
        'mrp',
        'purchase',
        'sale_management',
        'account',
        'sale_mrp',
        'purchase_mrp',
        'purchase_requisition',        
        'mrp_account',
        'manufacture_process_costing',
        'muk_web_theme',
        'tekprowess_accounting_reports',
    ],
    'data': [
        # Security
        'security/manufacturing_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/manufacturing_sequence.xml',
        'data/quality_check_data.xml',
        
        # Wizards (must be loaded early as they're referenced in views)
        'wizards/mrp_production_wizard_views.xml',
        'wizards/material_requirement_wizard_views.xml',
        'wizards/create_purchase_order_wizard_views.xml',
        
        # Views - Manufacturing Orders
        'views/mrp_production_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_workorder_views.xml',
        
        # Views - Product & Planning
        'views/product_template_views.xml',
        'views/mrp_production_schedule_views.xml',
        
        # Views - Quality Control
        'views/quality_alert_views.xml',
        'views/quality_check_views.xml',
        
        # Views - Integration
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        
        # Reports
        'reports/manufacturing_reports.xml',
        'reports/production_order_report.xml',
        'reports/bom_structure_report.xml',
        'reports/material_consumption_report.xml',
        
        # Menus
        'views/manufacturing_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
