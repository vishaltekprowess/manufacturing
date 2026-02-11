# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductionSchedule(models.Model):
    _name = 'manufacturing.production.schedule'
    _description = 'Production Schedule'
    _order = 'planned_date'

    name = fields.Char(string='Schedule Name', required=True)
    
    product_id = fields.Many2one('product.product', string='Product', required=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center')
    
    planned_date = fields.Date(string='Planned Date', required=True)
    planned_quantity = fields.Float(string='Planned Quantity', required=True)
    
    production_ids = fields.One2many('mrp.production', 'schedule_id', 
                                     string='Manufacturing Orders')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    
    notes = fields.Text(string='Notes')


class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production'

    schedule_id = fields.Many2one('manufacturing.production.schedule', 
                                  string='Production Schedule')
