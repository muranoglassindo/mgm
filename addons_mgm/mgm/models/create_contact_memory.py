from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class DairyReportMemory(models.TransientModel):
	_name = 'create.partner.memory'
	_description = 'Create Partner Memory'
	
	leads_project_id = fields.Many2one('leads.project', string='Leads Project', required=True)
	
	def create_partner(self):
		self._cr.execute("""
			SELECT id
			FROM res_partner
			WHERE name = '%s'
		""" % (
			self.leads_project_id.name
		))
		
		partner = self._cr.dictfetchall()
		
		if not partner:
			# mengecek state dan country dari adress
			self._cr.execute("""
				SELECT id
				FROM res_country_state
				WHERE name = '%s'
			""" % (
				self.leads_project_id.states
			))
			
			state = self._cr.dictfetchall()
			
			self._cr.execute("""
				SELECT id
				FROM res_country
				WHERE name = '%s'
			""" % (
				self.leads_project_id.country
			))
			
			country = self._cr.dictfetchall()
			
			# membuat data partner
			if state and country:
				partner = self.env['res.partner']
				company = partner.create({
					'company_type': "company",
					'name': self.leads_project_id.name,
					'street': self.leads_project_id.address,
					'city': self.leads_project_id.city,
					'state_id': state[0]['id'],
					'country_id': country[0]['id'],
					'zip': self.leads_project_id.zip,
					'phone': self.leads_project_id.phone,
					'email': self.leads_project_id.email,
					'website': self.leads_project_id.web
				})
				if self.leads_project_id.contactperson_ids:
					for rec in self.leads_project_id.contactperson_ids:
						partner.create({
							'company_type': "person",
							'parent_id': company.id,
							'name': rec.name,
							'phone': rec.phone,
							'email': rec.email,
							'function': rec.position,
						})
			else:
				if not state and not country:
					raise ValidationError(_("Invalid state and country address."))
				elif not state and country:
					raise ValidationError(_("Invalid state address."))
				elif not country and state:
					raise ValidationError(_("Invalid country address."))
		else:
			raise ValidationError(_("Partner is already exists."))