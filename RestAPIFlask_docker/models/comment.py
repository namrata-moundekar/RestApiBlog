from migrate_cmd import db
from datetime import datetime


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    blogid = db.Column('blogid',db.ForeignKey('blog.id'),unique=False)
    
    
 
        
 
       





