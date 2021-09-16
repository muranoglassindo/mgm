from datetime import datetime
from odoo import models


class LeadsFoloowupXlsx(models.AbstractModel):
	_name = 'report.mgm.leads_followup_xlsx'
	_inherit = 'report.odoo_report_xlsx.abstract'
	
	def generate_xlsx_report(self, workbook, data, lines):
		for obj in lines:
			format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': 'yellow', 'border': 1})
			format2 = workbook.add_format({
				'bold': 1,
				'border': 1,
				'align': 'left',
				'valign': 'vcenter',
				'text_wrap': True})
			head = workbook.add_format({
				'font_size': 14,
				'border': 1,
				'bold': True,
				'valign': 'vcenter',
				'align': 'center',
			})
			sheet = workbook.add_worksheet('Leads Followup')
			
			sheet.set_column('A:P',15)
			sheet.merge_range('A1:P2', 'LEADS FOLLOWUP', head)
			sheet.merge_range('A3:P4', 'SALES PROJECT', head)
			sheet.merge_range('A6:P6', 'PETUNJUK PENGISIAN DATA', format1)
			sheet.merge_range('A7:P22', '1. Type diisi oleh jenis usaha dari perusahaan ybs.\n2. Company Name diisi oleh nama perusahaan ybs.\n3. Street diisi oleh alamat perusahaan ybs (Kampung/RT/RW/No).\n4. Street 2 diisi oleh alamat perusahaan ybs (Kecamatan/Desa).\n5. City diisi oleh alamat perusahaan ybs (Kota).\n6. State diisi oleh lamat perusahaan ybs (Provinsi).\n7. ZIP diisi oleh kode pos dari alamat perusahaan ybs.\n8. Country diisi oleh negara dari perusahaan ybs.\n9. Phone diisi oleh nomor telepon perusahaan ybs.\n10. Email diisi oleh alamat email/surel dari perusahaan ybs.\n11. Website diisi oleh link website dari perusahaan ybs.\n12. Name diisi oleh nama dari contact person perusahaan ybs.\n13. Phone diisi oleh nomor telepon dari contact person perusahaan ybs.\n14. Email diisi oleh email dari contact person perusahaan ybs.\n15. Position diisi oleh jabatan dari contact person perusahaan ybs.\n16. Deadline followup akan otomatis dihitung sebulan dari saat file ini di upload.', format2)
			sheet.write(24, 0, 'Sales', format1)
			sheet.write(24, 1, 'Type', format1)
			sheet.write(24, 2, 'Company Name', format1)
			sheet.write(24, 3, 'Street', format1)
			sheet.write(24, 4, 'Street 2', format1)
			sheet.write(24, 5, 'City', format1)
			sheet.write(24, 6, 'State', format1)
			sheet.write(24, 7, 'ZIP', format1)
			sheet.write(24, 8, 'Country', format1)
			sheet.write(24, 9, 'Phone', format1)
			sheet.write(24, 10, 'Email', format1)
			sheet.write(24, 11, 'Website', format1)
			sheet.write(24, 12, 'Name', format1)
			sheet.write(24, 13, 'Phone', format1)
			sheet.write(24, 14, 'Email', format1)
			sheet.write(24, 15, 'Position', format1)