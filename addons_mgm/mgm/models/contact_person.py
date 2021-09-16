from odoo import api, fields, models, _

class ContactPerson(models.Model):
	_name = 'contact.person'
	
	leads_project_id = fields.Many2one('leads.project', string='Leads Project')
	name = fields.Char(string="Name")
	phone = fields.Char(string="Phone")
	email = fields.Char(string="email")
	position = fields.Char(string="Position")