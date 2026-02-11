# Tekprowess Manufacturing Module

## Overview

The Tekprowess Manufacturing module is a comprehensive manufacturing solution for Odoo 18 that seamlessly integrates with standard Odoo community modules including Purchase, Sales, Invoice, and Manufacturing (MRP).

## Features

### 1. Enhanced Manufacturing Orders
- **Production Types**: Standard, Make-to-Order, Subcontracting, Rework
- **Priority Management**: Set priorities for production orders
- **Cost Analysis**: Automatic calculation of material cost, labor cost, and overhead
- **Efficiency Tracking**: Monitor expected vs actual duration
- **Customer Integration**: Link production orders directly to sales orders and customers
- **Scheduling**: Plan and track start/end dates

### 2. Advanced Bill of Materials (BoM)
- **BoM Categories**: Standard, Custom, Engineering, Prototype
- **Revision Control**: Track BoM versions and revisions
- **Cost Estimation**: Automatic material cost calculation
- **Approval Workflow**: Approve BoMs before production
- **Scrap Management**: Define expected scrap percentages
- **Critical Components**: Mark critical components in BoM
- **Alternative Products**: Define alternative products for components

### 3. Quality Management
- **Quality Points**: Define quality checkpoints for products and BoMs
- **Quality Checks**: Automated creation of quality checks during production
- **Quality Types**: Visual inspection, Measurement, Test, Sampling
- **Quality Alerts**: Automatic alert generation for failed checks
- **Root Cause Analysis**: Track and document quality issues
- **Corrective Actions**: Record corrective and preventive actions

### 4. Enhanced Work Orders
- **Operator Assignment**: Assign operators to work orders
- **Skill Tracking**: Define required skills for operations
- **Safety Instructions**: Document safety requirements
- **Tools Required**: List tools needed for each operation
- **Performance Metrics**: Track efficiency and actual costs

### 5. Work Center Management
- **Capacity Planning**: Define work center capacity
- **Efficiency Rates**: Track work center efficiency
- **Maintenance Scheduling**: Plan and track maintenance
- **Skills Requirements**: Document required skills
- **Location Management**: Link work centers to stock locations

### 6. Production Planning
- **Production Schedule**: Calendar-based production planning
- **Material Requirements Planning (MRP)**: Generate material requirements from sales and production orders
- **Shortage Analysis**: Identify material shortages
- **Procurement Planning**: Automatic procurement type suggestion

### 7. Sales Order Integration
- **Manufacturing Status**: Track manufacturing status on sales orders
- **Automatic MO Creation**: Create manufacturing orders directly from sales orders
- **Customer Visibility**: View customer information on production orders
- **Manufacturing Orders Link**: Easy navigation between sales and manufacturing

### 8. Purchase Order Integration
- **Manufacturing Link**: View related manufacturing orders from purchase orders
- **Material Tracking**: Track which materials are for which production orders
- **Procurement Integration**: Link purchase orders to material requirements

### 9. Product Configuration
- **Manufacturing Types**: Make-to-Stock, Make-to-Order, Engineer-to-Order
- **Production Time**: Define standard production times
- **Setup Time**: Track setup requirements
- **Production Limits**: Set minimum and maximum production quantities
- **Quality Requirements**: Enable quality checks per product
- **Alternative Products**: Define product alternatives

### 10. Reporting
- **Production Order Report**: Comprehensive production order documentation
- **BoM Structure Report**: Detailed bill of materials with costing
- **Material Consumption Analysis**: Track material usage

## Installation

1. Copy the `tekprowess_manufacturing` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Tekprowess Manufacturing" module

## Dependencies

This module requires the following Odoo modules:
- base
- product
- stock
- mrp (Manufacturing)
- purchase
- sale_management
- account
- sale_mrp
- purchase_mrp
- mrp_account

## Configuration

### Initial Setup

1. **Quality Points**: Configure quality checkpoints
   - Navigate to: Manufacturing > Quality > Quality Points
   - Create quality points for products or BoMs

