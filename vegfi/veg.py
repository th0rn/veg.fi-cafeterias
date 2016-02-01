#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch script for generating pre-rendered veg.fi menu pages.
"""

from datetime import datetime
from datetime import timedelta
import logging
import re
import requests

from jinja2 import Template

logging.basicConfig(
    format='%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


SOURCE_API_URL = 'http://www.lounasaika.net/api/v1/menus.json'
TEMPLATE_FILE = 'template.html'

DAYS = ('maanantai', 'tiistai', 'keskiviikko', 'torstai', 'perjantai',
        'lauantai', 'sunnuntai')

# This is ordered
FOOD_TYPES = (
    ('potato', re.compile("perunoita \(")),
    ('carrot', re.compile("porkkan(oit)?aa? \(|Porkkanaraaste")),
    ('strawberry', re.compile("mansikoita \(")),
    ('seed', re.compile("siemeniä \(")),
    ('rice', re.compile("riisiä \(")),
    ('zucchini', re.compile("kesäkurpitsaviipaleita \(")),
    ('smoothie', re.compile("smoothie \(")),
    ('soup', re.compile("keittoa? \(")),
    ('lentils', re.compile("linssejä")),
    ('stew', re.compile("pataa \(")),
    ('tomato', re.compile("tomaatti \(")),
)

MEAL_TYPES = (
    ("main", re.compile("(pataa|pihvejä|currya) \(")),
)

MEAL_CLEAN_RC = re.compile('(?:, L, M, Veg)|(?:\*, )')


def get_weekday_name(weekday_index):
    try:
        return DAYS[weekday_index]
    except IndexError:
        return 'VIRHE'


def guess_type(item, search_regexen, default=None):
    """ Return the tag associated with the first matching regex or None. """
    for tag, reg in search_regexen:
        if reg.search(item):
            return tag
    return default


def clean_meal_string(meal):
    return MEAL_CLEAN_RC.sub('', meal)


def retrieve_meal_data():
    """Return a list of dict of restaurant data from the API.

    Raise a requests.HTTPError on failure.
    """
    response = requests.get(SOURCE_API_URL)
    response.raise_for_status()
    return response.json()


def acceptable_restaurant(restaurant, lang='fi'):
    R = restaurant
    if ('name' in R and 'meals' in R and R['meals'].get(lang) is not None):
        return True
    return False


def extract_vegan_meal(meal):
    """ Return a vegan meal tuple of (meal description, food_type) or None. """
    if 'Veg' in meal:
        # Add food type information
        food_type = guess_type(meal, FOOD_TYPES, default='generic')
        # Remove redundant information
        meal = clean_meal_string(meal)
        return (meal, food_type)
    return None


def get_menu(lang='fi', date=datetime.today()):
    """Returns dict of restaurants to filtered list of meals."""

    update_time = datetime.now().strftime('%a %d %b %Y %H:%M')
    logger.debug("Update time: %s" % update_time)

    weekday = date.weekday()
    logger.debug('weekday: %s' % weekday)
    day_name = get_weekday_name(weekday)

    vegmeals = dict()
    restaurants = retrieve_meal_data()
    for restaurant in restaurants:
        if not acceptable_restaurant(restaurant, lang=lang):
            logger.debug("Incomplete restaurant: {}".format(restaurant))
            continue

        name = restaurant['name']
        meals = restaurant['meals']
        meals_lang = meals[lang]
        if len(meals_lang) < weekday - 1:
            # Not enough days to reach this weekday... somehow
            msg = 'Number of days :: len(meals_lang): {} {}'
            logger.debug(msg.format(name, len(meals_lang)))
            continue

        try:
            meal_iter = (extract_vegan_meal(m) for m in meals_lang[weekday])
            vegmeals_local = [meal for meal in meal_iter if meal is not None]
            if vegmeals_local:
                vegmeals[name] = vegmeals_local
        except IndexError:
            msg = 'Caught error iterating on restaurant \'{}\' (got {} dishes)'
            logger.debug(msg.format(name, len(meals_lang)))

    sorted_meals = sorted(vegmeals.items())
    return sorted_meals, day_name, update_time


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
