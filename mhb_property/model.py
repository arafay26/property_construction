from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
from datetime import timedelta,date

class PropertyProject(models.Model):
    _name='project.property'

    name=fields.Char('Project Name')
    partner_id=fields.Many2one('res.partner',string='Owner')
    start_date=fields.Date()
    type=fields.Selection([('Housing Society','Housing Society'),('Appartments','Appartments')],required=1)
    plot_ids=fields.One2many('property.plot','property_id')
    account_id=fields.Many2one('account.account')
    payment_receive=fields.Boolean(string='Schedule invoices')

class Plots(models.Model):
    _name='property.plot'

    description = fields.Text(string='Description')
    property_id=fields.Many2one('project.property')
    type=fields.Selection([('Plot','Plot'),('Appartment','Appartment')])
    size=fields.Char(string='Size')
    bed_rooms=fields.Char(string='Bed Rooms')
    kitchen=fields.Boolean(string='Kitchen')
    property_stage=fields.Selection([('New','New'),('Resale','Resale')])
    # park_facing=fields.Boolean(string='Park facing')
    # corner=fields.Boolean(string='Corner')
    block=fields.Char(string='BLock#')
    floor=fields.Char()
    number=fields.Char(string='Plot#')
    street=fields.Char(string='Street#')
    scheme=fields.Char('Scheme')
    # area=fields.Char('SoecityArea')
    city=fields.Char('City')
    country=fields.Char('Country')
    balconies=fields.Integer(string='Balconies')
    bathrooms=fields.Integer(string='Bathrooms')
    state=fields.Selection([('Available','Available'),('Sold Out','Sold Out'),('Sold By Other','Sold By Other')],default='Available')
    schedule_id=fields.Many2one('payment.schedule',required=1)
    product_id=fields.Many2one('product.product',readonly=1,force_save=1)
    detail_ids=fields.Many2many('amenities.detail')
    order_ids=fields.One2many('sale.order','plot_id')
    move_ids=fields.One2many('account.move','plot_id')

    def NewSaleOrder(self):
        return {
            'name':"Quotation",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context':{'default_plot_id':self.id,'default_order_line': [(0, 0, {'product_id':self.env['product.product'].search([('plot_id','=',self.id)],limit=1).id,
                                                         'name':self.env['product.product'].search([('plot_id','=',self.id)],limit=1).name,
                                                        'price_unit':self.schedule_id.total_amount,

                                                         })]
},
            'target': 'new',
        }
    _rec_name = 'property_id'

    @api.model
    def create(self,vals):
        rec=super(Plots,self).create(vals)
        product_id=self.env['product.product'].create({'plot_id':rec.id,'name':str(rec.number)+', '+str(rec.street)+', '+str(rec.block)+', '+str(rec.property_id.name),'lst_price':rec.schedule_id.total_amount,'property_account_income_id':rec.property_id.account_id.id,'is_plot':True})
        rec.product_id=product_id.id
        return rec

class IneheritProductProduct(models.Model):
    _inherit = 'product.product'

    _rec_name = 'plot_id'

    plot_id=fields.Many2one('property.plot')
    is_plot=fields.Boolean(string='Plot')
    state=fields.Selection([('Available','Available'),('Sold Out','Sold Out'),('Sold By Other','Sold By Other')],default='Available',related='plot_id.state',readonly=True,force_save=True,store=True)

class InheritSaleOrderLine(models.Model):
    _inherit='sale.order.line'

    plot_id=fields.Many2one('property.plot',related='product_id.plot_id',store=True)
    state=fields.Selection([('Available','Available'),('Sold Out','Sold Out'),('Sold By Other','Sold By Other')],default='Available',related='product_id.state',readonly=True,force_save=True,store=True)
    product_id=fields.Many2one('product.product',domain=[('state','=','Available'),('is_plot','=',True)])


class PaymentSch(models.Model):
    _name='payment.schedule'

    name=fields.Char(string='Schedule Name')
    property_id=fields.Many2one('project.property')
    line_ids=fields.One2many('payment.schedule.line','schedule_id')
    total_amount=fields.Float(string='Total Amount',compute='CalcTotal')
    c_line_ids=fields.One2many('commission.line','schedule_id')

    def CalcTotal(self):
        for rec in self:
            total=0
            rec.total_amount=0
            for line in rec.line_ids:
                if rec.recurring:
                    total += line.amount*rec.number_of_invoices
                else:
                    total+=line.amount
            rec.total_amount=total

