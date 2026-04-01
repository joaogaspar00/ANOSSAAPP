from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField("Nome de utilizador", validators=[DataRequired()])
    password = PasswordField("Palavra-passe", validators=[DataRequired()])
    submit = SubmitField("Iniciar sessão")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Palavra-passe atual", validators=[DataRequired()])
    new_password = PasswordField("Nova palavra-passe", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar palavra-passe",
        validators=[DataRequired(), EqualTo("new_password", message="As palavras-passe têm de coincidir")]
    )
    submit = SubmitField("Alterar palavra-passe")


class EditProfileForm(FlaskForm):
    display_name = StringField("Nome de exibição", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Guardar")
