from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db=SQLAlchemy()

# list of user(s)/librarian(s)
class Users(db.Model, UserMixin):
    __tablename__='users'
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(50),unique=True, nullable=False)
    password=db.Column(db.String, nullable=False)
    date_joined=db.Column(db.Date)
    role=db.Column(db.String,nullable=False,server_default='User')
# all diff sections
class Sections(db.Model):
    __tablename__='sections'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50),unique=True,nullable=False)
    date_created=db.Column(db.Date)
    description=db.Column(db.String)
    # rating=db.Column(db.Float)
# list of all books in lib
class Books(db.Model):
    __tablename__='books'
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50),unique=True,nullable=False)
    content=db.Column(db.Text)
    author=db.Column(db.String)
    upload_on=db.Column(db.Date)
    
# books in sections
class Books_in_Section(db.Model):
    __tablename__="books_in_section"
    book_id=db.Column(db.Integer, db.ForeignKey(Books.id), primary_key=True)
    section_id=db.Column(db.Integer, db.ForeignKey(Sections.id), primary_key=True)

# record of books issued to the users
# class Issued_Books(db.Model):
#     __tablename__='issued_books'
#     user_id=db.Column(db.Integer, db.ForeignKey(Users.id), primary_key=True)
#     book_id=db.Column(db.Integer, db.ForeignKey(Books.id), primary_key=True)

# ratings for books
class Book_Rating(db.Model):
    __tablename__="book_rating"
    book_id=db.Column(db.Integer, db.ForeignKey(Books.id),primary_key=True)
    rated_users=db.Column(db.Integer)
    avg_rating=db.Column(db.Float)
# rating by users for books
class Book_Rated_Users(db.Model):
    __tablename__='book_rated_users'
    book_id=db.Column(db.Integer, db.ForeignKey(Books.id), primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey(Users.id), primary_key=True)
    rating=db.Column(db.Integer)
# rating for sections
class Section_Ratings(db.Model):
    __tablename__='section_ratings'
    section_id=db.Column(db.Integer, db.ForeignKey(Sections.id), primary_key=True)
    rated_users=db.Column(db.Integer)
    avg_rating=db.Column(db.Float)
# rating by users for sections
class Section_Rated_Users(db.Model):
    __tablename__='section_rated_users'
    section_id=db.Column(db.Integer, db.ForeignKey(Sections.id), primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey(Users.id), primary_key=True)
    rating=db.Column(db.Integer)

class Book_Issue_Records(db.Model):
    __tablename__='book_issue_records'
    book_id=db.Column(db.Integer, db.ForeignKey(Books.id), primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey(Users.id), primary_key=True)
    date_of_request=db.Column(db.DateTime,nullable=False)
    valid_upto=db.Column(db.DateTime,nullable=False)
    status=db.Column(db.String,default='Pending')