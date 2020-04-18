import re
from odoo import models, fields, api
from odoo.osv import expression


class AccountInvoiceLine(models.Model):
    _inherit ='account.invoice.line'

    category_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')
    brand = fields.Many2one('product.brand', string='Brand',related='product_id.brand')
    catalog_code = fields.Many2one('product.product',string='Catalog Code',related='product_id')
    seha_code = fields.Char(string='Seha Code',related='product_id.saha_code')

    def update_price(self, pricing_type):
        if pricing_type:
            product = self.product_id
            price_slab_obj = self.env['price.slab'].search(['|', ('product_id', '=', product.id),
                                                            ('product_tmp_id', '=', product.product_tmpl_id.id),
                                                            ('pricing_type', '=', pricing_type), ], limit=1)
            if price_slab_obj:
                self.price_unit = price_slab_obj.price
            else:
                self.price_unit = product.lst_price

    @api.multi
    @api.onchange('seha_code')
    def seha_code_change(self):
        if self.seha_code:
            product_obj = self.env['product.product'].search([('saha_code', '=', self.seha_code)], limit=1)
            if product_obj:
                self.product_id = product_obj.id
                self.update_price(self.invoice_id.pricing_type)

    @api.multi
    @api.onchange('catalog_code')
    def catalog_code_change(self):
        if self.catalog_code:
            self.product_id = self.catalog_code.id
            self.update_price(self.invoice_id.pricing_type)

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        self.brand = self.product_id.brand
        self.category_id = self.product_id.categ_id
        self.catalog_code = self.product_id.id
        self.seha_code = self.product_id.saha_code
        self.update_price(self.invoice_id.pricing_type)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pricing_type = fields.Selection(string="Pricing Type", selection=[('wholesale', 'Wholesale'),
                                                                      ('saha', 'SEHA'),
                                                                      ('moh', 'MOH'),
                                                                      ('retail', 'Retail')], required=True)

    @api.onchange('pricing_type')
    def onchange_pricing_type(self):
        for line in self.invoice_line_ids:
            line.update_price(self.pricing_type)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pricing_type = fields.Selection(string="Pricing Type", selection=[('wholesale', 'Wholesale'),
                                                                      ('saha', 'SEHA'),
                                                                      ('moh', 'MOH'),
                                                                      ('retail', 'Retail')], required=True)

    @api.onchange('pricing_type')
    def onchange_pricing_type(self):
        for line in self.order_line:
            line.product_uom_change()

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({'pricing_type': self.pricing_type})
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    category_id = fields.Many2one('product.category', string='Product Category',)
    brand = fields.Many2one('product.brand', string='Brand')
    catalog_code = fields.Many2one('product.product', string='Catalog Code')
    seha_code = fields.Char(string='Seha Code')

    @api.multi
    @api.onchange('seha_code')
    def seha_code_change(self):
        if self.seha_code:
            product_obj = self.env['product.product'].search([('saha_code', '=', self.seha_code)], limit=1)
            if product_obj:
                self.product_id = product_obj.id

    @api.multi
    @api.onchange('catalog_code')
    def catalog_code_change(self):
        if self.catalog_code:
            self.product_id = self.catalog_code.id

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        self.brand = self.product_id.brand
        self.category_id = self.product_id.categ_id
        self.catalog_code = self.product_id.id
        self.seha_code = self.product_id.saha_code
        return res

    @api.multi
    def _get_display_price(self, product):
        if self.order_id.pricing_type:
            price_slab_obj = self.env['price.slab'].search(['|', ('product_id', '=', product.id),
                                                       ('product_tmp_id', '=', product.product_tmpl_id.id),
                                                       ('pricing_type', '=', self.order_id.pricing_type),], limit=1)
            if price_slab_obj:
                return price_slab_obj.price
            else:
                return super(SaleOrderLine, self)._get_display_price(product)
        else:
            return super(SaleOrderLine, self)._get_display_price(product)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_code_hy = fields.Char('Product Code')
    catalog_code = fields.Char('Catalog Code')
    brand = fields.Many2one('product.brand', string='Brand')
    saha_code=fields.Char('Seha Code')
    price_slab = fields.One2many('price.slab', 'product_tmp_id')
    smd_item_code=fields.Char('SMD Item Code')
    seha_item_description =fields.Text('Seha Item Description')
    smd_item_description = fields.Text('SMD Item Description')
    seha_c_ten= fields.Char('Seha C-Ten')
    award_status= fields.Char('Award Status')

    @api.multi
    def update_catalog(self):
        products = self.env['product.product'].sudo().search([])
        for pro in products:
            if pro.product_tmpl_id.catalog_code:
                pro.catalog_code = pro.product_tmpl_id.catalog_code

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('product_code_hy', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)],
                                            limit=limit2)
                    if not products:
                        products += self.search(args + ['|', ('saha_code', operator, name),
                                                        ('catalog_code', operator, name),
                                                        ('id', 'not in', products.ids)],
                                                limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                products = self.search(domain, limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()


class ProductMaster(models.Model):
    _inherit = 'product.product'

    product_code_hy = fields.Char('Product Code')
    price_slab = fields.One2many('price.slab', 'product_tmp_id')
    smd_item_code = fields.Char('SMD Item Code')
    seha_item_description = fields.Text('Seha Item Description')
    smd_item_description = fields.Text('SMD Item Description')
    seha_c_ten = fields.Char('Seha C-Ten')
    award_status = fields.Char('Award Status')

    @api.multi
    @api.depends('name', 'catalog_code', 'default_code')
    def name_get(self):
        res = []
        for record in self:
            if record.catalog_code:
                catalog_code = '[' + str(record.catalog_code) + ']'
                name = u' '.join((catalog_code, record.name)).encode('utf-8').strip()
            elif record.default_code:
                default_code = '[' + str(record.default_code) + ']'
                name = u' '.join((default_code, record.name)).encode('utf-8').strip()
            else:
                name = str(record.name)
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('product_code_hy', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)],
                                            limit=limit2)
                    if not products:
                        products += self.search(args + ['|', ('saha_code', operator, name),
                                                        ('catalog_code', operator, name),
                                                        ('id', 'not in', products.ids)],
                                                limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                products = self.search(domain, limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()


class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char(string='Name')


class PriceSlab(models.Model):
    _name = 'price.slab'

    pricing_type = fields.Selection(string="Pricing Type", selection=[('wholesale', 'Wholesale'),
                                                                      ('saha', 'SEHA'),
                                                                      ('moh', 'MOH'),
                                                                      ('retail', 'Retail')])
    price = fields.Float('Price')
    product_id = fields.Many2one('product.product')
    product_tmp_id = fields.Many2one('product.template')
