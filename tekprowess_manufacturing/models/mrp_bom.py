# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Additional Fields
    bom_category = fields.Selection([
        ('standard', 'Standard'),
        ('custom', 'Custom'),
        ('engineering', 'Engineering'),
        ('prototype', 'Prototype'),
    ], string='BoM Category', default='standard')
    
    revision = fields.Char(string='Revision', default='1.0')
    revision_date = fields.Date(string='Revision Date', default=fields.Date.today)
    
    estimated_cost = fields.Float(string='Estimated Cost', 
                                   compute='_compute_estimated_cost', store=True)
    material_cost = fields.Float(string='Material Cost', 
                                  compute='_compute_estimated_cost', store=True)
    
    lead_time = fields.Float(string='Lead Time (Days)', 
                              help='Expected time to complete production')
    
    scrap_percentage = fields.Float(string='Scrap Percentage (%)', default=0.0)
    
    approved = fields.Boolean(string='Approved', default=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    
    notes = fields.Text(string='Technical Notes')
    
    # Quality related
    quality_point_ids = fields.One2many('manufacturing.quality.point', 'bom_id', 
                                        string='Quality Points')
    quality_point_count = fields.Integer(string='Quality Points', 
                                          compute='_compute_quality_point_count')
    
    @api.depends('bom_line_ids', 'bom_line_ids.product_qty', 
                 'bom_line_ids.product_id.standard_price')
    def _compute_estimated_cost(self):
        for bom in self:
            material_cost = sum(
                line.product_qty * line.product_id.standard_price 
                for line in bom.bom_line_ids
            )
            bom.material_cost = material_cost
            bom.estimated_cost = material_cost * (1 + bom.scrap_percentage / 100.0)
    
    @api.depends('quality_point_ids')
    def _compute_quality_point_count(self):
        for bom in self:
            bom.quality_point_count = len(bom.quality_point_ids)
    
    def action_approve(self):
        """Approve the Bill of Materials"""
        for bom in self:
            bom.write({
                'approved': True,
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
        return True
    
    def action_revise(self):
        """Create a new revision of the BoM"""
        self.ensure_one()
        # Parse current revision and increment
        try:
            major, minor = self.revision.split('.')
            new_revision = f"{major}.{int(minor) + 1}"
        except:
            new_revision = f"{self.revision}.1"
        
        new_bom = self.copy({
            'revision': new_revision,
            'revision_date': fields.Date.today(),
            'approved': False,
            'approved_by': False,
            'approval_date': False,
        })
        
        return {
            'name': _('New BoM Revision'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'form',
            'res_id': new_bom.id,
            'target': 'current',
        }
    
    def action_view_quality_points(self):
        self.ensure_one()
        return {
            'name': _('Quality Points'),
            'type': 'ir.actions.act_window',
            'res_model': 'manufacturing.quality.point',
            'view_mode': 'list,form',
            'domain': [('bom_id', '=', self.id)],
            'context': {'default_bom_id': self.id, 
                       'default_product_tmpl_id': self.product_tmpl_id.id},
        }
    
    @api.constrains('scrap_percentage')
    def _check_scrap_percentage(self):
        for bom in self:
            if bom.scrap_percentage < 0 or bom.scrap_percentage > 100:
                raise ValidationError(_('Scrap percentage must be between 0 and 100.'))


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    # Additional Fields
    is_critical = fields.Boolean(string='Critical Component', 
                                  help='Mark if this component is critical for production')
    alternative_product_ids = fields.Many2many('product.product', 
                                               string='Alternative Products',
                                               help='Alternative products that can be used')
    notes = fields.Text(string='Component Notes')
    lead_time = fields.Integer(string='Lead Time (Days)', 
                               related='product_id.seller_ids.delay', readonly=True)
