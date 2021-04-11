'''Templates

Build and manage templates.
'''

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Config
templates_path = '../theke/assets/templates'
assets_path = '../theke/assets'

env = Environment(
    loader = FileSystemLoader(templates_path),
    autoescape = select_autoescape(['html', 'xml'])
)

def build_template(template_name, template_data):
    '''Build an asset file from its template.

    @param template_name: name of the tempalte (without extension)
    @param template_date: dict with needed datas to compile the template
    '''
    template = env.get_template('{}.html.j2'.format(template_name))
    template.stream(template_data).dump('{}/{}.html'.format(assets_path, template_name))

if __name__ == '__main__':
    build_template('welcome_', {'title': 'FOO!'})