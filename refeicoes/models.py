from django.db import models
from django.contrib.auth.models import User
from core.models import Household


TIPO_REFEICAO = [
    ('pequeno_almoco', 'Pequeno-almoço'),
    ('almoco', 'Almoço'),
    ('jantar', 'Jantar'),
    ('snack', 'Snack'),
]


class Ingrediente(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    unidade = models.CharField(max_length=50, default='un')

    class Meta:
        verbose_name = 'Ingrediente'
        verbose_name_plural = 'Ingredientes'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.unidade})'


class Refeicao(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='refeicoes')
    nome = models.CharField(max_length=200)
    data = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPO_REFEICAO, default='jantar')
    receita = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    ingredientes = models.ManyToManyField(Ingrediente, through='RefeicaoIngrediente', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refeicoes_criadas')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Refeição'
        verbose_name_plural = 'Refeições'
        ordering = ['data', 'tipo']

    def __str__(self):
        return f'{self.nome} — {self.data}'


class RefeicaoIngrediente(models.Model):
    refeicao = models.ForeignKey(Refeicao, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=8, decimal_places=2, default=1)

    class Meta:
        verbose_name = 'Ingrediente da Refeição'
        unique_together = ('refeicao', 'ingrediente')

    def __str__(self):
        return f'{self.quantidade} {self.ingrediente.unidade} de {self.ingrediente.nome}'


class InventarioItem(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='inventario')
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    minimo_stock = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item de Inventário'
        verbose_name_plural = 'Inventário'
        unique_together = ('household', 'ingrediente')
        ordering = ['ingrediente__nome']

    def __str__(self):
        return f'{self.ingrediente.nome}: {self.quantidade} {self.ingrediente.unidade}'

    def em_falta(self):
        return self.quantidade <= self.minimo_stock


class ItemListaCompras(models.Model):
    CATEGORIA_CHOICES = [
        ('frescos', 'Frescos'),
        ('lacticinios', 'Lacticínios'),
        ('carnes', 'Carnes e Peixes'),
        ('padaria', 'Padaria'),
        ('conservas', 'Conservas'),
        ('bebidas', 'Bebidas'),
        ('higiene', 'Higiene'),
        ('limpeza', 'Limpeza'),
        ('outro', 'Outro'),
    ]
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='lista_compras')
    nome = models.CharField(max_length=200)
    quantidade = models.CharField(max_length=100, blank=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='outro')
    comprado = models.BooleanField(default=False)
    comprado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='compras_feitas')
    comprado_em = models.DateTimeField(null=True, blank=True)
    gerado_automaticamente = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itens_criados')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Item da Lista de Compras'
        verbose_name_plural = 'Lista de Compras'
        ordering = ['comprado', 'categoria', 'nome']

    def __str__(self):
        return self.nome
