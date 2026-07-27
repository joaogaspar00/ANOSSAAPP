from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, IntegerField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import TASK_PRIORITIES


class TaskForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(message="Campo obrigatório.")])
    description = TextAreaField("Descrição", validators=[Optional()])
    due_date = DateField("Data de vencimento", validators=[Optional()])
    priority = SelectField("Prioridade", choices=TASK_PRIORITIES, default="medium")
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
        "Intervalo (dias)",
        validators=[Optional(), NumberRange(min=1, message="O valor tem de ser pelo menos %(min)s.")],
        default=2,
    )
    submit = SubmitField("Guardar tarefa")
