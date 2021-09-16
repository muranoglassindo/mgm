from odoo import api, fields, models, _

class DailyReport(models.Model):
	_name = 'daily.report'
	
	date = fields.Date(string="Visit Date")
	input_date = fields.Char(string="Date")
	name = fields.Char(string="Salesperson")
	area = fields.Char(string="Area")
	customer = fields.Char(string="Customer")
	report = fields.Text(string="Report")
	phone = fields.Char(string="Phone")
	stamp = fields.Selection([
		('true', 'Ada'),
		('false', 'Tidak Ada')
	], default='false')
	sign = fields.Selection([
		('true', 'Ada'),
		('false', 'Tidak Ada')
	], default='false')