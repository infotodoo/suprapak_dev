from odoo import models, fields, api
from datetime import datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    state = fields.Selection(selection_add=[('wait','Wait for Portfolio')])

    def validation_invoice_due(self):
        for record in self:
            if record.picking_type_id.warehouse_id.code == 'DES':
                record.state = 'wait'
                domain = [('partner_id','=',record.partner_id.id),('invoice_date_due','<',datetime.today()),('amount_residual','>', 0 )]
                invoice_ids = self.env['account.move'].search(domain)
                total = 0
                for invoice_id in invoice_ids:
                    total += invoice_id.amount_residual
                if total > self.partner_id.credit_limit:
                    res = self.wizard()
                else:
                    res = super(StockPicking,self).button_validate()
            else:
                res = super(StockPicking,self).button_validate()
        return res
       

    def wizard(self):
        imd = self.env['ir.model.data']
        for record in self:
            partners = record.message_follower_ids.partner_id.ids
            users = self.env['res.users'].search([('partner_id.id', 'in', partners)])
            ids = []
            for user in users:
                ids.append((4, user.id))
        vals_wiz = {
            'message': 'Bloqueado por Cartera vencida',
            'users_ids': ids,
        }
        wiz_id = self.env['customer.delivery.wizard'].create(vals_wiz)
        action = imd.xmlid_to_object('dev_customer_credit_limit.action_delivery_wizard')
        form_view_id = imd.xmlid_to_res_id('dev_customer_credit_limit.view_delivery_wizard')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [(form_view_id, 'form')],
            'view_id': form_view_id,
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            'res_id': wiz_id.id,
        }