# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Override priority to support 4 levels instead of 3
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Low'),
            ('2', 'High'),
            ('3', 'Very High'),
        ],
        string='Priority',
        default='0',
        index=True,
        help="Priority for this stock move. Setting a priority will set the same priority on the linked Manufacturing Order."
    )
