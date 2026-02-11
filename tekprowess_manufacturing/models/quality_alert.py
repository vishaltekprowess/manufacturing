# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ManufacturingQualityAlert(models.Model):
    _name = 'manufacturing.quality.alert'
    _description = 'Manufacturing Quality Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Alert Title', required=True, tracking=True)
    
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', 
                                    required=True, ondelete='cascade')
    quality_check_id = fields.Many2one('manufacturing.quality.check', string='Quality Check')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    
    alert_type = fields.Selection([
        ('quality', 'Quality Issue'),
        ('defect', 'Defect'),
        ('rework', 'Rework Required'),
        ('scrap', 'Scrap'),
    ], string='Alert Type', default='quality', required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Critical'),
    ], string='Priority', default='0', tracking=True)
    
    state = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ], string='Status', default='open', tracking=True)
    
    description = fields.Text(string='Description', required=True)
    root_cause = fields.Text(string='Root Cause Analysis')
    corrective_action = fields.Text(string='Corrective Action')
    preventive_action = fields.Text(string='Preventive Action')
    
    reported_by = fields.Many2one('res.users', string='Reported By', 
                                  default=lambda self: self.env.user, required=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    
    reported_date = fields.Datetime(string='Reported Date', 
                                    default=fields.Datetime.now, required=True)
    resolved_date = fields.Datetime(string='Resolved Date')
    
    affected_quantity = fields.Float(string='Affected Quantity')
    
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    
    def action_assign_to_me(self):
        self.assigned_to = self.env.user
    
    def action_in_progress(self):
        self.state = 'in_progress'
    
    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now(),
        })
    
    def action_close(self):
        self.state = 'closed'
