# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaterialRequirement(models.Model):
    _name = 'manufacturing.material.requirement'
    _description = 'Material Requirement Planning'
    _order = 'required_date'

    name = fields.Char(string='Reference', required=True, default='New')
    
    product_id = fields.Many2one('product.product', string='Product', required=True)
    required_quantity = fields.Float(string='Required Quantity', required=True)
    available_quantity = fields.Float(string='Available Quantity', 
                                      compute='_compute_available_quantity')
    shortage_quantity = fields.Float(string='Shortage', 
                                     compute='_compute_shortage')
    
    required_date = fields.Date(string='Required Date', required=True)
    
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('procured', 'Procured'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    
    procurement_type = fields.Selection([
        ('purchase', 'Purchase'),
        ('manufacture', 'Manufacture'),
        ('transfer', 'Transfer'),
    ], string='Procurement Type')
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    
    @api.depends('product_id')
    def _compute_available_quantity(self):
        for req in self:
            req.available_quantity = req.product_id.qty_available
    
    @api.depends('required_quantity', 'available_quantity')
    def _compute_shortage(self):
        for req in self:
            req.shortage_quantity = max(0, req.required_quantity - req.available_quantity)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('manufacturing.material.requirement') or 'New'
        return super(MaterialRequirement, self).create(vals)
