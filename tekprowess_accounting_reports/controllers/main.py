# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, content_disposition
import json


class FinancialReportController(http.Controller):

    @http.route('/tekprowess_accounting_reports/export/xlsx', type='http', auth='user')
    def download_xlsx(self, model, options, output_format, token='dummy', **kwargs):
        """
        Download financial report as XLSX
        """
        options = json.loads(options)
        report_obj = request.env[model].new({})
        
        # Get report content
        content = report_obj.get_xlsx(options)
        
        # Determine filename
        report_name = report_obj._get_report_name().lower().replace(' ', '_')
        filename = f"{report_name}.xlsx"
        
        response = request.make_response(
            content,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )
        response.set_cookie('fileToken', token)
        return response

    @http.route('/tekprowess_accounting_reports/export/pdf', type='http', auth='user')
    def download_pdf(self, model, options, output_format, token='dummy', **kwargs):
        """
        Download financial report as PDF
        """
        options = json.loads(options)
        # We need to create a record to call the report method, but since it's transient/abstract 
        # and we need to pass data, we might need a different approach or just instantiate
        # However, for QWeb report generation, we often need an ID or list of IDs.
        # But here we are generating based on options.
        
        report_obj = request.env[model].new({})
        content = report_obj.get_pdf(options)
        
        # Determine filename
        report_name = report_obj._get_report_name().lower().replace(' ', '_')
        filename = f"{report_name}.pdf"

        response = request.make_response(
            content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )
        response.set_cookie('fileToken', token)
        return response
