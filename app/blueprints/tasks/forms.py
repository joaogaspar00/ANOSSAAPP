from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import RECURRENCE_TYPES


class TaskForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired()])
    description = TextAreaField("Descrição", validators=[Optional()])
    due_date = DateField("Data de vencimento", validators=[Optional()])
    assigned_to_id = SelectField("Atribuído a", coerce=int, validators=[Optional()])
    recurrence_type = SelectField(
        "Recorrência",
        choices=[
            ("none", "Nenhuma"),
            ("daily", "Diário"),
            ("weekly", "Semanal"),
            ("monthly", "Mensal"),
            ("every_x_days", "A cada X dias"),
        ],
        default="none",
    )
    interval_days = IntegerField(
        "Intervalo (dias)", validators=[Optional(), NumberRange(min=1)], default=2
    )
    submit = SubmitField("Guardar tarefa")
