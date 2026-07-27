from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from app.models import User, CURRENCY_SYMBOLS

REQUIRED = "Campo obrigatório."


class LoginForm(FlaskForm):
    username = StringField("Nome de utilizador", validators=[DataRequired(message=REQUIRED)])
    password = PasswordField("Palavra-passe", validators=[DataRequired(message=REQUIRED)])
    submit = SubmitField("Iniciar sessão")


class RegisterForm(FlaskForm):
    display_name = StringField("Nome", validators=[
        DataRequired(message=REQUIRED),
        Length(max=100, message="Máximo de %(max)d caracteres."),
    ])
    username = StringField("Nome de utilizador", validators=[
        DataRequired(message=REQUIRED),
        Length(max=64, message="Máximo de %(max)d caracteres."),
    ])
    email = StringField("Email", validators=[
        DataRequired(message=REQUIRED),
        Email(message="Introduz um email válido."),
        Length(max=120, message="Máximo de %(max)d caracteres."),
    ])
    password = PasswordField("Palavra-passe", validators=[
        DataRequired(message=REQUIRED),
        Length(min=6, message="Mínimo de %(min)d caracteres."),
    ])
    confirm_password = PasswordField(
        "Confirmar palavra-passe",
        validators=[
            DataRequired(message=REQUIRED),
            EqualTo("password", message="As palavras-passe não coincidem."),
        ]
    )
    submit = SubmitField("Criar conta")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("Este nome de utilizador já está em uso.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Este email já está em uso.")


class HouseholdForm(FlaskForm):
    name = StringField("Nome do casal", validators=[
        DataRequired(message=REQUIRED),
        Length(max=100, message="Máximo de %(max)d caracteres."),
    ])
    currency = SelectField(
        "Moeda",
        choices=[(code, f"{code} ({symbol})") for code, symbol in CURRENCY_SYMBOLS.items()],
        default="EUR",
    )
    submit = SubmitField("Guardar")
