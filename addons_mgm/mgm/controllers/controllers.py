# -*- coding: utf-8 -*-
from odoo import http

# class Mgm(http.Controller):
#     @http.route('/mgm/mgm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mgm/mgm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mgm.listing', {
#             'root': '/mgm/mgm',
#             'objects': http.request.env['mgm.mgm'].search([]),
#         })

#     @http.route('/mgm/mgm/objects/<model("mgm.mgm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mgm.object', {
#             'object': obj
#         })