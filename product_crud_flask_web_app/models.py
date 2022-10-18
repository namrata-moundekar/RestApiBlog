from product_crud_flask_web_app.config import *
class Product(db.Model):                                                
    id = db.Column('PROD_ID',db.Integer(),primary_key=True)
    name = db.Column('PROD_NAME',db.String(30))
    vendor = db.Column('PROD_VENDOR', db.String(30))
    category = db.Column('PROD_CATEGORY', db.String(30))
    price = db.Column('PROD_PRICE', db.Float())
    qty = db.Column('PROD_QTY', db.Integer())

    @staticmethod
    def dummy_product():
        return Product(id=0,name='',qty=0,price=0.0,category='',vendor='')

db.create_all()     

if __name__ == '__main__':
    
    db.create_all()
