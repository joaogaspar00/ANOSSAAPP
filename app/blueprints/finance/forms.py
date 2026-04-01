from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from app.models import EXPENSE_CATEGORIES


class ExpenseForm(FlaskForm):
    date = DateField("Data", validators=[DataRequired()])
    category = SelectField(
        "Categoria",
        choices=[(c, c) for c in EXPENSE_CATEGORIES],
        validators=[DataRequired()]
    )
    amount = FloatField("Valor (DKK)", validators=[DataRequired(), NumberRange(min=0.01)])
    note = TextAreaField("Nota", validators=[Optional()])
    submit = SubmitField("Guardar despesa")
