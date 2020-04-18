# -*- coding: utf-8 -*-

{
    'name': 'HyGen ERP',
    'summary': 'Hygenic ERP',
    'depends': ['crm','product', 'purchase', 'sale','account','stock'],
    'data': [
            # 'views/sale_form.xml',
             'views/product_form.xml',
             'views/smd_template.xml',
             # 'reports/sale_order.xml',
             # 'reports/report_agedpartnerbalance.xml',
             ],
    'installable': True,
    'autoinstall': False
}