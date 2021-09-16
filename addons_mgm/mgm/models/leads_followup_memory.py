from odoo import models, fields, api, _
from xlrd import open_workbook,XLRDError
import base64
from odoo.exceptions import ValidationError
from datetime import datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class DairyReportMemory(models.TransientModel):
	_name = 'leads.followup.memory'
	_description = 'Leads Followup Memory'
	
	leads_followup = fields.Binary("File Leads Followup", help='Template Leads Followup Sales Project')
	
	def download_leads_followup(self, context={}):
		self.ensure_one()
		return {
			'type': 'ir.actions.report',
			'report_name':'mgm.leads_followup_xlsx',
			'model':'sale.order',
			'report_type':"xlsx",
		}
	
	def check_leads(self, sales, company_name, deadline):
		# cek keberadaan data yang sama (Sales, perusahaan dan deadline yang sama) jika ada maka update, jika tidak maka buat
		self._cr.execute("""
			SELECT id FROM leads_project
			WHERE (salesperson = '%s' and name = '%s' and deadline = '%s')
		""" % (
			sales,
			company_name,
			deadline
		))
		
		leads_followup_id = self._cr.dictfetchall()
		return leads_followup_id
	
	def upload_leads_followup(self):
		if self.leads_followup:
			try:
				file_data = base64.b64decode(self.leads_followup)
				book = open_workbook(file_contents=file_data)
			except (TypeError, XLRDError) as e:
				raise ValidationError(
					_('It appears that the file you upload is not in valid format, or is corrupted. Details: {}').format(e))
			
			sheet = book.sheets()[0]
			date = datetime.now()
			col_sales = 0
			col_type = 1
			col_company_name = 2
			col_street = 3
			col_street2 = 4
			col_city = 5
			col_state = 6
			col_zip = 7
			col_country = 8
			col_phone = 9
			col_email = 10
			col_website = 11
			col_name = 12
			col_phone_person = 13
			col_email_person = 14
			col_position = 15
			for i in range(sheet.nrows):
				if i > 24:
					sales = sheet.cell(i, col_sales).value.upper()
					type = sheet.cell(i, col_type).value
					company_name = sheet.cell(i, col_company_name).value.upper()
					street = sheet.cell(i, col_street).value
					street2 = sheet.cell(i, col_street2).value
					city = sheet.cell(i, col_city).value.capitalize()
					states = sheet.cell(i, col_state).value.capitalize()
					try:
						zip = int(sheet.cell(i, col_zip).value)
					except ValueError:
						raise ValidationError("ZIP must be a number")
					country = sheet.cell(i, col_country).value.capitalize()
					try:
						phone = int(sheet.cell(i, col_phone).value)
					except ValueError:
						raise ValidationError("Phone must be a number")
					email = sheet.cell(i, col_email).value
					website = sheet.cell(i, col_website).value
					name = sheet.cell(i, col_name).value.upper()
					try:
						phone_person = int(sheet.cell(i, col_phone_person).value)
					except ValueError:
						raise ValidationError("Phone  must be a number")
					email_person = sheet.cell(i, col_email_person).value
					position = sheet.cell(i, col_position).value
					deadline = date + relativedelta(months=+1)
					
					# cek keberadaan data yang sama (Sales, perusahaan dan deadline yang sama) jika ada maka update, jika tidak maka buat
					leads_followup_id = self.check_leads(sales, company_name, deadline)
					
					if leads_followup_id:
						self._cr.execute("""
							UPDATE leads_project
							SET name = '%s',
								address = '%s',
								city = '%s',
								states = '%s',
								country = '%s',
								zip = '%s',
								phone = '%s',
								email = '%s',
								web = '%s',
								deadline = '%s',
								salesperson = '%s',
								project_type = '%s'
							WHERE id = '%s'
						""" % (
							company_name,
							street + " " + street2,
							city,
							states,
							country,
							zip,
							phone,
							email,
							website,
							deadline,
							sales,
							type,
							leads_followup_id[0]['id']
						))
						
						# mencari kontak person dari perusahaan ybs jika ada maka edit, jika tidak maka buat baru
						self._cr.execute("""
							SELECT id FROM contact_person
							WHERE (leads_project_id = '%s' and name = '%s' and phone = '%s')
						""" % (
							leads_followup_id[0]['id'],
							name,
							phone_person,
						))
						
						contact_id = self._cr.dictfetchall()
						
						if contact_id:
							self._cr.execute("""
								UPDATE contact_person
								SET name = '%s',
									phone = '%s',
									email = '%s',
									position = '%s'
								WHERE leads_project_id = '%s' and name ='%s'
							""" % (
								name,
								phone_person,
								email_person,
								position,
								leads_followup_id[0]['id'],
								name,
							))
						else:
							self._cr.execute("""
								INSERT INTO contact_person(leads_project_id, name, phone, email, position)
								VALUES('%s', '%s', '%s', '%s', '%s');
							""" % (
									leads_followup_id[0]['id'],
									name,
									phone_person,
									email_person,
									position
								))
					else:
						self._cr.execute("""
							INSERT INTO leads_project(name, address, city, states, country, zip, phone, email, web, deadline, salesperson, project_type, state, status)
							VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');
						""" % (
							company_name,
							street + " " + street2,
							city,
							states,
							country,
							zip,
							phone,
							email,
							website,
							deadline,
							sales,
							type,
							"followup1",
							"wip",
						))
						
						leads_followup_id = self.check_leads(sales, company_name, deadline)
						
						self._cr.execute("""
							INSERT INTO contact_person(leads_project_id, name, phone, email, position)
							VALUES('%s', '%s', '%s', '%s', '%s');
						""" % (
							leads_followup_id[0]['id'],
							name,
							phone_person,
							email_person,
							position
						))
			return {
				'name': _('Leads Followup Project'),
				'type': 'ir.actions.act_window',
				'view_mode': 'tree,form',
				'res_model': 'leads.project',
				'target': 'current'
			}