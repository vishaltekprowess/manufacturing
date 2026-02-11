# -*- coding: utf-8 -*-
from odoo import models, api


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def _load_menus_blacklist(self):
        """
        Load the list of blacklisted menu items for manufacturing users.
        Manufacturing users will see: Manufacturing, Inventory, Sales, Purchase, and Invoicing.
        All other unrelated menus will be hidden.
        """
        res = set(super()._load_menus_blacklist())
        user = self.env.user
        ref = self.env.ref
        
        # Define manufacturing user groups (non-admin)
        manufacturing_user_groups = [
            'tekprowess_manufacturing.group_manufacturing_user',
            'tekprowess_manufacturing.group_quality_inspector',
            'tekprowess_manufacturing.group_production_planner',
        ]
        
        # Check if user is a manufacturing user but NOT an administrator
        is_manufacturing_user = any(user.has_group(g) for g in manufacturing_user_groups)
        is_admin = user.has_group('tekprowess_manufacturing.group_manufacturing_manager')
        
        # If user is manufacturing user but not admin, hide UNRELATED menus
        if is_manufacturing_user and not is_admin:
            # List of menus to HIDE (only unrelated modules)
            # KEEPING: Manufacturing, Inventory, Sales, Purchase, Invoicing
            menu_xmlids = {
                # Communication & Collaboration
                'mail.menu_root_discuss',
                
                # Contacts (standalone)
                'contacts.menu_contacts',
                
                # CRM
                'crm.crm_menu_root',
                
                # Point of Sale
                'point_of_sale.menu_point_root',
                
                # Project Management
                'project.menu_main_pm',
                
                # Timesheets
                'hr_timesheet.timesheet_menu_root',
                
                # Calendar
                'calendar.mail_menu_calendar',
                
                # Marketing
                'mass_mailing.mass_mailing_menu_root',
                'mass_mailing_sms.mass_mailing_sms_menu_root',
                
                # Surveys
                'survey.menu_surveys',
                
                # Human Resources
                'hr.menu_hr_root',
                'hr_recruitment.menu_hr_recruitment_root',
                'hr_holidays.menu_hr_holidays_root',
                'hr_attendance.menu_hr_attendance_root',
                'hr_appraisal.menu_hr_appraisal_root',
                
                # Fleet Management
                'fleet.menu_root',
                
                # Maintenance (non-manufacturing)
                'maintenance.menu_maintenance_title',
                
                # Website & eCommerce
                'website.menu_website_configuration',
                'website_sale.menu_catalog',
                
                # Live Chat
                'im_livechat.menu_livechat_root',
                
                # IoT
                'iot.iot_menu_root',
                
                # Dashboards
                'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
                
                # Link Tracker
                'utm.menu_link_tracker_root',
                
                # Apps Menu (only admins should install modules)
                'base.menu_management',
                
                # Settings Menu (only admins should configure)
                'base.menu_administration',
            }
            
            # Add each blacklisted menu and all its children
            for xmlid in menu_xmlids:
                menu = ref(xmlid, raise_if_not_found=False)
                if menu:
                    # Get all child menus recursively
                    child_ids = self.search([('id', 'child_of', menu.id)]).ids
                    res.update(child_ids)
        
        return list(res)

    def get_user_roots(self):
        """
        Return all root menu ids visible for the user.
        Manufacturing users will see: Manufacturing, Inventory, Sales, Purchase, Invoicing.
        """
        user = self.env.user
        
        # Define manufacturing user groups (non-admin)
        manufacturing_user_groups = [
            'tekprowess_manufacturing.group_manufacturing_user',
            'tekprowess_manufacturing.group_quality_inspector',
            'tekprowess_manufacturing.group_production_planner',
        ]
        
        # Check if user is a manufacturing user but NOT an administrator
        is_manufacturing_user = any(user.has_group(g) for g in manufacturing_user_groups)
        is_admin = user.has_group('tekprowess_manufacturing.group_manufacturing_manager')
        
        # Get all user root menus normally
        menus = super().get_user_roots()
        
        # If manufacturing user but not admin, filter to show only manufacturing-related menus
        if is_manufacturing_user and not is_admin:
            # Hide unrelated menus, KEEP manufacturing-related ones
            excluded_xmlids = [
                'mail.menu_root_discuss',
                'contacts.menu_contacts',
                'crm.crm_menu_root',
                'point_of_sale.menu_point_root',
                'project.menu_main_pm',
                'hr_timesheet.timesheet_menu_root',
                'calendar.mail_menu_calendar',
                'mass_mailing.mass_mailing_menu_root',
                'mass_mailing_sms.mass_mailing_sms_menu_root',
                'survey.menu_surveys',
                'hr.menu_hr_root',
                'hr_recruitment.menu_hr_recruitment_root',
                'hr_holidays.menu_hr_holidays_root',
                'hr_attendance.menu_hr_attendance_root',
                'hr_appraisal.menu_hr_appraisal_root',
                'fleet.menu_root',
                'maintenance.menu_maintenance_title',
                'website.menu_website_configuration',
                'website_sale.menu_catalog',
                'im_livechat.menu_livechat_root',
                'iot.iot_menu_root',
                'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
                'utm.menu_link_tracker_root',
                'base.menu_management',  # Apps
                'base.menu_administration',  # Settings
            ]
            
            excluded_ids = []
            for xmlid in excluded_xmlids:
                menu_ref = self.env.ref(xmlid, raise_if_not_found=False)
                if menu_ref:
                    excluded_ids.append(menu_ref.id)
            
            # Filter out excluded menus
            menus = menus.filtered(lambda m: m.id not in excluded_ids)
        
        return menus
