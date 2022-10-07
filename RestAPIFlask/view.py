from datetime import datetime
from flask import request,render_template
import json
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import check_password_hash
from flask import jsonify
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
# from passlib.hash import pbkdf2_sha256
from  werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, fields
import os
import logging
from marshmallow import Schema, fields

# logging.basicConfig(filename='record.log', level=logging.DEBUG)
logging.basicConfig(filename='record.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

#######################    APP CONFIG HERE  ########################################
"""app config here"""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:root@localhost/flaskwebapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
ma = Marshmallow(app)

app.config["JWT_SECRET_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY2NDg3NTI3NiwianRpIjoiNjBlNTZkMWMtZGM3Yi00MjgxLWE1YzctMTQyMDRhYzdhNzUzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InJpdGEiLCJuYmYiOjE2NjQ4NzUyNzYsImV4cCI6MTY2NDg3NjE3Nn0.yRgDPdQJrV4Smps8XwbFOmr07qIGR-RpyLs6EuVy-0U"
jwt = JWTManager(app)



#######################    MODELS HERE  ########################################

class Blog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(130), nullable=False)
  content = db.Column(db.Text, nullable=False)
  created_at = db.Column(db.DateTime,default=datetime.utcnow)
  modified_at = db.Column(db.DateTime,default=datetime.utcnow)
  userid = db.Column('userid',db.ForeignKey('user.id'),unique=False)
  

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    blogid = db.Column('blogid',db.ForeignKey('blog.id'),unique=False)
    
    def __init__(self, comment, blogid):
          self.comment = comment
          self.blogid = blogid
 
        
 
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(130), nullable=False)
  password = db.Column(db.String(130), nullable=True)
  blog = db.relationship(
        'Blog',
        backref='user',
        cascade='all, delete, delete-orphan',
        single_parent=True
        
    )
  
  def __init__(self, name, password):
        self.name = name
        self.password = password
        
        
db.create_all()         

#######################    MODELS SCHEMA USING MARSHMALLOW HERE  ########################################
class UserSchema(ma.Schema):
    class Meta:
        fields = ("name", "password")
        
        

class BlogSchema(ma.Schema):
    class Meta:
        model = Blog
        load_instance = True
        include_relationships = True

        fields = ("title", "content", "created_at","modified_at","userid")

    user = ma.Nested(UserSchema, many=True)
    
    
    # class Meta:
    #     fields = ("title", "content", "created_at","modified_at","userid")
        
        # userid = fields.Int()
        # user = fields.Nested('UserSchema', default=[], many=True)
 


class CommentSchema(ma.Schema):
    class Meta:
        model = Comment
        load_instance = True
        include_relationships = True
        fields = ("comment","blogid")
    blog = ma.Nested(BlogSchema, many=True)

 
blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

 

################################   swagger specific  ####################################################


SWAGGER_URL = '/swagger/'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "RestAPIFlask"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

############################      End swagger specific     #################################################

##########################      USER REGISTER AND LOGIN CODE HERE     #####################################

@app.route('/user_register/', methods = ['POST'])
def register():
    """ REGISTER USER WITH USERNAME AND PASSWORD"""
    
    data = request.get_json()  # will retrive that json
    if data:
            
            user = User.query.filter_by(name=data.get('name')).first()
            if user:
                return json.dumps({"ERROR" : "Duplicate user"})
            usr = User(name=data["name"],password = generate_password_hash(data["password"]))
            db.session.add(usr)
            db.session.commit()
            app.logger.debug("User added successfully")
            return json.dumps({"SUCCESS" : f"Record ({usr.id}) Added Successfully...! 200"})

        
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})



@app.route('/userlogin/', methods = ['POST'])
def login():
    """ LOGIN WITH USER NAME AND PASSWORD AND IT RETURNS BEARER ACCESS TOKEN"""
    
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('name') and data.get('password'):
            name = data.get('name')
            password= data.get('password')
            user = User.query.filter_by(name=name).first()
            if check_password_hash(user.password,password):
                    jwt_token=create_access_token(identity=user.name)
                    app.logger.debug("Get token when login")
                    return json.dumps({"token":jwt_token})
                    
            else:
                return json.dumps({"ERROR":"Invalid name or password"})    
    else:
         return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})
 
        
 
