import json

from flask import render_template, request, redirect, url_for
from flask.ext.login import login_required

from .. import db
from ..models import EditableHTML, Resource
from . import main


@main.route('/')
def index():
    return redirect(url_for('.city_view', city_name='seattle'))


@main.route('/catalog/<string:city_name>')
def city_view(city_name):
    # TODO: use <city_name> to generate the correct resources, etc.
    # for now, we just always render the seattle resources :(
    city = "Seattle, Washington"
    cities = [('Seattle', 'seattle'), ('Philadelphia', 'philadelphia')]
    category_icons = ['housing', 'food', 'hygiene', 'computers', 'employment',
                      'mail', 'recreation']

    ''' RESOURCE STRUCTURE:
        categories = list of string categories
        features = list of string features
        name = string
        content = string (should be atomized to just the important fields!!)
        supercategories = list of strings
        address = string
        lat =
        long =
        website = string
    '''

    resources = Resource.query.all()  # should really just be a specific city
    resources_as_dicts = Resource.get_resources_as_dicts(resources)

    return render_template('main/index.html',
                           city=city,
                           cities=cities,
                           resources=resources_as_dicts,
                           category_icons=category_icons)


@main.route('/get-resources')
def get_resources():
    resources = Resource.query.all()
    resources_as_dicts = Resource.get_resources_as_dicts(resources)
    return json.dumps(resources_as_dicts)


@main.route('/get-associations/<int:resource_id>')
def get_associations(resource_id):
    resource = Resource.query.get(resource_id)
    associations = {}
    if resource is None:
        return json.dumps(associations)
    for td in resource.text_descriptors:
        associations[td.descriptor.name] = td.text
    for od in resource.option_descriptors:
        associations[od.descriptor.name] = od.descriptor.values[od.option]
    return json.dumps(associations)


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template('main/about.html',
                           editable_html_obj=editable_html_obj)


@main.route('/contact')
def contact():
    editable_html_obj = EditableHTML.get_editable_html('contact')
    return render_template('main/contact.html',
                           editable_html_obj=editable_html_obj)


@main.route('/update-editor-contents', methods=['POST'])
@login_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(
        editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200
