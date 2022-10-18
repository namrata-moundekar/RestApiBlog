from flask import Flask, jsonify, send_from_directory
from marshmallow import Schema, fields
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from werkzeug.security import check_password_hash
from flask import jsonify
from flask_marshmallow import Marshmallow, fields
from  werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
import os
import logging
from marshmallow import Schema, fields
from flask_restful import Resource
from flask import Blueprint, Response, request
from pathlib import Path
from urllib.parse import urljoin
from flask import current_app
from flask import make_response
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint 
# from RestAPIFlask.models import *
from .migrate_cmd import db, migrate,redis_cache
from .models.user import User
from .models.comment import Comment
from .models.blog import Blog
from .constants import USER_LIST
from ast import literal_eval
from flask_caching import Cache



#######################     Logging Starts   ######################################
logging.basicConfig(filename='record.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s : %(message)s')

#######################    APP CONFIG HERE  ########################################
"""      app config here    """


app = Flask(__name__, template_folder='./swagger/templates')
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:root@localhost/flaskwebapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

 # configure the redis
# app.config["REDIS_HOST"] = "localhost"
# app.config["REDIS_PASSWORD"] = "password"
# app.config["REDIS_PORT"] = 6379

#######################    Caching CONFIG HERE  ########################################
"""      Caching config here    """

cache = Cache(config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
})



ma = Marshmallow(app)
api = Api(app)

cache.init_app(app)

# redis_cache.init_app(app)
db.init_app(app)
migrate.init_app(app, db)



app.config["JWT_SECRET_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY2NDg3NTI3NiwianRpIjoiNjBlNTZkMWMtZGM3Yi00MjgxLWE1YzctMTQyMDRhYzdhNzUzIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InJpdGEiLCJuYmYiOjE2NjQ4NzUyNzYsImV4cCI6MTY2NDg3NjE3Nn0.yRgDPdQJrV4Smps8XwbFOmr07qIGR-RpyLs6EuVy-0U"
jwt = JWTManager(app)



#######################    MODELS SCHEMA USING MARSHMALLOW HERE  ########################################



class UserSchema(ma.Schema):
    class Meta:
        fields = ("name", "password")
        
class BlogSchema(ma.Schema):
    class Meta:
        fields = ("id","title", "content", "created_at","modified_at","userid")

        
class CommentSchema(ma.Schema):
    class Meta:
        model = Comment
        load_instance = True
        include_relationships = True
        fields = ("id","comment","blogid")
    blog = ma.Nested(BlogSchema, many=True)

 
blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)



################################   Bluprint specific  ####################################################

user_blueprint = Blueprint('user_blueprint', __name__)
blog_blueprint = Blueprint('blog_blueprint', __name__)
comment_blueprint = Blueprint('comment_blueprint', __name__)



###############################   swagger specific  ####################################################


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

###########################      End swagger specific     #################################################




##########################      USER REGISTER AND LOGIN CODE HERE     #####################################


@app.route('/a')
def welcome():
    return "welcome"

@user_blueprint.route('/user_register/', methods = ['POST'])
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
            app.logger.info("User added successfully")
            return json.dumps({"SUCCESS" : f"Record ({usr.id}) Added Successfully...! 200"})
            # return Response(all_user, mimetype="application/json", status=200)
        
    else:
        app.logger.info("User required all fields.")
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})



@user_blueprint.route('/userlogin/', methods = ['POST'])
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
                    app.logger.info("Get token when login")
                    return json.dumps({"token":jwt_token})
                    
            else:
                return json.dumps({"ERROR":"Invalid name or password"})    
    else:
         return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})
 
         




@user_blueprint.route('/get_user/', methods = ['GET'])
@jwt_required()
@cache.cached(timeout=30)
def get_user():
    """Get List of Users
   
    """
    current_user = get_jwt_identity()
    access_token = create_access_token(identity = current_user)
    if cache.get('USER_LIST'):
            print("Getting User Data from redis Cache")
            users = cache.get(USER_LIST)
            print("all_user before",users)
            return users_schema.dump(users)
    else:
        all_user = User.query.all()
        print("all_user after",all_user)
        print("cache",cache)
        app.logger.info("Get all user")
        return users_schema.dump(all_user)
    
    
 
    
 



##########################    BLOG START HERE     #############################################

@blog_blueprint.route('/get_blog/', methods = ['POST'])
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
            app.logger.info("Blog added successfully")
            return json.dumps({"SUCCESS" : f"Record ({blg.id}) Added Successfully...! 200"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})



@blog_blueprint.route('/blog/<int:id>',methods=['GET'])
@cache.cached(timeout=30)
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
        app.logger.info("Get blog with particular id")
        return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
        
        # return blog_schema.dump(blog)
    else:
        return json.dumps({"ERROR": f"No blog with Given Id {id}"})




@blog_blueprint.route('/get_blog/', methods = ['GET'])
@cache.cached(timeout=30)
def get_post():
    """Get List of blog
   
    """
    
    
    all_blog = Blog.query.all()
   
    app.logger.info("Get all Blog post")
    return blogs_schema.dump(all_blog)
    
    
    

@blog_blueprint.route('/blog/<int:id>',methods=['PUT'])
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
                app.logger.info("Blog updated successfully")
                return json.dumps({"SUCCESS" : f"Record ({blog.id}) Updated Successfully...!  200"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "Blog with given id not present so cannot update.."})