@app.route('/get_user/', methods = ['GET'])
def get_user():
    """ GET  ALL USER """
    
    all_user = User.query.all()
    if all_user:
        user_lst = []
        for usr in all_user:
            json_dict = {"user_ID": usr.id,
                          "user_name": usr.name,
                          "user_password": usr.password,
                        }
            user_lst.append(json_dict)
        app.logger.debug("Get all user")
        return users_schema.dump(all_user)

 
##########################    BLOG START HERE     #############################################


@app.route('/post_blog', methods = ['POST'])
@jwt_required()
def add_blog():
    """ ADD BLOG POST WITH BEARER TOKEN"""
    
    current_user = get_jwt_identity()
    access_token = create_access_token(identity = current_user)
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('title') and data.get('content') and data.get('created_at') and data.get('modified_at'):
            id = data.get('id')
            blog = Blog.query.filter_by(id=id).first()
            if blog:
                return json.dumps({"ERROR" : "Duplicate Blog -->401"})
            blg = Blog(**data)
            db.session.add(blg)
            db.session.commit()
            app.logger.debug("Blog added successfully")
            return json.dumps({"SUCCESS" : f"Record ({blg.id}) Added Successfully...! 200"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})




@app.route('/blog/<int:id>',methods=['GET'])
def get_blog(id):
    """ GET BLOG POST USING ID"""
    
    blog = Blog.query.filter_by(id=id).first()
    if blog:
        json_dict = {"BLOG_ID": blog.id,
                      "BLOG_TITLE": blog.title,
                      "BLOG_CONTENT": blog.content,
                      "BLOD_C_DATE": blog.created_at,
                      "BLOG_M_DATE": blog.modified_at,
                      "BLOG_user_id": blog.userid,}
        app.logger.debug("Get blog with particular id")
        return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
        
        # return blog_schema.dump(blog)
    else:
        return json.dumps({"ERROR": f"No blog with Given Id {id}"})




@app.route('/get', methods = ['GET'])
def get_post():
    """ GET ALL BLOG POST THROUGH DATABASE"""
    
    all_blog = Blog.query.all()
    # if all_blog:
    #     blog_list = []
    #     for blog in all_blog:
    #         json_dict = {"BLOG_ID": blog.id,
    #                       "BLOG_TITLE": blog.title,
    #                       "BLOG_CONTENT": blog.content,
    #                       "BLOD_C_DATE": blog.created_at,
    #                       "BLOG_M_DATE": blog.modified_at,
    #                       "BLOG_user_id": blog.userid,
                         
    #                       }
    #         blog_list.append(json_dict)
    app.logger.debug("Get all Blog post")
    return blogs_schema.dump(all_blog)
    
    
    

@app.route('/blog/<int:id>',methods=['PUT'])
def update_blog(id):
    """ UPDATE BLOG POST"""
    
    blog = Blog.query.filter_by(id=id).first()
    if blog:
        data = request.get_json()
        if data:
            if data.get('title') and data.get('content') and data.get('created_at') and data.get('modified_at') and data.get('userid'):
                blog.title = data.get('title')
                blog.content = data.get('content')
                blog.created_at = data.get('created_at')
                blog.modified_at = data.get('modified_at')
                blog.userid = data.get('userid')
                db.session.commit()
                app.logger.debug("Blog updated successfully")
                return json.dumps({"SUCCESS" : f"Record ({blog.id}) Updated Successfully...!  200"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "Blog with given id not present so cannot update.."})



