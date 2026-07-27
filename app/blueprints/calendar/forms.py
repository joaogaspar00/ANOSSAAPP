from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional
from app.models import EVENT_VISIBILITIES


class EventForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(message="Campo obrigatório.")])
    event_type = SelectField("Tipo", choices=[
        ("external", "Evento"),
        ("shopping", "Dia de compras"),
    ])
    visibility = SelectField("Visibilidade", choices=EVENT_VISIBILITIES, default="shared")
    start_date = DateField("Data", validators=[DataRequired(message="Campo obrigatório.")])
    notes = TextAreaField("Notas", validators=[Optional()])
    submit = SubmitField("Guardar")
