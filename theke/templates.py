'''Templates

Build and manage templates.
'''

import theke

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Config
templates_path = './assets/templates'
assets_path = './assets'

env = Environment(
    loader = FileSystemLoader([templates_path, theke.PATH_CACHE]),
    autoescape = select_autoescape(['html', 'xml'])
)
env.globals.update(zip=zip)

def build_template(template_name, template_data):
    '''Build an asset file from its template.

    @param template_name: name of the tempalte (without extension)
    @param template_data: dict with needed datas to compile the template
    '''
    template = env.get_template('{}.html.j2'.format(template_name))
    template.stream(template_data).dump('{}/{}.html'.format(assets_path, template_name))

def render(template_name, template_data):
    '''Fill a template with given data and return the str.
    '''
    template = env.get_template('{}.html.j2'.format(template_name))
    # TMP. Uncomment to quickly export a rendered template
    # template.stream(template_data).dump('{}.html'.format(template_name))
    return template.render(template_data)

if __name__ == '__main__':
    build_template('welcome_', {'title': 'FOO!'})