@app.route('/blog/search/', methods=['POST'])
@jwt_required()
def search():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    data = request.get_json()


    if data.get('title'):
            search_title = data.get('title')
            blog = Blog.query.filter_by(title=search_title).all()
     
  
    if not blog:
        return json.dumps({"ERROR": "blog not present"})

    return blogs_schema.dump(blog)
    # return json.dumps(blog,indent=4, sort_keys=True, default=str)



@app.route('/blog/<int:id>/',methods=['DELETE'])
def delete_blog(id):
    """ DELETE BLOG POST """
    
    blg = Blog.query.filter_by(id=id).first()
    if blg:
        db.session.delete(blg)
        db.session.commit()
        app.logger.debug("Blog deleted successfully")
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...! 200"})
    return json.dumps({"ERROR": "blog with given id not present so cannot Delete.."})



##########################################  COMMENT START HERE  ########################################################


@app.route('/post_comment/', methods = ['POST'])
@jwt_required()
def add_comment():
    """ ADD comment POST WITH BEARER TOKEN"""
    
    current_user = get_jwt_identity()
    access_token = create_access_token(identity = current_user)
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('comment') and data.get('blogid'):
            id = data.get('id')
            comment = Comment.query.filter_by(id=id).first()
            if comment:
                return json.dumps({"ERROR" : "Duplicate comment-->401"})
            cmnt = Comment(**data)
            db.session.add(cmnt)
            db.session.commit()
            app.logger.debug("Comment added successfully")
            return json.dumps({"SUCCESS" : f"Record ({cmnt.id}) Added Successfully...!  200"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})




@app.route('/comment/<int:id>',methods=['GET'])
def get_comment(id):
    """ GET comment POST THROUGH DATABASE"""
    
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        json_dict = {"comment_ID": comment.id,
                      "comment_TITLE": comment.comment,
                      "comment_BLOGID": comment.blogid,
                      }
        # return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
        app.logger.debug("Get comment with particular id.")
        return comment_schema.dump(comment)
    else:
        return json.dumps({"ERROR": f"No comment with Given Id {id}"})




@app.route('/getcomment', methods = ['GET'])
def get_comment_ALL():
    """ GET ALL comment POST """
    
    all_comment = Comment.query.all()
    if all_comment:
        comment_list = []
        for comment in all_comment:
            json_dict = {"comment_ID": comment.id,
                          "comment_TITLE": comment.comment,
                          "comment_BLOGID": comment.blogid,
                         }
            comment_list.append(json_dict)
        # return json.dumps(comment_list,indent=4, sort_keys=True, default=str)
        app.logger.debug("Get all comments ")
        return comments_schema.dump(all_comment)
    return json.dumps({"ERROR": f"No comments"})




@app.route('/comment/<int:id>',methods=['PUT'])
def update_comment(id):
    """ UPDATE comment POST """
    
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        data = request.get_json()
        if data:
            if data.get('comment') and data.get('blogid'):
                comment.comment = data.get('comment')
                comment.blogid = data.get('blogid')
                
                db.session.commit()
                app.logger.debug("Comment updated successfully")
                return json.dumps({"SUCCESS" : f"Record ({comment.id}) Updated Successfully...!  200"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "comment with given id not present so cannot update.."})



@app.route('/comment/<int:id>',methods=['DELETE'])
def delete_comment(id):
    """ DELETE comment POST """
    
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        db.session.delete(comment)
        db.session.commit()
        app.logger.debug("Comment deleted successfully")
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...! 200"})
    return json.dumps({"ERROR": "comment with given id not present so cannot Delete.."})





# @app.route('/commentsearch',methods=['GET'])
# def search_comment():
#     comment = Comment.query.filter(Comment.title.like('%'+search_term+'%')).first()
#     if comment:
#         json_dict = {"comment_ID": comment.id,
#                       "comment_TITLE": comment.comment,
#                       "comment_BLOGID": comment.blogid,
#                       }
#         return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
#     else:
#         return json.dumps({"ERROR": f"No comment with Given Id {id}"})
   
if __name__ == '__main__':
    db.create_all() 
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True,host='0.0.0.0', port=port)
