from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Добавляет CSS класс к полю формы
    Использование: {{ form.field|add_class:"form-control" }}
    """
    return value.as_widget(attrs={'class': arg})
