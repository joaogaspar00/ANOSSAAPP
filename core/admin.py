from django.contrib import admin
from .models import Household, UserProfile


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ['nome', 'moeda', 'convite_ativo', 'criado_em']
    list_filter = ['moeda', 'convite_ativo']
    search_fields = ['nome']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'household', 'cor_perfil']
    list_filter = ['household']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user', 'household']
