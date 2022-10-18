
from product_crud_flask_web_app.models import *

from flask import request,render_template


@app.route("/product/",methods = ["GET"])
def welcome_page():
    return render_template('product.html',product = Product.dummy_product(),products = Product.query.all())


@app.route('/product/save/', methods = ['POST'])   
def save_product_information():
    msg = ''

    reqdata  = request.form         
    if reqdata:
        dbprod = Product.query.filter_by(id=reqdata.get('pid')).first()
        if dbprod:
            
            dbprod.name = reqdata.get('pname')
            dbprod.qty = reqdata.get('pqty')
            dbprod.price = reqdata.get('pprice')
            dbprod.vendor = reqdata.get('pven')
            dbprod.category = reqdata.get('pcat')
            db.session.commit()    
            msg = "Product Updated Successfully...!"
        else:
            prod = Product(id=reqdata.get('pid'),
                    name=reqdata.get('pname'),
                    qty=reqdata.get('pqty'),
                    price=reqdata.get('pprice'),
                    vendor=reqdata.get('pven'),
                    category=reqdata.get('pcat'))
            db.session.add(prod)        # insert query will be fired..
            db.session.commit()         # data will be committed
            msg = "Product Added Successfully...!"
            #prod = Product.dummy_product()  #empty

        #prod_list = Product.query.all()
    return render_template('product.html',resp = msg,product = Product.dummy_product(),products = Product.query.all())

@app.route("/delete/<int:pid>",methods = ['GET'])
def delete_product(pid):
    msg = ''
    dbprod = Product.query.filter_by(id=pid).first()
    if dbprod:
        db.session.delete(dbprod)
        db.session.commit()
        msg = "Product Deleted Successfully...!"
    return render_template('product.html', resp=msg, product=Product.dummy_product(), products=Product.query.all())


@app.route("/edit/<int:pid>",methods = ['GET'])
def populate_data_in_form_for_edit(pid):
    dbprod = Product.query.filter_by(id=pid).first()
    return render_template('product.html', resp='', product=dbprod, products=Product.query.all())






if __name__ == '__main__':
    app.run(debug=True)