class PaymentSchLines(models.Model):
    _name='payment.schedule.line'

    schedule_id=fields.Many2one('payment.schedule',string='Schedule')
    recurring=fields.Boolean(string='Recurring')
    interval=fields.Integer(string='Interval')
    number_of_invoices=fields.Integer(string='Number Of Invoices')
    payment_type=fields.Many2one('type.payment',string='Payment Type')
    no_of_months=fields.Integer(string='Months')
    amount=fields.Float(string='Amount')

class InheritCommissionLines(models.Model):
    _name='commission.line'

    schedule_id=fields.Many2one('payment.schedule',string='Schedule')
    amount=fields.Float(string='On amount')
    c_type_id=fields.Many2one('user.commission.type',string='Commission Type',required=1)
    percentage=fields.Float(string='Percentage',required=1)

class paymentType(models.Model):
    _name='type.payment'

    name=fields.Char()
    amenities=fields.Boolean('Amenities')
    default_receive=fields.Boolean(string='By default Invoice')

class Amenities(models.Model):
    _name='amenities.detail'

    name=fields.Char()

    @api.model
    def create(self,vals):
        rec=super(Amenities,self).create(vals)
        self.env['type.payment'].create({'name':rec.name,'amenities':True})
        return rec

class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    cnic=fields.Char(string='CNIC')
    filer=fields.Char(string='Is Filer')
    interests=fields.Char(string='Interests')
    owner=fields.Boolean(string='Is Onwer')

class InheritCrmLead(models.Model):
    _inherit = 'crm.lead'

    cnic=fields.Char(string='CNIC')
    filer=fields.Char(string='Is Filer')


class InheritSaleOrder(models.Model):
    _inherit='sale.order'

    payment_type=fields.Selection([('Installments','Installments'),('Full Payment','Full Payment')])
    commission_paid=fields.Boolean()
    payment_start_date=fields.Date(string='Payment Start Date')
    plot_id=fields.Many2one('property.plot')

    @api.model
    def create(self,vals):
        rec=super(InheritSaleOrder,self).create(vals)
        if rec.opportunity_id.cnic:
            rec.partner_id.cnic=rec.opportunity_id.cnic
        if rec.opportunity_id.filer:
            rec.partner_id.filer=rec.opportunity_id.filer

        return rec

    def action_confirm(self):
        res = super(InheritSaleOrder,self).action_confirm()
        for line in self.order_line:
            line.product_id.plot_id.state='Sold Out'
            line.product_id.state='Sold Out'
            for rec in line.product_id.plot_id.schedule_id.line_ids:
                if rec.payment_type==True or rec.schedule_id.property_id.payment_receive==True:
                    if not rec.payment_type.amenities:
                        print(self.env['account.journal'].search([('type','=','sale')],limit=1).id)
                        inv=self.env['account.move'].create(
                            {
                                'partner_id': self.partner_id.id,
                                'plot_id':self.plot_id,
                                'journal_id':self.env['account.journal'].search([('type','=','sale')],limit=1).id,
                                'invoice_date_due' : date.today() + relativedelta(months=rec.no_of_months),
                                'move_type': 'out_invoice',
                            })
                        print(inv)
                        inv_line=self.env['account.move.line'].create([{'move_id':inv.id,'product_id': line.product_id.id,
                                                                 'name': line.product_id.name,
                                                                 'account_id':line.product_id.property_account_income_id.id,
                                                                 'credit':rec.amount,
                                                                'exclude_from_invoice_tab':False,
                                                                 'quantity': line.product_uom_qty,
                                                                 'product_uom_id': line.product_id.uom_id.id,
                                                                 'price_unit': rec.amount},
                                                             {'move_id': inv.id, 'product_id': line.product_id.id,
                                                              'name': line.product_id.name,
                                                              'account_id': line.product_id.property_account_income_id.id,
                                                              'debit': rec.amount,
                                                              'exclude_from_invoice_tab': True,
                                                              'quantity': line.product_uom_qty,
                                                              'product_uom_id': line.product_id.uom_id.id,
                                                              'price_unit': rec.amount

                                                              }]
    )
                        print(inv_line)
                        if rec.recurring:
                            for i in range(1,rec.number_of_invoices):
                                if not rec.payment_type.amenities:
                                    print(rec)
                                    print('here')
                                    inv = self.env['account.move'].create(
                                        {
                                            'partner_id': self.partner_id.id,
                                            'plot_id': self.plot_id,
                                            'invoice_date_due': date.today() + relativedelta(months=rec.interval*i),
                                            'move_type': 'out_invoice',
                                            'journal_id': self.env['account.journal'].search([('type', '=', 'sale')],
                                                                                             limit=1).id

                                        })
                                    print(inv)
                                    self.env['account.move.line'].create(
                                        [{'move_id': inv.id, 'product_id': line.product_id.id,
                                          'name': line.product_id.name,
                                          'account_id': line.product_id.property_account_income_id.id,
                                          'credit': rec.amount,
                                          'exclude_from_invoice_tab': False,
                                          'quantity': line.product_uom_qty,
                                          'product_uom_id': line.product_id.uom_id.id,
                                          'price_unit': rec.amount},
                                         {'move_id': inv.id, 'product_id': line.product_id.id,
                                          'name': line.product_id.name,
                                          'account_id': line.product_id.property_account_income_id.id,
                                          'debit': rec.amount,
                                          'exclude_from_invoice_tab': True,
                                          'quantity': line.product_uom_qty,
                                          'product_uom_id': line.product_id.uom_id.id,
                                          'price_unit': rec.amount

                                          }]
                                        )

                        # self.env['account.move.line'].create({'move_id':inv.id,'product_id': line.product_id.id,
                        #                                           'name': line.product_id.name,
                        #                                           'account_id': line.product_id.property_account_income_id.id,
                        #                                           'debit': rec.amount,
                        #                                           'quantity': line.product_uom_qty,
                        #                                           'product_uom_id': line.product_id.uom_id.id,
                        #                                           'price_unit': rec.amount
                        #
                        #                                          })
                    else:
                        check=False
                        for line in self.product_id.plot_id.detail_ids:
                            if rec.payment_type.name==line.name:
                                check=True
                        if check:
                            inv = self.env['account.move'].create(
                                {
                                    'partner_id': self.partner_id.id,
                                    'invoice_date_due': date.today() + relativedelta(months=rec.no_of_months),
                                    'move_type': 'out_invoice',
                                    'journal_id': self.env['account.journal'].search([('type', '=', 'sale')],
                                                                                     limit=1).id,

                                })
                            self.env['account.move.line'].create([{'move_id': inv.id, 'product_id': line.product_id.id,
                                                                   'name': line.product_id.name,
                                                                   'account_id': line.product_id.property_account_income_id.id,
                                                                   'credit': rec.amount,
                                                                   'exclude_from_invoice_tab': False,
                                                                   'quantity': line.product_uom_qty,
                                                                   'product_uom_id': line.product_id.uom_id.id,
                                                                   'price_unit': rec.amount},
                                                                  {'move_id': inv.id, 'product_id': line.product_id.id,
                                                                   'name': line.product_id.name,
                                                                   'account_id': line.product_id.property_account_income_id.id,
                                                                   'debit': rec.amount,
                                                                   'exclude_from_invoice_tab': True,
                                                                   'quantity': line.product_uom_qty,
                                                                   'product_uom_id': line.product_id.uom_id.id,
                                                                   'price_unit': rec.amount

                                                                   }])
        return res


