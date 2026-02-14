from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def wrap_title_words(title):
    """Wrap multi-word titles: first word on first line, rest on new line."""
    words = title.strip().split(' ')
    if len(words) > 1:
        return mark_safe(f'{words[0]}<br>{" ".join(words[1:])}')
    return title

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
        'pending': 'bg-[#FDF6CC] text-[#967D21] border-[#D4AF37]',
        'confirmed': 'bg-[#F0FDF4] text-[#16A34A] border-[#22C55E]',
        'completed': 'bg-[#FEFDF5] text-[#584B0B] border-[#E5E7EB]',
        'cancelled': 'bg-[#FEE2E2] text-[#DC2626] border-[#EF4444]',
    }
    style = status_styles.get(status.lower(), 'bg-[#F3F4F6] text-[#6B7280] border-[#D1D5DB]')
    display_status = status.title() if status else status
    html = f'<span class="inline-block px-1.5 py-0.5 text-[10px] font-medium rounded {style}">{display_status}</span>'
    return mark_safe(html)
