/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

/**
 * Tekprowess Manufacturing Dashboard
 * Shows Manufacturing / Sales / Purchase section based on the `dashboard_section`
 * context passed by the client action.
 */
export class ManufacturingDashboard extends Component {
    static template = "tekprowess_manufacturing.ManufacturingDashboard";
    static components = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        // Determine which section to show from the action context
        const ctx = this.props.action?.context || {};
        this.section = ctx.dashboard_section || "manufacturing"; // 'manufacturing' | 'sales' | 'purchase'

        this.chartRef = useRef("mainChart");
        this._chart = null;
        this._chartJsLoaded = false;
        this._chartsRendered = false;

        this.state = useState({
            loading: true,
            data: {},
        });

        onWillStart(async () => {
            await this._loadChartJs();
            await this._loadData();
        });

        onMounted(() => {
            this._renderChart();
        });

        onPatched(() => {
            if (!this.state.loading && !this._chartsRendered) {
                this._chartsRendered = true;
                this._renderChart();
            }
        });

        onWillUnmount(() => {
            if (this._chart) { this._chart.destroy(); this._chart = null; }
        });
    }

    // -------------------------------------------------------------------------
    // Data loading
    // -------------------------------------------------------------------------

    async _loadChartJs() {
        if (window.Chart) { this._chartJsLoaded = true; return; }
        await new Promise((resolve) => {
            const s = document.createElement("script");
            s.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js";
            s.onload = () => { this._chartJsLoaded = true; resolve(); };
            s.onerror = () => resolve();
            document.head.appendChild(s);
        });
    }

    async _loadData() {
        this.state.loading = true;
        const methodMap = {
            manufacturing: "get_manufacturing_data",
            sales: "get_sales_data",
            purchase: "get_purchase_data",
        };
        const method = methodMap[this.section] || "get_manufacturing_data";
        try {
            const result = await this.orm.call(
                "tekprowess.manufacturing.dashboard",
                method,
                [],
                {}
            );
            this.state.data = result;
        } catch (e) {
            console.error("Dashboard load error:", e);
        } finally {
            this.state.loading = false;
        }
    }

    async refresh() {
        if (this._chart) { this._chart.destroy(); this._chart = null; }
        this._chartsRendered = false;
        await this._loadData();
    }

    // -------------------------------------------------------------------------
    // Chart rendering — one chart per section
    // -------------------------------------------------------------------------

    _renderChart() {
        if (this.state.loading) return;
        const Chart = window.Chart;
        if (!Chart) return;
        const canvas = this.chartRef.el;
        if (!canvas) return;
        if (this._chart) { this._chart.destroy(); this._chart = null; }

        const d = this.state.data;

        if (this.section === "manufacturing") {
            this._chart = new Chart(canvas, {
                type: "bar",
                data: {
                    labels: d.chart_labels || [],
                    datasets: [
                        {
                            label: "Confirmed",
                            data: d.chart_confirmed || [],
                            backgroundColor: "rgba(135, 90, 123, 0.80)",
                            borderRadius: 4,
                            categoryPercentage: 0.7,
                        },
                        {
                            label: "Done",
                            data: d.chart_done || [],
                            backgroundColor: "rgba(135, 90, 123, 0.25)",
                            borderRadius: 4,
                            categoryPercentage: 0.7,
                        },
                    ],
                },
                options: this._barOptions(),
            });

        } else if (this.section === "sales") {
            this._chart = new Chart(canvas, {
                type: "bar",
                data: {
                    labels: d.chart_labels || [],
                    datasets: [
                        {
                            label: "Amount",
                            data: d.chart_amount || [],
                            backgroundColor: "rgba(71, 160, 198, 0.7)",
                            borderRadius: 4,
                            categoryPercentage: 0.7,
                            yAxisID: "y",
                        },
                        {
                            label: "Orders",
                            data: d.chart_orders || [],
                            type: "line",
                            borderColor: "rgba(39, 174, 96, 0.9)",
                            backgroundColor: "rgba(39, 174, 96, 0.1)",
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3,
                            yAxisID: "y1",
                        },
                    ],
                },
                options: this._dualAxisOptions(),
            });

        } else if (this.section === "purchase") {
            this._chart = new Chart(canvas, {
                type: "bar",
                data: {
                    labels: d.chart_labels || [],
                    datasets: [
                        {
                            label: "Amount",
                            data: d.chart_amount || [],
                            backgroundColor: "rgba(230, 126, 34, 0.7)",
                            borderRadius: 4,
                            categoryPercentage: 0.7,
                            yAxisID: "y",
                        },
                        {
                            label: "Orders",
                            data: d.chart_orders || [],
                            type: "line",
                            borderColor: "rgba(231, 76, 60, 0.9)",
                            backgroundColor: "rgba(231, 76, 60, 0.1)",
                            fill: true,
                            tension: 0.4,
                            pointRadius: 3,
                            yAxisID: "y1",
                        },
                    ],
                },
                options: this._dualAxisOptions(),
            });
        }
    }

    _barOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: "bottom", labels: { boxWidth: 10, font: { size: 10 }, padding: 8 } },
                tooltip: { mode: "index", intersect: false },
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, color: "#6c757d" } },
                y: { beginAtZero: true, ticks: { font: { size: 10 }, precision: 0, color: "#6c757d" }, grid: { color: "rgba(0,0,0,0.04)" } },
            },
        };
    }

    _dualAxisOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: { display: true, position: "bottom", labels: { boxWidth: 10, font: { size: 10 }, padding: 8 } },
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 }, color: "#6c757d" } },
                y: { beginAtZero: true, position: "left", ticks: { font: { size: 10 }, color: "#6c757d" }, grid: { color: "rgba(0,0,0,0.04)" } },
                y1: { beginAtZero: true, position: "right", ticks: { font: { size: 10 }, precision: 0, color: "#6c757d" }, grid: { drawOnChartArea: false } },
            },
        };
    }

    // -------------------------------------------------------------------------
    // Navigation helpers
    // -------------------------------------------------------------------------

    _open(model, domain, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }

    // Manufacturing
    onClickMfgAll() { this._open("mrp.production", [], "Manufacturing Orders"); }
    onClickMfgDraft() { this._open("mrp.production", [["state", "=", "draft"]], "Draft Orders"); }
    onClickMfgConfirmed() { this._open("mrp.production", [["state", "=", "confirmed"]], "Confirmed Orders"); }
    onClickMfgProgress() { this._open("mrp.production", [["state", "in", ["progress", "to_close"]]], "In Progress"); }
    onClickMfgDone() { this._open("mrp.production", [["state", "=", "done"]], "Done Orders"); }

    // Sales
    onClickSaleAll() { this._open("sale.order", [], "Sales Orders"); }
    onClickSaleQuotation() { this._open("sale.order", [["state", "=", "draft"]], "Quotations"); }
    onClickSaleSent() { this._open("sale.order", [["state", "=", "sent"]], "Sent Quotations"); }
    onClickSaleConfirmed() { this._open("sale.order", [["state", "=", "sale"]], "Confirmed Orders"); }
    onClickSaleDone() { this._open("sale.order", [["state", "=", "done"]], "Locked Orders"); }
    onClickSaleToInvoice() { this._open("sale.order", [["state", "in", ["sale", "done"]], ["invoice_status", "=", "to invoice"]], "To Invoice"); }

    // Purchase
    onClickPurchaseAll() { this._open("purchase.order", [], "Purchase Orders"); }
    onClickPurchaseDraft() { this._open("purchase.order", [["state", "=", "draft"]], "Draft RFQ"); }
    onClickPurchaseSent() { this._open("purchase.order", [["state", "=", "sent"]], "Sent RFQ"); }
    onClickPurchaseConfirmed() { this._open("purchase.order", [["state", "=", "purchase"]], "Confirmed Orders"); }
    onClickPurchaseDone() { this._open("purchase.order", [["state", "=", "done"]], "Done Orders"); }
    onClickPurchaseToBill() { this._open("purchase.order", [["state", "in", ["purchase", "done"]], ["invoice_status", "=", "to invoice"]], "To Bill"); }

    // Open individual records
    openMfgOrder(id) { this.action.doAction({ type: "ir.actions.act_window", res_model: "mrp.production", res_id: id, views: [[false, "form"]], target: "current" }); }
    openSaleOrder(id) { this.action.doAction({ type: "ir.actions.act_window", res_model: "sale.order", res_id: id, views: [[false, "form"]], target: "current" }); }
    openPurchaseOrder(id) { this.action.doAction({ type: "ir.actions.act_window", res_model: "purchase.order", res_id: id, views: [[false, "form"]], target: "current" }); }

    // Format
    fmt(amount, symbol) {
        if (!amount) return (symbol || "$") + " 0.00";
        return (symbol || "$") + " " + new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(amount);
    }
}

registry.category("actions").add("manufacturing_dashboard", ManufacturingDashboard);
