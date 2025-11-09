# First create the directory if it doesn't exist
# mkdir -p e:\rhci\backend\rhci_platform\templatetags

from django import template

register = template.Library()

@register.filter
def zip(a, b):
    """Zip two lists together in a template."""
    return zip(a, b)