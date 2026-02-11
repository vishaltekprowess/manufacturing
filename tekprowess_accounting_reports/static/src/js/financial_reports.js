/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Financial Reports Controller
 * Handles the display and interaction of financial reports
 */
export class FinancialReportController extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            lines: [],
            columns: [],
            options: {},
            loading: false,
            reportName: "",
        });

        onWillStart(async () => {
            await this.loadReport();
        });
    }

    /**
     * Load report data
     */
    async loadReport() {
        this.state.loading = true;
        try {
            const context = this.props.action.context || {};
            const options = context.report_options || {};

            // Get report data from model
            const reportModel = this.props.action.res_model;
            const result = await this.orm.call(
                reportModel,
                'get_report_data',
                [],
                { options }
            );

            this.state.lines = result.lines || [];
            this.state.columns = result.columns || [];
            this.state.reportName = result.report_name || "";
            this.state.options = options;
        } catch (error) {
            console.error("Error loading report:", error);
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Toggle unfold/fold for a line
     */
    toggleUnfold(lineId) {
        const line = this.state.lines.find(l => l.id === lineId);
        if (line && line.unfoldable) {
            line.unfolded = !line.unfolded;
        }
    }

    /**
     * Export report to Excel
     */
    async exportToExcel() {
        try {
            const reportModel = this.props.action.res_model;
            const options = JSON.stringify(this.state.options);
            const url = `/tekprowess_accounting_reports/export/xlsx?model=${reportModel}&options=${encodeURIComponent(options)}&output_format=xlsx`;

            await this.action.doAction({
                type: 'ir.actions.act_url',
                url: url,
            });
        } catch (error) {
            console.error("Error exporting to Excel:", error);
        }
    }

    /**
     * Export report to PDF
     */
    async exportToPDF() {
        try {
            const reportModel = this.props.action.res_model;
            const options = JSON.stringify(this.state.options);
            const url = `/tekprowess_accounting_reports/export/pdf?model=${reportModel}&options=${encodeURIComponent(options)}&output_format=pdf`;

            await this.action.doAction({
                type: 'ir.actions.act_url',
                url: url,
            });
        } catch (error) {
            console.error("Error exporting to PDF:", error);
        }
    }

    /**
     * Drill down into a line (open related records)
     */
    async drillDown(line) {
        if (!line.caret_options) {
            return;
        }

        try {
            const reportModel = this.props.action.res_model;
            const action = await this.orm.call(
                reportModel,
                'action_open_line',
                [line.id],
                { options: this.state.options }
            );

            if (action) {
                this.action.doAction(action);
            }
        } catch (error) {
            console.error("Error drilling down:", error);
        }
    }

    /**
     * Get CSS class for a line based on its level and type
     */
    getLineClass(line) {
        const classes = [];

        if (line.level !== undefined) {
            classes.push(`o_account_reports_level${line.level}`);
        }

        if (line.class) {
            classes.push(line.class);
        }

        if (line.unfoldable) {
            classes.push('o_account_reports_unfoldable');
            if (line.unfolded) {
                classes.push('o_account_reports_unfolded');
            }
        }

        return classes.join(' ');
    }

    /**
     * Check if a line should be displayed (based on parent folding)
     */
    isLineVisible(line, index) {
        if (!line.parent_id) {
            return true;
        }

        // Find parent line
        const parentLine = this.state.lines.find(l => l.id === line.parent_id);
        if (!parentLine) {
            return true;
        }

        // Check if parent is unfolded
        return parentLine.unfolded === true;
    }
}

FinancialReportController.template = "tekprowess_accounting_reports.FinancialReportView";
FinancialReportController.components = { Layout };

// Register the controller
registry.category("actions").add("financial_report", FinancialReportController);

/**
 * Utility functions for financial reports
 */
export const FinancialReportUtils = {
    /**
     * Format a monetary value
     */
    formatMonetary(value, currency = '₹') {
        if (value === null || value === undefined) {
            return '-';
        }

        const formatted = new Intl.NumberFormat('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(Math.abs(value));

        return value < 0 ? `(${currency}${formatted})` : `${currency}${formatted}`;
    },

    /**
     * Format a percentage value
     */
    formatPercentage(value) {
        if (value === null || value === undefined) {
            return '-';
        }

        return `${value.toFixed(2)}%`;
    },

    /**
     * Parse column name to determine if it's numeric
     */
    isNumericColumn(columnName) {
        const numericKeywords = ['balance', 'debit', 'credit', 'amount', 'total', 'value'];
        const lowerName = columnName.toLowerCase();
        return numericKeywords.some(keyword => lowerName.includes(keyword));
    },
};
