from django import template

register = template.Library()

@register.filter
def add(value, arg):
    """Add two numbers together."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def lookup(dict_obj, key):
    """Look up a key in a dictionary."""
    try:
        return dict_obj.get(key)
    except (AttributeError, TypeError):
        return None

@register.simple_tag
def nested_lookup(dict_obj, key1, key2):
    """Look up a nested key in a dictionary dict_obj[key1][key2]."""
    try:
        return dict_obj.get(key1, {}).get(key2)
    except (AttributeError, TypeError):
        return None

@register.simple_tag
def status_badge(status):
    """Generate a styled status badge."""
    status_styles = {
        'pending': 'bg-gradient-to-r from-amber-50 to-amber-100 text-amber-700 border border-amber-200',
        'confirmed': 'bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-700 border border-emerald-200',
        'completed': 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border border-blue-200',
        'cancelled': 'bg-gradient-to-r from-slate-50 to-slate-100 text-slate-600 border border-slate-200',
    }
    style = status_styles.get(status.lower(), 'bg-gradient-to-r from-slate-50 to-slate-100 text-slate-600 border border-slate-200')
    display_status = status.title() if status else status
    return f'<span class="inline-block px-3 py-1.5 text-xs font-semibold rounded-lg shadow-sm {style}">{display_status}</span>'
