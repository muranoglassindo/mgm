from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class LeadsProject(models.Model):
	_name = 'leads.project'
	
	# Detail Leads
	state = fields.Selection([
		('followup1', 'Followup 1'),
		('followup2', 'Followup 2'),
		('followup3', 'Followup 3'),
		('done', 'Done'),
		('closed', 'Closed'),
	], default='followup1')
	salesperson = fields.Char(string="Sales")
	deadline = fields.Date(string="Deadline")
	category = fields.Char(string="Category")
	name = fields.Char(string="Company Name")
	project_type = fields.Char(string="Project Type")
	address = fields.Char(string="Address", compute='_compute_adress', store=True)
	street = fields.Char(string="Street")
	street2 = fields.Char(string="Street2")
	city = fields.Char(string="City")
	states = fields.Char(string="State")
	country = fields.Char(string="Country")
	zip = fields.Char(string="ZIP")
	phone = fields.Char(string="Phone")
	email = fields.Char(string="Email")
	web = fields.Char(string="Website Link")
	status = fields.Selection([
		('wip', 'WIP'),
		('success', 'Success'),
		('failed', 'Failed'),
	], default='wip')
	
	# Contact Person
	contactperson_ids = fields.One2many('contact.person', 'leads_project_id', string="Contact Person")
	
	# Followup leads project
	followup_leads_ids = fields.One2many('followup.leads.project', 'leads_project_id', string="Followup")
	
	def _get_leads_report_filename(self):
		leads_report_file_name = "Leads Followup - " + datetime.now().strftime('%B %Y')
		return leads_report_file_name
	
	@api.depends('street', 'street2')
	def _compute_adress(self):
		""" untuk menyatukan street dan street2
        """
		for leads in self:
			leads.address = leads.street + " " + leads.street2
			
	def write(self, vals):
		for leads in self:
			if "salesperson" in vals or "deadline" in vals or "name" in vals:
				if not self.env.user.has_group('mgm.mgm_group_admin_sales'):
					raise UserError("You cannot edit this Leads")
			super(LeadsProject, self).write(vals)
	
	def action_confirm(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Confirm Followup'),
			'res_model': 'confirm.leads.memory',
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_leads_project_id': self.id,
			},
		}
		
	def action_create_partner(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Create Partner'),
			'res_model': 'create.partner.memory',
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new',
			'context': {
				'default_leads_project_id': self.id,
			},
		}
		
	def action_validate(self):
		for leads in self:
			if leads.state == "followup1":
				leads.state = "followup2"
			elif leads.state == "followup2":
				leads.state = "followup3"
			elif leads.state == "followup3":
				leads.state = "done"
				
	def check_due_date(self):
		# set state menjadi closed ketika sudah melewati deadline
		self._cr.execute("""
			UPDATE leads_project
			SET state = 'closed'
			WHERE deadline < '%s'
		""" % (
			fields.Date.today(),
		))