from ..migrate_cmd import db
from datetime import datetime
#######################    MODELS HERE  ########################################

class Blog(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(130), nullable=False)
  content = db.Column(db.Text, nullable=False)
  created_at = db.Column(db.DateTime,default=datetime.utcnow)
  modified_at = db.Column(db.DateTime,default=datetime.utcnow)
  userid = db.Column('userid',db.ForeignKey('user.id'),unique=False)
  







