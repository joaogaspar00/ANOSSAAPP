from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, TextAreaField, SelectField,
                     DateField, FieldList, FormField, FloatField, SubmitField)
from wtforms.validators import DataRequired, Optional, NumberRange


class IngredientLineForm(FlaskForm):
    class Meta:
        csrf = False
    name = StringField("Ingrediente")
    quantity = FloatField("Quantidade", validators=[Optional()])
    unit = StringField("Unidade")


REQUIRED = "Campo obrigatório."
MIN_VALUE = "O valor tem de ser pelo menos %(min)s."


class RecipeForm(FlaskForm):
    name = StringField("Nome da receita", validators=[DataRequired(message=REQUIRED)])
    servings = IntegerField("Porções", validators=[
        DataRequired(message=REQUIRED), NumberRange(min=1, message=MIN_VALUE),
    ], default=2)
    prep_time_minutes = IntegerField("Tempo de preparação (min)", validators=[Optional()])
    category = SelectField("Categoria", choices=[
        ("", "Escolher categoria"),
        ("Pequeno-almoço", "Pequeno-almoço"),
        ("Almoço", "Almoço"),
        ("Jantar", "Jantar"),
        ("Lanche", "Lanche"),
        ("Sobremesa", "Sobremesa"),
        ("Outro", "Outro"),
    ], validators=[Optional()])
    instructions = TextAreaField("Modo de preparação", validators=[Optional()])
    submit = SubmitField("Guardar receita")


class MealPlanForm(FlaskForm):
    planned_date = DateField("Data", validators=[DataRequired(message=REQUIRED)])
    meal_slot = SelectField("Refeição", choices=[
        ("breakfast", "Pequeno-almoço"),
        ("lunch", "Almoço"),
        ("dinner", "Jantar"),
        ("snack", "Lanche"),
    ], default="dinner")
    recipe_id = SelectField("Receita", coerce=int, validators=[Optional()])
    custom_name = StringField("Nome personalizado", validators=[Optional()])
    servings_planned = IntegerField("Porções", validators=[Optional(), NumberRange(min=1, message=MIN_VALUE)], default=2)
    notes = TextAreaField("Notas", validators=[Optional()])
    submit = SubmitField("Planear refeição")
