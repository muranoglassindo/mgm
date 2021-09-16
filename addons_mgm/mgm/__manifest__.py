# -*- coding: utf-8 -*-
{
    'name': "mgm",

    'summary': """
        ERP Murano Glassindo Makmur""",

    'description': """
        Long description of module's purpose
        ERP untuk proses bisnis PT. Murano Glassindo Makmur, terdapat beberapa modul, yaitu:
        Discuss, Contacts, Sales, Legal, Purchase, Inventory, Manufacturing serta Accounting.
        Persiapan sebelum penggunaan sistem ERP:
        - Settings
        
            1. Sales:
            - uncentang online signature
            - centang variant, UoM, Discount, product configuration, Margin, Lock Confirmed, Customer Address.
            
            2. Purchase:
            - Centang Lock Confirmed Orders
            - Centang Bill Control > Ordered Quantities
            
            3. Inventory:
            - Centang Lots/Serial Number, display on Deivery Slip
            
            4. Manufacturing
            - Centang WO
            - untuk Work Center Finished Goods harus "Finished Goods"
        
        - Variant Product
            - attribut variant harus "Routing" dan "Ketebalan"
            - buat UoM M2 dan M1
        
        - Ganti Format Tanggal agar Tangal/Bulan/Tahun
            - Settings > Translations > Languages > English : date format > %d/%m/%Y
            
        - Ganti setting waktu user jadi Asia/Jakarta
        
        - User Director code nya harus DIR (berfungsi untuk ttd invoice)
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.2.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale_management',
        'contacts',
        'legal',
        'stock',
        'sale_margin',
        'purchase',
        'mrp',
        'hr_expense',
        'l10n_id',
        'ks_binary_file_preview',
        'om_account_accountant',
        'odoo_report_xlsx',
        'tgl_format_number',
        'deltatech_mrp_edit_comp',
    ],

    # always loaded
    'data': [
        'security/mgm_security.xml',
        
        'security/ir.model.access.csv',
    
        'data/product_mgm.xml',
        'data/payment_term.xml',
        'data/increment_number.xml',
        
        'reports/sale_report_template.xml',
        'reports/sale_report_external_template.xml',
        'reports/sale_report.xml',
        'reports/stock_report_views.xml',
        'reports/stock_report_template.xml',
        'reports/mrp_report_view.xml',
        'reports/mrp_spk_report_template.xml',
        'reports/invoice_report_view.xml',
        'reports/invoice_report_template.xml',
        'reports/mrp_barcode.xml',
        'reports/purchase_order_report_view.xml',
        'reports/purchase_order_template.xml',
        'reports/rfq_report_template.xml',
        'reports/daily_report_sales.xml',
        'reports/order_picture_template.xml',
        'reports/customer_complain_template.xml',
        'reports/internal_memo_template.xml',
        
        'views/views.xml',
        'views/templates.xml',
        'views/sale_view.xml',
        'views/purchase_views.xml',
        'views/res_partner.xml',
        'views/res_users_views.xml',
        'views/account_move_view.xml',
        'views/stock_picking_view.xml',
        'views/mrp_production_view.xml',
        'views/mrp_workorder_views.xml',
        'views/cancel_sq_memory_view.xml',
        'views/daily_report_view.xml',
        'views/daily_report_memory_view.xml',
        'views/customer_complain_view.xml',
        'views/cron_mgm.xml',
        'views/leads_project_view.xml',
        'views/leads_followup_memory.xml',
        'views/confirm_leads_followup_memory_view.xml',
        'views/create_partner_memory_view.xml',
        
        'menus/sales_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}