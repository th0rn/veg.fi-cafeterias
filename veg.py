#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""<+Module Description.+>"""

from datetime import datetime
from datetime import timedelta
import json
import logging
import re
import requests

from jinja2 import Template

logging.basicConfig(level=logging.DEBUG)

SOURCE_API_URL = 'http://www.lounasaika.net/api/v1/menus.json'
TEMPLATE_FILE = 'template.html'


def get_weekday_name(weekday_index):
    if weekday_index == 0:
        return 'maanantai'
    elif weekday_index == 1:
        return 'tiistai'
    elif weekday_index == 2:
        return 'keskiviikko'
    elif weekday_index == 3:
        return 'torstai'
    elif weekday_index == 4:
        return 'perjantai'
    elif weekday_index == 5:
        return 'lauantai'
    elif weekday_index == 6:
        return 'sunnuntai'
    else:
        return 'VIRHE'


def guess_food_type(food):

    if re.search(".*perunoita \(", food) is not None:
        return 'potato'
    if re.search(".*porkkan(oit)?aa? \(|Porkkanaraaste.*", food) is not None:
        return 'carrot'
    # if re.search("Porkkanaraaste.*", food) is not None:
        # return 'carrot'
    if re.search(".*mansikoita \(", food) is not None:
        return 'strawberry'
    if re.search(".*siemeniä \(", food) is not None:
        return 'seed'
    if re.search(".*riisiä \(", food) is not None:
        return 'rice'
    if re.search(".*kesäkurpitsaviipaleita \(", food) is not None:
        return 'zucchini'
    if re.search(".*smoothie \(", food) is not None:
        return 'smoothie'
    if re.search(".*keittoa? \(", food) is not None:
        return 'soup'
    if re.search(".*linssejä.*", food) is not None:
        return 'lentils'
    if re.search(".*pataa \(", food) is not None:
        return 'stew'
    if re.search(".*tomaatti \(", food) is not None:
        return 'tomato'
    return 'generic'


def guess_meal_type(food):

    if re.search(".*pataa \(", food) is not None:
        return 'main'
    if re.search(".*pihvejä \(", food) is not None:
        return 'main'
    if re.search(".*currya \(", food) is not None:
        return 'main'


def get_menu(lang='fi', date=datetime.today()):
    """Returns dict of restaurants to filtered list of meals."""

    response = requests.get(SOURCE_API_URL)
    response_content = response.text
    response_json = json.loads(response_content)
    vegmeals = {}
    logging.debug('date.weekday(): %s' % date.weekday())
    weekday = date.weekday()
    logging.debug('weekday: %s' % weekday)

    for restaurant in response_json:
        name = restaurant.get('name')
        meals = restaurant.get('meals', {})
        if meals:
            meals_en = meals.get(lang, [])
            if meals_en:
                vegmeals_local = list()
                logging.debug('len(meals_en): %s' % len(meals_en))
                # TODO: Collect entire week's data, not just one day.
                try:
                    for meal in meals_en[weekday]:
                        if meal.find("Veg") != -1:
                            # Add food type information
                            food_type = guess_food_type(meal)
                            # Remove redundant information
                            meal = re.sub('(?:, L, M, Veg)|(?:\*, )', '', meal)
                            vegmeals_local.append([meal, food_type])
                except IndexError:
                    logging.debug(
                            'Out of range for %s.' % restaurant.get('name')
                            )
                if vegmeals_local:
                    vegmeals[name] = vegmeals_local
    day_name = get_weekday_name(weekday)

    update_time = datetime.now().strftime('%a %d %b %Y %H:%M')
    logging.debug("Update time: %s" % update_time)
    return vegmeals, day_name, update_time


def get_plaintext_menu(lounas_dict):
    """Returns a plaintext aggregation of filtered meals for each restaurant"""

    string = ""
    for name, meals in lounas_dict.items():
        if meals:
            string += u"%s\n" % name.upper()
            for meal in meals:
                paren_index = meal.find('(')
                if paren_index > -1:
                    meal = meal[:(paren_index - 1)]
                string += "- %s\n" % meal
            string += '\n'
    # return string.rstrip()
    return string


def render_html():
    """Render HTML with content."""

    # Read html template from file.
    with open(TEMPLATE_FILE, 'r') as template_file:
        template = Template(template_file.read())

    # Get menu dict, day string, and update time datetime for today.
    menu_today, day_today, updated_today = get_menu()

    # Then for tomorrow.
    tomorrow = datetime.today() + timedelta(days=1)
    menu_tomorrow, day_tomorrow, updated_tomorrow = get_menu(date=tomorrow)

    # If tomorrow is Mon, we must discard menu as it is for the previous Mon.
    if day_tomorrow == 'maanantai':
        menu_tomorrow = {}

    # Render template with information for today and tomorrow.
    html_rendered = template.render(
            menu=[menu_today, menu_tomorrow],
            day=[day_today, day_tomorrow],
            updated=[updated_today, updated_tomorrow],
            )

    # Write filled-in template to file.
    with open('rendered.html', 'w') as rendered_html:
        rendered_html.write(html_rendered)

    return 0


def main():
    """Run main."""

    render_html()

    return 0

if __name__ == '__main__':
    main()
