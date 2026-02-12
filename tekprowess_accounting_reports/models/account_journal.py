from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def action_open_reconcile(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tekprowess_accounting_reports.action_bank_statement_line_list')
        action['domain'] = [('journal_id', '=', self.id), ('is_reconciled', '=', False)]
        action['context'] = {'default_journal_id': self.id, 'search_default_journal_id': self.id}
        return action

    def action_open_to_check(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tekprowess_accounting_reports.action_bank_statement_line_list')
        action['domain'] = [('journal_id', '=', self.id), ('is_reconciled', '=', False)] # Approximation for "to check"
        action['context'] = {'default_journal_id': self.id, 'search_default_journal_id': self.id}
        return action

    def action_open_bank_transactions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tekprowess_accounting_reports.action_bank_statement_line_list')
        action['domain'] = [('journal_id', '=', self.id)]
        action['context'] = {'default_journal_id': self.id, 'search_default_journal_id': self.id}
        return action

    def action_open_reconcile_statement(self):
        stmt_id = self.env.context.get('statement_id')
        action = self.env['ir.actions.act_window']._for_xml_id('tekprowess_accounting_reports.action_bank_statement_line_list')
        if stmt_id:
             action['domain'] = [('statement_id', '=', stmt_id)]
        return action
