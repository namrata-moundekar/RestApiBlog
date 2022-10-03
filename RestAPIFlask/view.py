from datetime import datetime
from flask import request,render_template
import json
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from flask import jsonify
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
# from passlib.hash import pbkdf2_sha256
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:root@localhost/flaskwebapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Blog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(130), nullable=False)
  content = db.Column(db.Text, nullable=False)
  created_at = db.Column(db.DateTime,default=datetime.utcnow)
  modified_at = db.Column(db.DateTime,default=datetime.utcnow)
  
  userid = db.Column('userid',db.ForeignKey('user.id'),unique=False,nullable=True)
  


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    blogid = db.Column('blogid',db.ForeignKey('blog.id'),unique=False,nullable=True)
       

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(130), nullable=False)
  password = db.Column(db.String(130), nullable=True)
  
  def __init__(self, name, password):
        self.name = name
        self.password = password
# db.create_all()         

class BlogSchema(ma.Schema):
    class Meta:
        fields = ("title", "content", "created_at","modified_at")
 
class UserSchema(ma.Schema):
    class Meta:
        fields = ("name", "password")

class CommentSchema(ma.Schema):
    class Meta:
        fields = ("comment",)


 
blog_schema = BlogSchema()
blogs_schema = BlogSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)


db.create_all() 

### swagger specific ###
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "flask"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###

##########################User#############################################
@app.route('/user_register', methods = ['POST'])
def register():
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('name') and data.get('password') :
            name = data.get('name')
            user = User.query.filter_by(name=name).first()
            if user:
                return json.dumps({"ERROR" : "Duplicate user"})
            usr = User(name=data["name"],password = data["password"])
            db.session.add(usr)
            db.session.commit()
            return json.dumps({"SUCCESS" : f"Record ({usr.id}) Added Successfully...!"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})



@app.route('/userlogin', methods = ['POST'])
def login():
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('name') and data.get('password'):
            name = data.get('name')
            user = User.query.filter_by(name=name).first()
            if user and check_password_hash(user.password,data["password"]):
                # if check_password_hash(user.password,data["password"]):
                    jwt_token=create_access_token(identity=user.name)
                    return json.dumps({"token":jwt_token})
                    
            else:
                return json.dumps({"ERROR":"Invalid name or password"})
        
    else:
         return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})

 
##########################BLOG#############################################


@app.route('/post_blog', methods = ['POST'])
def add_blog():
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('title') and data.get('content') and data.get('created_at') and data.get('modified_at'):
            id = data.get('id')
            blog = Blog.query.filter_by(id=id).first()
            if blog:
                return json.dumps({"ERROR" : "Duplicate Blog"})
            blg = Blog(**data)
            db.session.add(blg)
            db.session.commit()
            return json.dumps({"SUCCESS" : f"Record ({blg.id}) Added Successfully...!"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})

@app.route('/blog/<int:id>',methods=['GET'])
def get_blog(id):
    blog = Blog.query.filter_by(id=id).first()
    if blog:
        json_dict = {"BLOG_ID": blog.id,
                      "BLOG_TITLE": blog.title,
                      "BLOG_CONTENT": blog.content,
                      "BLOD_C_DATE": blog.created_at,
                      "BLOG_M_DATE": blog.modified_at,
                      "BLOG_user_id": blog.userid,}
        return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
    else:
        return json.dumps({"ERROR": f"No blog with Given Id {id}"})


@app.route('/get', methods = ['GET'])
def get_post():
    all_blog = Blog.query.all()
    if all_blog:
        blog_list = []
        for blog in all_blog:
            json_dict = {"BLOG_ID": blog.id,
                          "BLOG_TITLE": blog.title,
                          "BLOG_CONTENT": blog.content,
                          "BLOD_C_DATE": blog.created_at,
                          "BLOG_M_DATE": blog.modified_at,
                          "BLOG_user_id": blog.userid,
                         
                          }
            blog_list.append(json_dict)
        return json.dumps(blog_list,indent=4, sort_keys=True, default=str)

@app.route('/blog/<int:id>',methods=['PUT'])
def update_product(id):
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
                return json.dumps({"SUCCESS" : f"Record ({blog.id}) Updated Successfully...!"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "Blog with given id not present so cannot update.."})


@app.route('/blog/<int:id>',methods=['DELETE'])
def delete_blog(id):
    blg = Blog.query.filter_by(id=id).first()
    if blg:
        db.session.delete(blg)
        db.session.commit()
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...!"})
    return json.dumps({"ERROR": "blog with given id not present so cannot Delete.."})



##########################################COMMENT########################################################


@app.route('/post_comment', methods = ['POST'])
def add_comment():
    data = request.get_json()  # will retrive that json
    if data:
        if data.get('id') and data.get('comment') and data.get('blogid'):
            id = data.get('id')
            comment = Comment.query.filter_by(id=id).first()
            if comment:
                return json.dumps({"ERROR" : "Duplicate comment"})
            cmnt = Comment(**data)
            db.session.add(cmnt)
            db.session.commit()
            return json.dumps({"SUCCESS" : f"Record ({cmnt.id}) Added Successfully...!"})

        return json.dumps({"ERROR": "Required fields not present"})
    else:
        return json.dumps({"ERROR" : "EMPTY BODY, ALL FIELDS REQUIRED"})

@app.route('/comment/<int:id>',methods=['GET'])
def get_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        json_dict = {"comment_ID": comment.id,
                      "comment_TITLE": comment.comment,
                      "comment_BLOGID": comment.blogid,
                      }
        return json.dumps(json_dict,indent=4, sort_keys=True, default=str)
    else:
        return json.dumps({"ERROR": f"No comment with Given Id {id}"})


@app.route('/getcomment', methods = ['GET'])
def get_comment_ALL():
    all_comment = Comment.query.all()
    if all_comment:
        comment_list = []
        for comment in all_comment:
            json_dict = {"comment_ID": comment.id,
                          "comment_TITLE": comment.comment,
                          "comment_BLOGID": comment.blogid,
                         
                          }
            comment_list.append(json_dict)
        return json.dumps(comment_list,indent=4, sort_keys=True, default=str)

    return json.dumps({"ERROR": f"No comments"})

@app.route('/comment/<int:id>',methods=['PUT'])
def update_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        data = request.get_json()
        if data:
            if data.get('comment') and data.get('blogid'):
                comment.comment = data.get('comment')
                comment.blogid = data.get('blogid')
                
                db.session.commit()
                return json.dumps({"SUCCESS" : f"Record ({comment.id}) Updated Successfully...!"})
        return json.dumps({"ERROR": "Required fields not present"})
    return json.dumps({"ERROR": "comment with given id not present so cannot update.."})


@app.route('/comment/<int:id>',methods=['DELETE'])
def delete_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    if comment:
        db.session.delete(comment)
        db.session.commit()
        return json.dumps({"SUCCESS": f"Record ({id}) Removed Successfully...!"})
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
    # db.create_all() 

    app.run(debug=True)
