from ..migrate_cmd import db
from datetime import datetime


#######################    MODELS HERE  ########################################

 
        
 
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
        





