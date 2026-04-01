from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Optional


class EditProfileForm(FlaskForm):
    display_name = StringField("Nome de exibição", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Guardar nome")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Palavra-passe atual", validators=[DataRequired()])
    new_password = PasswordField("Nova palavra-passe", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirmar nova palavra-passe",
        validators=[DataRequired(), EqualTo("new_password", message="As palavras-passe não coincidem")]
    )
    submit = SubmitField("Alterar palavra-passe")


class HouseholdNameForm(FlaskForm):
    name = StringField("Nome do agregado familiar", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Guardar")
