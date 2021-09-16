from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class ConfirmLeads(models.TransientModel):
	_name = 'confirm.leads.memory'
	
	leads_project_id = fields.Many2one('leads.project', string='Leads Project', required=True)
	followup = fields.Text("Reason", required=True)
	status = fields.Selection([
		('wip', 'WIP'),
		('success', 'Success'),
		('failed', 'Failed'),
	], default='wip')
	
	def action_confirm(self):
		"""
		Confirm followup Leads
		:return:
		"""
		if self.status:
			if self.leads_project_id.state == "followup3" and self.status == "wip":
				raise ValidationError(_("Status for leads should not be WIP in this state."))
			else:
				self.leads_project_id.status = self.status
		else:
			raise ValidationError(_("Status for leads cannot be Empty."))
		self.env['followup.leads.project'].create({
			'leads_project_id': self.leads_project_id.id,
			'date': datetime.now(),
			'user_id': self.env.user.id,
			'followup': self.followup,
			'state': self.leads_project_id.state,
		})
		self.leads_project_id.action_validate()

