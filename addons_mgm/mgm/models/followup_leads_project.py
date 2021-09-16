from odoo import api, fields, models, _

class FollowupLeadsProject(models.Model):
	_name = 'followup.leads.project'
	
	# Detail Leads
	leads_project_id = fields.Many2one('leads.project', string='Leads Project')
	date = fields.Datetime(string="Date")
	user_id = fields.Many2one('res.users', string='Sales')
	followup = fields.Text(string="Information")
	state = fields.Selection([
		('followup1', 'Followup 1'),
		('followup2', 'Followup 2'),
		('followup3', 'Followup 3'),
	], default='followup1')