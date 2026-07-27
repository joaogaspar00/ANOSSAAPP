from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import GOAL_TYPES

REQUIRED = "Campo obrigatório."
MIN_VALUE = "O valor tem de ser pelo menos %(min)s."


class GoalForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(message=REQUIRED)])
    description = TextAreaField("Descrição", validators=[Optional()])
    type = SelectField("Tipo", choices=GOAL_TYPES, default="other")
    target_value = FloatField("Valor a atingir", validators=[Optional(), NumberRange(min=0, message=MIN_VALUE)])
    deadline = DateField("Prazo", validators=[Optional()])
    submit = SubmitField("Guardar objetivo")


class ProgressForm(FlaskForm):
    current_value = FloatField("Valor atual", validators=[
        DataRequired(message=REQUIRED), NumberRange(min=0, message=MIN_VALUE),
    ])
    submit = SubmitField("Atualizar progresso")
