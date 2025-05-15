from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permet d'accéder à une valeur de dictionnaire dans un template en utilisant une clé.
    """
    return dictionary.get(key)
