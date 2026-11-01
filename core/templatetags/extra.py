from django import template
register = template.Library()

@register.filter
def antes_guion(value):
    return str(value).split(' - ', 1)[0]
