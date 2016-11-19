from .. import db


def normalize_string(s):
    """Return a normalized string for use by the template engine

    Different sources of data (i.e. the given resource.md files, the jekyll
    templates, etc.) expect and use different ways of encoding the names of
    various components of the resource object. This function just normalizes
    resource fields of the form "I Have Capital Letters and Spaces" to the form
    "i_have_capital_letters_and_spaces" so that the jinja template can properly
    render anything thrown at it.
    """
    return s.lower().replace(' ', '_')


class OptionAssociation(db.Model):
    """
    Association between a resource and a descriptor with an index for the
    value of the option.
    """
    __tablename__ = 'option_associations'
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'),
                            primary_key=True)
    descriptor_id = db.Column(db.Integer, db.ForeignKey('descriptors.id'),
                              primary_key=True)
    option = db.Column(db.Integer)
    resource = db.relationship('Resource',
                               back_populates='option_descriptors')
    descriptor = db.relationship('Descriptor',
                                 back_populates='option_resources')

    def __repr__(self):
        return '%s: %s' % (self.descriptor.name,
                           self.descriptor.values[self.option])


class TextAssociation(db.Model):
    """
    Association between a resource and a descriptor with a text field for the
    value of the descriptor.
    """
    __tablename__ = 'text_associations'
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'),
                            primary_key=True)
    descriptor_id = db.Column(db.Integer, db.ForeignKey('descriptors.id'),
                              primary_key=True)
    text = db.Column(db.String(64))
    resource = db.relationship('Resource', back_populates='text_descriptors')
    descriptor = db.relationship('Descriptor', back_populates='text_resources')

    def __repr__(self):
        return '%s: %s' % (self.descriptor.name, self.text)


class Descriptor(db.Model):
    """
    Schema for descriptors that contain the name and values for an
    attribute of a resource.
    """
    __tablename__ = 'descriptors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    values = db.Column(db.PickleType)
    is_searchable = db.Column(db.Boolean)
    text_resources = db.relationship(
        'TextAssociation',
        back_populates='descriptor',
        cascade='save-update, merge, delete, delete-orphan'
    )
    option_resources = db.relationship(
        'OptionAssociation',
        back_populates='descriptor',
        cascade='save-update, merge, delete, delete-orphan'
    )

    def __repr__(self):
        return '<Descriptor \'%s\'>' % self.name


class Resource(db.Model):
    """
    Schema for resources with relationships to descriptors.
    """
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    address = db.Column(db.String(64))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    text_descriptors = db.relationship(
        'TextAssociation',
        back_populates='resource',
        cascade='save-update, merge, delete, delete-orphan'
    )
    option_descriptors = db.relationship(
        'OptionAssociation',
        back_populates='resource',
        cascade='save-update, merge, delete, delete-orphan'
    )
    suggestions = db.relationship('Suggestion', backref='resource',
                                  uselist=True)

    def __repr__(self):
        return '<Resource \'%s\'>' % self.name

    @staticmethod
    def generate_fake(count=20, center_lat=39.951021, center_long=-75.197243):
        """Generate a number of fake resources for testing."""
        from sqlalchemy.exc import IntegrityError
        from random import randint
        from faker import Faker
        from geopy.geocoders import Nominatim

        geolocater = Nominatim()
        fake = Faker()

        num_options = 5
        options = []

        for i in range(num_options):
            options.append(Descriptor(
                name=fake.word(),
                values=['True', 'False'],
                is_searchable=fake.boolean()
            ))

        for i in range(count):

            # Generates random coordinates around Philadelphia.
            latitude = str(fake.geo_coordinate(
                center=center_lat,
                radius=0.01
            ))
            longitude = str(fake.geo_coordinate(
                center=center_long,
                radius=0.01
            ))

            location = geolocater.reverse(latitude + ', ' + longitude)
            resource = Resource(
                name=fake.name(),
                address=location.address,
                latitude=latitude,
                longitude=longitude
            )

            oa = OptionAssociation(option=randint(0, 1))
            oa.descriptor = options[randint(0, num_options - 1)]
            resource.option_descriptors.append(oa)

            ta = TextAssociation(text=fake.sentence(nb_words=10))
            ta.descriptor = Descriptor(
                name=fake.word(),
                values=[],
                is_searchable=fake.boolean()
            )
            resource.text_descriptors.append(ta)

            db.session.add(resource)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    @staticmethod
    def get_resources_as_dicts(resources):
        resources_as_dicts = [resource.__dict__ for resource in resources]
        # .__dict__ returns the SQLAlchemy object as a dict, but it also adds a
        # field '_sa_instance_state' that we don't need, so we delete it.
        for d in resources_as_dicts:
            del d['_sa_instance_state']
        return resources_as_dicts

    @staticmethod
    def get_resources_as_full_dicts(resources):
        # maps array of resources to array of useful dictionaries containing
        # all of the information/associations for that resources
        resources_as_dicts = []
        for resource in resources:
            resource_as_dict = resource.__dict__
            resource_as_dict['long'] = resource_as_dict['longitude']
            resource_as_dict['lat'] = resource_as_dict['latitude']

            for td in resource.text_descriptors:
                key = normalize_string(td.descriptor.name)
                value = td.text
                resource_as_dict[key] = value
            for od in resource.option_descriptors:
                key = normalize_string(od.descriptor.name)
                value = od.descriptor.values[od.option]
                resource_as_dict[key] = value

            if '_sa_instance_state' in resource_as_dict:
                del resource_as_dict['_sa_instance_state']
            if 'text_descriptors' in resource_as_dict:
                del resource_as_dict['text_descriptors']
            if 'option_descriptors' in resource_as_dict:
                del resource_as_dict['option_descriptors']

            """
            TEMPORARY
            the following code packages categories/supercategories/etc.
            into lists, this is TEMPORARY since eventually these will be
            lists in the underlying model, but for right now they are just
            strings. after multi-options are added, we can remove this
            """
            resource_as_dict['categories'] = [resource_as_dict['categories']]
            resource_as_dict['supercategories'] = [
                resource_as_dict['supercategories']]
            resource_as_dict['features'] = [resource_as_dict['features']]
            """
            end of TEMPORARY section
            """
            resources_as_dicts.append(resource_as_dict)

        return resources_as_dicts

    @staticmethod
    def print_resources():
        resources = Resource.query.all()
        for resource in resources:
            print resource
            print resource.address
            print '(%s , %s)' % (resource.latitude, resource.longitude)
            print resource.text_descriptors
            print resource.option_descriptors