@blog_blueprint.route('/blog/search', methods = ['POST'])
@jwt_required()
@cache.cached(timeout=30)
def search_blog():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    data = request.get_json()


    if data.get('title'):
            search_title = data.get('title')
            blog = Blog.query.filter_by(title=search_title).all()
    
    if data.get('content'):
            search_content = data.get('content')
            blog = Blog.query.filter_by(content=search_content).all()
     
     
  
    if not blog:
        return json.dumps({"ERROR": "blog not present"})

    return blogs_schema.dump(blog)
    
 
@blog_blueprint.route('/blog/<int:id>',methods=['DELETE'])
def delete_blog(id):
    """ DELETE BLOG POST """
    
    blg = Blog.query.filter_by(id=id).first()
    if blg:
        db.session.delete(blg)
        db.session.commit()
        app.logger.info("Blog deleted successfully")
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...! 200"})
    return json.dumps({"ERROR": "blog with given id not present so cannot Delete.."})



##########################################  COMMENT START HERE  ########################################################



@comment_blueprint.route('/post_comment/', methods = ['POST'])
@jwt_required()
def add_comment():
    """Post List of comment """
    current_user = get_jwt_identity()
    access_token = create_access_token(identity = current_user)
    data = request.get_json()  # will retrive that json
    if data:
        if data["id"]:
            comment = Comment.query.filter_by(id=data["id"]).first()
            if comment:
                return json.dumps({"ERROR" : "Duplicate comment-->401"})
            cmnt = Comment(id=data["id"],comment=data["comment"],blogid=data["blogid"])
            db.session.add(cmnt)
            db.session.commit()
            app.logger.info("Comment added successfully")
            return json.dumps({"SUCCESS" : f"Record ({cmnt.id}) Added Successfully...!  200"})
            # return CommentListResponseSchema().dump({'comment_list': cmnt})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})




@comment_blueprint.route('/comment/<int:id>',methods=['GET'])
@cache.cached(timeout=30)
def get_comment(id):
    """Comment detail view.
   
    """
   
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        json_dict = {"comment_ID": comment.id,
                      "comment_TITLE": comment.comment,
                      "comment_BLOGID": comment.blogid,
                      }
        # return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
        app.logger.info("Get comment with particular id.")
        return comment_schema.dump(comment)
        # return CommentListResponseSchema().dump({'comment_list': json_dict})
    else:
        return json.dumps({"ERROR": f"No comment with Given Id {id}"})




    

@comment_blueprint.route('/get_comment/',methods=['GET'])
@cache.cached(timeout=30)
def get_comment_ALL():
    """Get List of comment
  
    """
    all_comment = Comment.query.all()
    
    app.logger.info("Get all comments ")
    return comments_schema.dump(all_comment) 
    # return CommentListResponseSchema().dump({'comment_list': all_comment})





@comment_blueprint.route('/comment/<int:id>',methods=['PUT'])
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
                app.logger.info("Comment updated successfully")
                return json.dumps({"SUCCESS" : f"Record ({comment.id}) Updated Successfully...!  200"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "comment with given id not present so cannot update.."})


@comment_blueprint.route('/comment/search/', methods=['POST'])
@jwt_required()
@cache.cached(timeout=30)
def search_comment():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    data = request.get_json()

    if data.get('comment'):
            search_comment = data.get('comment')
            comment = Comment.query.filter_by(comment=search_comment).all()
     
    if not comment:
        return json.dumps({"ERROR": "Comment not present"})

    return comments_schema.dump(comment)



@comment_blueprint.route('/comment/<int:id>',methods=['DELETE'])
def delete_comment(id):
    """ DELETE comment POST """
    
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        db.session.delete(comment)
        db.session.commit()
        app.logger.info("Comment deleted successfully")
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...! 200"})
    return json.dumps({"ERROR": "comment with given id not present so cannot Delete.."})


################################    End of Comment API Endpoints      #########################

# method_view = CommentApi.as_view('comments')
# app.add_url_rule("/comments/{cid}", view_func=method_view)

# with app.test_request_context():
#     jwt_scheme = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
#     spec.components.security_scheme("bearerAuth", jwt_scheme)
#     spec.options["security"] = [{"bearerAuth": []}]
#     # spec.components.schema("Comment", schema=CommentResponseSchema)
#     spec.components.schema("Comment", schema=CommentListResponseSchema)
#     spec.path(view=get_comment_ALL)
#     # spec.path(view="/comment/{cid}", func=get_comment)
#     spec.path(view=get_comment)
#     spec.path(view=add_comment)
#     # spec.path(view=method_view,app=app)
#     spec.path(view=get_post)
#     spec.path(view=get_user)
    
    
# @app.route('/docs')
# @app.route('/docs/<path:path>')
# def swagger_docs(path=None):
#     if not path or path == 'index.html':
#         return render_template('index.html', base_url='/docs')
#     else:
#         return send_from_directory('./swagger/static', secure_filename(path))




##########################################  Blueprint register routes  ########################################################
app.register_blueprint(user_blueprint) 

app.register_blueprint(blog_blueprint) 

app.register_blueprint(comment_blueprint) 
   
if __name__ == '__main__':
    db.create_all() 
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=True,host='0.0.0.0', port=port)
