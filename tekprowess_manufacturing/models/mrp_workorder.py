# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    # Additional Fields
    operator_id = fields.Many2one('res.users', string='Operator')
    skill_required = fields.Char(string='Skill Required')
    
    tools_required = fields.Text(string='Tools Required')
    safety_instructions = fields.Text(string='Safety Instructions')
    
    quality_check_count = fields.Integer(string='Quality Checks', 
                                          compute='_compute_quality_check_count')
    
    actual_cost = fields.Float(string='Actual Cost', compute='_compute_actual_cost', store=True)
    
    efficiency = fields.Float(string='Efficiency (%)', compute='_compute_efficiency')
    
    @api.depends('duration', 'workcenter_id.costs_hour')
    def _compute_actual_cost(self):
        for workorder in self:
            workorder.actual_cost = (workorder.duration / 60.0) * workorder.workcenter_id.costs_hour
    
    @api.depends('duration_expected', 'duration')
    def _compute_efficiency(self):
        for workorder in self:
            if workorder.duration > 0:
                workorder.efficiency = (workorder.duration_expected / workorder.duration) * 100
            else:
                workorder.efficiency = 0.0
    
    def _compute_quality_check_count(self):
        for workorder in self:
            workorder.quality_check_count = self.env['manufacturing.quality.check'].search_count([
                ('workorder_id', '=', workorder.id)
            ])
    
    def action_view_quality_checks(self):
        self.ensure_one()
        return {
            'name': _('Quality Checks'),
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.quality.check',
            'view_mode': 'list,form',
            'domain': [('workorder_id', '=', self.id)],
            'context': {'default_workorder_id': self.id, 
                       'default_production_id': self.production_id.id},
        }


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # Additional Fields
    capacity = fields.Float(string='Capacity (Units/Day)', default=100.0)
    efficiency_rate = fields.Float(string='Efficiency Rate (%)', default=100.0)
    
    maintenance_schedule = fields.Text(string='Maintenance Schedule')
    last_maintenance_date = fields.Date(string='Last Maintenance Date')
    next_maintenance_date = fields.Date(string='Next Maintenance Date')
    
    location_id = fields.Many2one('stock.location', string='Stock Location')
    
    skill_requirements = fields.Text(string='Skill Requirements')
