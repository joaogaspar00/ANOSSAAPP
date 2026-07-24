def household_context(request):
    if not request.user.is_authenticated:
        return {}
    try:
        profile = request.user.profile
        household = profile.household
        if not household:
            return {'household': None, 'parceiro': None}
        parceiro = household.parceiro(request.user)
        return {
            'household': household,
            'parceiro': parceiro,
        }
    except Exception:
        return {}
