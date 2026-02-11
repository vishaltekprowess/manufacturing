# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ManufacturingQualityPoint(models.Model):
    _name = 'manufacturing.quality.point'
    _description = 'Manufacturing Quality Point'
    _order = 'sequence, id'

    name = fields.Char(string='Quality Check', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    product_id = fields.Many2one('product.product', string='Product')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials')
    
    check_type = fields.Selection([
        ('visual', 'Visual Inspection'),
        ('measurement', 'Measurement'),
        ('test', 'Test'),
        ('sampling', 'Sampling'),
    ], string='Check Type', required=True, default='visual')
    
    check_point = fields.Selection([
        ('first', 'First Article'),
        ('production', 'During Production'),
        ('final', 'Final Inspection'),
    ], string='Check Point', required=True, default='final')
    
    mandatory = fields.Boolean(string='Mandatory', default=True)
    
    norm = fields.Char(string='Norm/Standard')
    tolerance_min = fields.Float(string='Minimum Tolerance')
    tolerance_max = fields.Float(string='Maximum Tolerance')
    
    instructions = fields.Text(string='Instructions')
    
    active = fields.Boolean(string='Active', default=True)


class ManufacturingQualityCheck(models.Model):
    _name = 'manufacturing.quality.check'
    _description = 'Manufacturing Quality Check'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Check Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', 
                                    required=True, ondelete='cascade')
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    
    quality_point_id = fields.Many2one('manufacturing.quality.point', 
                                       string='Quality Point')
    
    check_type = fields.Selection([
        ('visual', 'Visual Inspection'),
        ('measurement', 'Measurement'),
        ('test', 'Test'),
        ('sampling', 'Sampling'),
    ], string='Check Type', required=True, default='visual')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', tracking=True)
    
    mandatory = fields.Boolean(string='Mandatory', default=False)
    
    # Check details
    inspector_id = fields.Many2one('res.users', string='Inspector')
    check_date = fields.Datetime(string='Check Date')
    
    norm = fields.Char(string='Norm/Standard')
    tolerance_min = fields.Float(string='Minimum Tolerance')
    tolerance_max = fields.Float(string='Maximum Tolerance')
    measured_value = fields.Float(string='Measured Value')
    
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
    ], string='Result', tracking=True)
    
    notes = fields.Text(string='Notes')
    corrective_action = fields.Text(string='Corrective Action')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    def action_start(self):
        for check in self:
            check.write({
                'state': 'in_progress',
                'inspector_id': self.env.user.id,
            })
    
    def action_pass(self):
        for check in self:
            check.write({
                'state': 'done',
                'result': 'pass',
                'check_date': fields.Datetime.now(),
            })
    
    def action_fail(self):
        for check in self:
            check.write({
                'state': 'failed',
                'result': 'fail',
                'check_date': fields.Datetime.now(),
            })
            # Create quality alert
            self.env['manufacturing.quality.alert'].create({
                'production_id': check.production_id.id,
                'quality_check_id': check.id,
                'product_id': check.product_id.id,
                'name': f'Quality Check Failed: {check.name}',
                'description': check.notes or _('Quality check failed during inspection'),
            })
    
    @api.constrains('measured_value', 'tolerance_min', 'tolerance_max')
    def _check_tolerance(self):
        for check in self:
            if check.check_type == 'measurement' and check.measured_value:
                if check.tolerance_min and check.measured_value < check.tolerance_min:
                    raise ValidationError(_('Measured value is below minimum tolerance.'))
                if check.tolerance_max and check.measured_value > check.tolerance_max:
                    raise ValidationError(_('Measured value is above maximum tolerance.'))
