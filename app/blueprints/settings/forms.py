from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from app.models import CURRENCY_SYMBOLS

REQUIRED = "Campo obrigatório."
MAX_LEN = "Máximo de %(max)d caracteres."


class EditProfileForm(FlaskForm):
    display_name = StringField("Nome de exibição", validators=[
        DataRequired(message=REQUIRED), Length(max=100, message=MAX_LEN),
    ])
    color = StringField("Cor de perfil", validators=[DataRequired(message=REQUIRED)])
    bio = TextAreaField("Sobre mim", validators=[Length(max=200, message=MAX_LEN)])
    submit = SubmitField("Guardar")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Palavra-passe atual", validators=[DataRequired(message=REQUIRED)])
    new_password = PasswordField("Nova palavra-passe", validators=[
        DataRequired(message=REQUIRED), Length(min=6, message="Mínimo de %(min)d caracteres."),
    ])
    confirm_password = PasswordField(
        "Confirmar nova palavra-passe",
        validators=[DataRequired(message=REQUIRED), EqualTo("new_password", message="As palavras-passe não coincidem.")]
    )
    submit = SubmitField("Alterar palavra-passe")


class HouseholdForm(FlaskForm):
    name = StringField("Nome do agregado familiar", validators=[
        DataRequired(message=REQUIRED), Length(max=100, message=MAX_LEN),
    ])
    currency = SelectField(
        "Moeda",
        choices=[(code, f"{code} ({symbol})") for code, symbol in CURRENCY_SYMBOLS.items()],
    )
    submit = SubmitField("Guardar")
