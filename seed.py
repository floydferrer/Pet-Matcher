"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db
from models import User, Pet, Tag
from sqlalchemy import insert


db.drop_all()
db.create_all()

with open('generator/Pet_Matcher_Tags.csv') as tags:
    fieldnames= ['tag_name','pet_owner','lifestyle','home_size','qualities']
    db.session.execute(
        insert(Tag),
        DictReader(tags, fieldnames=fieldnames))
# with open('generator/Pet_Matcher_Tags.csv') as tags:
#     db.session.bulk_insert_mappings(Tag, DictReader(tags), render_nulls=True)

db.session.commit()