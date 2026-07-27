from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from app.models import EXPENSE_CATEGORIES, SPLIT_TYPES

REQUIRED = "Campo obrigatório."


class ExpenseForm(FlaskForm):
    date = DateField("Data", validators=[DataRequired(message=REQUIRED)])
    category = SelectField(
        "Categoria",
        choices=[(c, c) for c in EXPENSE_CATEGORIES],
        validators=[DataRequired(message=REQUIRED)]
    )
    amount = FloatField("Valor", validators=[
        DataRequired(message=REQUIRED),
        NumberRange(min=0.01, message="O valor tem de ser pelo menos %(min)s."),
    ])
    paid_by_id = SelectField("Pago por", coerce=int, validators=[DataRequired(message=REQUIRED)])
    split_type = SelectField("Divisão", choices=SPLIT_TYPES, default="50_50")
    amount_a = FloatField("Parte do membro 1", validators=[Optional(), NumberRange(min=0, message="O valor tem de ser pelo menos %(min)s.")])
    amount_b = FloatField("Parte do membro 2", validators=[Optional(), NumberRange(min=0, message="O valor tem de ser pelo menos %(min)s.")])
    note = TextAreaField("Nota", validators=[Optional()])
    submit = SubmitField("Guardar despesa")

    def validate_amount_b(self, field):
        if self.split_type.data == "custom":
            total = (self.amount_a.data or 0) + (field.data or 0)
            if abs(total - (self.amount.data or 0)) > 0.01:
                raise ValidationError("A soma das partes tem de ser igual ao valor total.")
