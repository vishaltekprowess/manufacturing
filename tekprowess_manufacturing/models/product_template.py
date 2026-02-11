# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Manufacturing specific fields
    manufacturing_type = fields.Selection([
        ('make_to_stock', 'Make to Stock'),
        ('make_to_order', 'Make to Order'),
        ('engineer_to_order', 'Engineer to Order'),
    ], string='Manufacturing Type', default='make_to_stock')
    
    production_time = fields.Float(string='Production Time (Hours)', 
                                    help='Standard time to produce one unit')
    setup_time = fields.Float(string='Setup Time (Minutes)', 
                               help='Time required to setup production')
    
    min_production_qty = fields.Float(string='Minimum Production Quantity', default=1.0)
    max_production_qty = fields.Float(string='Maximum Production Quantity', default=0.0)
    
    quality_point_ids = fields.One2many('manufacturing.quality.point', 'product_tmpl_id', 
                                        string='Quality Points')
    
    require_quality_check = fields.Boolean(string='Require Quality Check', default=False)
    
    scrap_rate = fields.Float(string='Expected Scrap Rate (%)', default=0.0)
    
    alternative_product_ids = fields.Many2many('product.template', 
                                               'product_alternative_rel',
                                               'product_id', 'alternative_id',
                                               string='Alternative Products')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Override for product variant specific fields if needed
    manufacturing_notes = fields.Text(string='Manufacturing Notes')
