from odoo import api, fields, models, tools, SUPERUSER_ID, _

class SalesAdmin(models.Model):
	_name = 'sales.admin'
	
	name = fields.Char(string="Name")
	code = fields.Char(string="Code")