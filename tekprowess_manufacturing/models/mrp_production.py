# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Additional Fields
    production_type = fields.Selection([
        ('standard', 'Standard Production'),
        ('make_to_order', 'Make to Order'),
        ('subcontracting', 'Subcontracting'),
        ('rework', 'Rework'),
    ], string='Production Type', default='standard', required=True)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='0')
    
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', 
                                     compute='_compute_sale_order', store=True)
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                   related='sale_order_id.partner_id', store=True)
    
    production_cost = fields.Float(string='Production Cost', 
                                    compute='_compute_production_cost', store=True)
    material_cost = fields.Float(string='Material Cost', 
                                  compute='_compute_production_cost', store=True)
    labor_cost = fields.Float(string='Labor Cost', 
                               compute='_compute_production_cost', store=True)
    overhead_cost = fields.Float(string='Overhead Cost')
    
    expected_duration = fields.Float(string='Expected Duration (Hours)', 
                                      compute='_compute_expected_duration')
    actual_duration = fields.Float(string='Actual Duration (Hours)', 
                                    compute='_compute_actual_duration')
    
    quality_check_count = fields.Integer(string='Quality Checks', 
                                          compute='_compute_quality_check_count')
    quality_alert_count = fields.Integer(string='Quality Alerts', 
                                          compute='_compute_quality_alert_count')
    
    efficiency = fields.Float(string='Efficiency (%)', 
                               compute='_compute_efficiency')
    
    notes = fields.Text(string='Production Notes')
    special_instructions = fields.Text(string='Special Instructions')
    
    # Scheduling
    planned_start_date = fields.Datetime(string='Planned Start Date')
    planned_end_date = fields.Datetime(string='Planned End Date')
    actual_start_date = fields.Datetime(string='Actual Start Date')
    actual_end_date = fields.Datetime(string='Actual End Date')
    
    # Integration fields
    purchase_order_ids = fields.Many2many('purchase.order', string='Purchase Orders',
                                           compute='_compute_purchase_orders')
    
    @api.depends('move_raw_ids', 'move_raw_ids.created_purchase_line_ids')
    def _compute_purchase_orders(self):
        for production in self:
            purchase_orders = production.move_raw_ids.mapped('created_purchase_line_ids.order_id')
            production.purchase_order_ids = purchase_orders
    
    @api.depends('origin')
    def _compute_sale_order(self):
        for production in self:
            if production.origin:
                sale_order = self.env['sale.order'].search([
                    ('name', '=', production.origin)
                ], limit=1)
                production.sale_order_id = sale_order.id if sale_order else False
            else:
                production.sale_order_id = False
    
    @api.depends('move_raw_ids', 'move_raw_ids.product_uom_qty', 
                 'move_raw_ids.product_id.standard_price')
    def _compute_production_cost(self):
        for production in self:
            material_cost = sum(
                move.product_uom_qty * move.product_id.standard_price 
                for move in production.move_raw_ids
            )
            labor_cost = sum(
                wo.duration / 60.0 * wo.workcenter_id.costs_hour 
                for wo in production.workorder_ids
            )
            production.material_cost = material_cost
            production.labor_cost = labor_cost
            production.production_cost = material_cost + labor_cost + production.overhead_cost
    
    @api.depends('workorder_ids', 'workorder_ids.duration_expected', 'planned_start_date', 'planned_end_date')
    def _compute_expected_duration(self):
        for production in self:
            # Try to compute from work orders first
            duration_from_wo = sum(
                wo.duration_expected / 60.0 for wo in production.workorder_ids
            )
            
            if duration_from_wo:
                production.expected_duration = duration_from_wo
            elif production.planned_start_date and production.planned_end_date:
                # Fallback: compute from planned dates
                delta = production.planned_end_date - production.planned_start_date
                production.expected_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                production.expected_duration = 0.0
    
    @api.depends('workorder_ids', 'workorder_ids.duration', 'actual_start_date', 'actual_end_date')
    def _compute_actual_duration(self):
        for production in self:
            # Try to compute from work orders first
            duration_from_wo = sum(
                wo.duration / 60.0 for wo in production.workorder_ids
            )
            
            if duration_from_wo:
                production.actual_duration = duration_from_wo
            elif production.actual_start_date and production.actual_end_date:
                # Fallback: compute from actual dates
                delta = production.actual_end_date - production.actual_start_date
                production.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                production.actual_duration = 0.0
    
    def _compute_quality_check_count(self):
        for production in self:
            production.quality_check_count = self.env['manufacturing.quality.check'].search_count([
                ('production_id', '=', production.id)
            ])
    
    def _compute_quality_alert_count(self):
        for production in self:
            production.quality_alert_count = self.env['manufacturing.quality.alert'].search_count([
                ('production_id', '=', production.id)
            ])
    
    @api.depends('expected_duration', 'actual_duration')
    def _compute_efficiency(self):
        for production in self:
            if production.actual_duration > 0:
                production.efficiency = (production.expected_duration / production.actual_duration) * 100
            else:
                production.efficiency = 0.0
    
    def action_view_quality_checks(self):
        self.ensure_one()
        return {
            'name': _('Quality Checks'),
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.quality.check',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_check_date': fields.Datetime.now(),
            },
        }
    
    def action_view_quality_alerts(self):
        self.ensure_one()
        return {
            'name': _('Quality Alerts'),
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.quality.alert',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_assigned_to': self.user_id.id,
            },
        }
    
    
    def button_mark_done(self):
        """Override to add quality checks validation"""
        for production in self:
            # Check if all mandatory quality checks are done
            pending_checks = self.env['manufacturing.quality.check'].search([
                ('production_id', '=', production.id),
                ('state', '!=', 'done'),
                ('mandatory', '=', True),
            ])
            if pending_checks:
                raise UserError(_('You cannot finish production with pending mandatory quality checks.'))
            
            # Set actual end date
            production.actual_end_date = fields.Datetime.now()
        
        return super(MrpProduction, self).button_mark_done()
    
    def action_confirm(self):
        """Override to set actual start date"""
        res = super(MrpProduction, self).action_confirm()
        for production in self:
            if not production.actual_start_date:
                production.actual_start_date = fields.Datetime.now()
        return res
    
    @api.model
    def create(self, vals):
        """Auto-create quality checks on production order creation"""
        production = super(MrpProduction, self).create(vals)
        production._create_quality_checks()
        return production
    
    def _create_quality_checks(self):
        """Create quality checks based on product configuration"""
        for production in self:
            quality_points = self.env['manufacturing.quality.point'].search([
                '|',
                ('product_id', '=', production.product_id.id),
                ('product_tmpl_id', '=', production.product_id.product_tmpl_id.id),
            ])
            
            for point in quality_points:
                self.env['manufacturing.quality.check'].create({
                    'production_id': production.id,
                    'quality_point_id': point.id,
                    'product_id': production.product_id.id,
                    'name': point.name,
                    'check_type': point.check_type,
                    'mandatory': point.mandatory,
                })