class InheritAccountMOve(models.Model):
    _inherit = 'account.move'

    plot_id=fields.Many2one('property.plot')

class CommissionUser(models.Model):
    _name='user.commission.type'

    name=fields.Char(string='Name')

class UserCommission(models.Model):
    _name='user.commission'

    _rec_name = 'user_id'

    date=fields.Date()
    user_id=fields.Many2one('res.users',required=1,string='Agent')
    commission_ids=fields.One2many('user.commission.line','commission_id',readonly=1,force_save=1)
    total_amount=fields.Float('Total Amount')
    status=fields.Selection([('Draft','Draft'),('Submitted','Submitted'),('Validated','Validated'),('Paid','Paid')],default='Draft',string='Status')

    def GetSales(self):
        for rec in self.env['sale.order'].search([('user_id','=',self.user_id.id),('commission_paid','=',False)]):
            total=0
            for inv in self.env['account.move'].search([('invoice_origin','=',rec.name),('state','=','Paid')]):
                total+=inv.amount_total
            for line in total>rec.schedule_id.c_line_ids.filtered(lambda x:x.c_type_id==rec.user_id.c_type_id and x.payment_type==rec.payment_type):
                if total>=line.amount:
                    self.env['user.commission.line'].create({'sale_id':rec.id,'commission_id':self.id,'commission':rec.amount_total*(line.percentage/100)})
                    rec.commission_paid=True
        self.status='Submitted'

    def SetValidated(self):
        self.status='Validated'

    def SetPaid(self):
        self.status='Paid'

class CommissionUserLine(models.Model):
    _name='user.commission.line'

    sale_id=fields.Many2one('sale.order')
    commission_id=fields.Many2one('user.commission')
    commission=fields.Float(string='Commission Amount')
    payment_type=fields.Selection([('Installments','Installments'),('Full Payment','Full Payment')])


class InheritResUser(models.Model):
    _inherit='res.users'

    c_type_id=fields.Many2one('user.commission.type',string='Commission Type',required=1)
