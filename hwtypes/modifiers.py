# This is a factory for type modifiers.
def make_modifier(name, include_indicator=True):
    _cache = {}
    indicator_key = "__is" + name

    def _Modifier(typ):
        key = id(typ)
        cls_name = name + typ.__name__
        modified_typ = type(cls_name, (typ,), {indicator_key: True})
        return _cache.setdefault(key, modified_typ)

    if not include_indicator:
        return _Modifier

    def _inidicator(inst):
        return getattr(type(inst), indicator_key, False)

    return _Modifier, _inidicator
