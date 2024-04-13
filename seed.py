"""Seed database with PetFinder API tag data from Pet_Matcher_Tags.CSV."""

from csv import DictReader
from app import db
from models import Tag
from sqlalchemy import insert


db.drop_all()
db.create_all()

with open('generator/Pet_Matcher_Tags.csv') as tags:
    fieldnames= ['tag_name','pet_owner','lifestyle','home_size','qualities']
    db.session.execute(
        insert(Tag),
        DictReader(tags, fieldnames=fieldnames))

db.session.commit()