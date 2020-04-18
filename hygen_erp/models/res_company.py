# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
        _inherit = 'res.company'

        custom_bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account')