2. **Work Centers**: Enhance work center configuration
   - Navigate to: Manufacturing > Configuration > Work Centers
   - Set capacity, efficiency rates, and maintenance schedules

3. **Products**: Configure manufacturing settings
   - Open any product form
   - Go to the "Manufacturing" tab
   - Set manufacturing type, production times, and quality requirements

4. **Bill of Materials**: Create and approve BoMs
   - Navigate to: Manufacturing > Products > Bills of Materials
   - Set BoM category, revision, and approve when ready

### User Groups

The module adds the following security groups:
- **Manufacturing Manager**: Full access to all manufacturing features
- **Manufacturing User**: Standard manufacturing operations
- **Quality Inspector**: Access to quality checks and alerts
- **Production Planner**: Access to scheduling and material planning

## Usage

### Creating a Manufacturing Order

**Method 1: From Sales Order**
1. Create a sales order with products that have a BoM
2. Confirm the sales order
3. Click "Create MO" button
4. Manufacturing orders are automatically created

**Method 2: Direct Creation**
1. Go to: Manufacturing > Operations > Create Manufacturing Order
2. Fill in the wizard with product, quantity, and other details
3. Click "Create"

**Method 3: Traditional**
1. Navigate to: Manufacturing > Operations > Manufacturing Orders
2. Click "Create"
3. Fill in the form and confirm

### Quality Management Workflow

1. **Setup Quality Points**
   - Define what to check, when to check, and acceptance criteria
   
2. **Automatic Check Creation**
   - Quality checks are automatically created when manufacturing orders are confirmed
   
3. **Perform Checks**
   - Open the quality check
   - Click "Start" to begin inspection
   - Record measurements and observations
   - Click "Pass" or "Fail"
   
4. **Handle Failures**
   - Failed checks automatically create quality alerts
   - Assign alerts to team members
   - Document root cause and corrective actions
   - Resolve and close alerts

### Material Requirements Planning

1. Navigate to: Manufacturing > Planning > Generate MRP
2. Set date range and filters
3. Click "Generate"
4. Review material requirements
5. Create purchase orders for shortages

### Production Scheduling

1. Navigate to: Manufacturing > Planning > Production Schedule
2. Create schedule entries for planned production
3. View in calendar format
4. Create manufacturing orders from schedules

## Integration with Other Modules

### Sales Module
- View manufacturing orders from sales orders
- Track manufacturing status
- Automatic MO creation from confirmed sales

### Purchase Module
- View related manufacturing orders
- Track materials purchased for production
- Link purchase orders to MRP

### Inventory Module
- Full integration with stock moves
- Component reservation and consumption
- Finished product receipt

### Accounting Module
- Production cost tracking
- Material and labor cost calculation
- Work center cost analysis

## Technical Information

### Models

- `mrp.production` (inherited): Enhanced manufacturing orders
- `mrp.bom` (inherited): Enhanced bill of materials
- `mrp.workorder` (inherited): Enhanced work orders
- `mrp.workcenter` (inherited): Enhanced work centers
- `product.template` (inherited): Manufacturing settings
- `sale.order` (inherited): Manufacturing integration
- `purchase.order` (inherited): Manufacturing integration
- `manufacturing.quality.point`: Quality checkpoint definitions
- `manufacturing.quality.check`: Quality inspection records
- `manufacturing.quality.alert`: Quality issue tracking
- `manufacturing.production.schedule`: Production planning
- `manufacturing.material.requirement`: MRP records

### Views

All major models have enhanced forms, trees, and search views with manufacturing-specific fields and functionality.

### Reports

- Production Order Report (PDF)
- BoM Structure Report (PDF)
- Material Consumption Analysis (Pivot/Graph)

## Support

For support and questions about this module, please contact Tekprowess.

## Version

- **Module Version**: 18.0.1.0.0
- **Odoo Version**: 18.0
- **License**: LGPL-3

## Author

Tekprowess

## Changelog

### Version 1.0.0
- Initial release
- Manufacturing order enhancements
- Quality management system
- Production planning
- Integration with sales and purchase
- Comprehensive reporting
