from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email

class UploadForm(FlaskForm):
    """A flask-wtf form for additional fields to be sent along with the upload.
       Note: despite temptation to name the button "submit" if you name it "submit"
       that will confuse the javascript when it tries to submit the form, so name it 
       something else ("uploadme" in this case) """
    name = StringField('Your Name', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    original_filename = HiddenField()
    saved_filename = HiddenField()
    uploadme = SubmitField('Continue to Upload', render_kw={"class":"btn btn-primary"})