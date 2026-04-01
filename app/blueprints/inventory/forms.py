from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

INVENTORY_CATEGORIES = [
    "Lacticínios", "Carne & Peixe", "Legumes", "Fruta",
    "Cereais", "Conservas & Secos", "Especiarias",
    "Limpeza", "Higiene", "Outro",
]


class InventoryItemForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired()])
    quantity = FloatField("Quantidade", validators=[DataRequired(), NumberRange(min=0)], default=0)
    unit = StringField("Unidade", validators=[DataRequired()])
    min_threshold = FloatField("Quantidade mínima", validators=[Optional(), NumberRange(min=0)])
    is_recurring = BooleanField("Produto fixo (sempre na lista de compras)")
    category = SelectField("Categoria", choices=[(c, c) for c in INVENTORY_CATEGORIES])
    submit = SubmitField("Guardar")


class AdjustQuantityForm(FlaskForm):
    delta = FloatField("Ajustar quantidade (+/-)", validators=[DataRequired()])
    submit = SubmitField("Atualizar")
