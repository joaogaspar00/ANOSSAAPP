from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import ACTIVITY_TYPES

REQUIRED = "Campo obrigatório."


class ActivityForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(message=REQUIRED)])
    type = SelectField("Tipo", choices=ACTIVITY_TYPES, default="other")
    planned_date = DateField("Data planeada", validators=[Optional()])
    location = StringField("Localização", validators=[Optional()])
    notes = TextAreaField("Notas", validators=[Optional()])
    submit = SubmitField("Guardar")


class RatingForm(FlaskForm):
    value = IntegerField("Avaliação (1-5)", validators=[
        DataRequired(message=REQUIRED),
        NumberRange(min=1, max=5, message="O valor tem de estar entre %(min)s e %(max)s."),
    ])
    submit = SubmitField("Avaliar")
