
import os
from flask import Flask,request
from flask import render_template, url_for, redirect, flash
from sqlalchemy import exc
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, login_manager, UserMixin
from datetime import date,datetime,timedelta
from application.models import *
# from werkzeug.utils import secure_filename
from fpdf import FPDF
app=Flask(__name__)
# current_dir=os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'pdf','doc'}
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///library_database.sqlite3"
app.config['SECRET_KEY']="veryverysecurekey"
# app.config['UPLOAD_FOLDER']="static"

db.init_app(app)
login_manager=LoginManager(app)
app.app_context().push()

@login_manager.user_loader #current_user details
def load_user(id):
    return Users.query.get(id)

@app.route('/new_user', methods=["GET",'POST']) #new user registration
def new_user():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        cpass=request.form.get('cpassword')
        if cpass==password:
            userx=Users(username=username, password=password,date_joined=date.today())
            db.session.add(userx)
            db.session.commit()
            return redirect('/login')
        else:
            return 'Passwords didnot match. Pls retry'
    return render_template('new_user.html')

@app.route('/login', methods=["GET","POST"]) #logging in a user
def log_in_user():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        this_user=Users.query.filter_by(username=username).first()
        
        if this_user:
            if this_user.role=='User':
                if this_user.password==password:
                    login_user(this_user, force=True)
                    return redirect('/sections')
                return "Username or Password didnot match! Please try again"
        return "User doesn't exist"
    return render_template('login_user.html')

@app.route('/login/admin', methods=["GET","POST"]) #admin(librarian) login
def log_in_admin():
    if request.method=="POST":
        username=request.form.get('username')
        password=request.form.get('password')
        this_user=Users.query.filter_by(username=username).first()
        
        if this_user:
            if this_user.role=='Admin':
                if this_user.password==password:
                    login_user(this_user, force=True)
                    # return redirect('/admin/dashboard')
                    return redirect('/sections')
                return "Username or Password didnot match! Please try again"
        return "User doesn't exist"
    return render_template('login_admin.html')

@app.route('/') #Homepage
def home():
    if current_user:
        return redirect('/sections')
    return redirect('/login')

#sections
@app.route('/sections') #Sections page R
@login_required
def sections():
    sections=Sections.query.all()
    rating=Section_Ratings.query.all()
    if rating:
        rating.sort(key=lambda x: (x.avg_rating or 0),reverse=True)
    s=[]
    for x in rating:
        for y in sections:
            if x.section_id==y.id:
                s.append(y)
    print(s)
    return render_template('sections_page.html',sections=s,rating=rating)

@app.route('/sections/add_new', methods=['GET','POST']) #new section C
@login_required
def add_sections():
    if current_user.role=='Admin':
        if request.method=='POST':
            name=request.form.get('name')
            descr=request.form.get('description')
            sec_new=Sections(name=name,date_created=date.today(),description=descr)
            db.session.add(sec_new)
            sec=Sections.query.filter_by(name=name,description=descr).first()
            ratex=Section_Ratings(section_id=sec.id)
            db.session.add(ratex)
            db.session.commit()
            return redirect('/sections')
        return render_template('add_sections.html') #req
    return 'Access Denied !'

@app.route('/sections/update/<int:sid>',methods=['GET','POST']) #edit section U
@login_required
def update_section(sid):
    sec=Sections.query.filter_by(id=sid).first()
    if request.method=='POST':
        sec.name=request.form.get('name')
        sec.description=request.form.get('description')
        db.session.add(sec)
        db.session.commit()
        return redirect('/sections')
    return render_template('add_sections.html',sec=sec) #req

@app.route('/sections/remove<sid>') #confirm before deleting section
@login_required
def remove_section_confirmation(sid):
    return f'<a href="/sections/remove/{sid}">Confirm?</a>'

@app.route('/sections/remove/<int:sid>') #delete section D
@login_required
def remove_section(sid):
    if current_user.role=='Admin':
        sec=Sections.query.get_or_404(sid)
        bk_in_sec=Books_in_Section.query.filter_by(section_id=sid).all()
        sect_rate=Section_Ratings.query.filter_by(section_id=sid).first()
        sect_rated_users=Section_Rated_Users.query.filter_by(section_id=sid).all()
        if bk_in_sec:
            for x in bk_in_sec:
                db.session.delete(x)
                remove_book(x.book_id)
        if sect_rate:db.session.delete(sect_rate)
        if sect_rated_users:
            for x in sect_rated_users:
                db.session.delete(x)
        db.session.delete(sec)
        db.session.commit()
        return redirect('/sections')
    else:
        return 'Access Denied!'

@app.route('/ratesections/<id>',methods=['GET','POST'])
@login_required
def section_rating(id):
    sections=Section_Ratings.query.filter_by(section_id=id).first()
    rated=Section_Rated_Users.query.filter_by(section_id=id).all()
    rating_done=False
    r_user=None
    for x in rated:
        if x.user_id==current_user.id:
            rating_done=True
            given=int(x.rating)
            r_user=x
            break
    if request.method=='POST':
        try:
            if sections.rated_users:
                total_rating=int(int(sections.rated_users)*float(sections.avg_rating))
                new_rating=int(request.form.get('rating'))
                total_users=int(sections.rated_users)
                if not rating_done:
                    total_users=int(sections.rated_users)+1
                    avg=round((total_rating+new_rating)/total_users,2)
                    s_rate=Section_Rated_Users(section_id=id,user_id=current_user.id,rating=new_rating)
                    db.session.add(s_rate)
                else:
                    total_rating-=given
                    avg=round((total_rating+new_rating)/total_users,2)
                    r_user.rating=new_rating
                    db.session.add(r_user)
            else:
                new_rating=int(request.form.get('rating'))
                avg=new_rating/1
                total_users=1
                s_rate=Section_Rated_Users(section_id=id,user_id=current_user.id,rating=new_rating)
                db.session.add(s_rate)
        except exc.IntegrityError:
            return 'Error!'
        sections.rated_users=total_users
        sections.avg_rating=avg
        db.session.add(sections)
        db.session.commit()
        return redirect('/sections')
    print(sections)
    return render_template('ratings.html',sections=sections,x=r_user)

#books

@app.route('/ratebook/<id>',methods=['GET','POST'])
@login_required
def book_rating(id):
    book=Book_Rating.query.filter_by(book_id=id).first()
    rated=Book_Rated_Users.query.filter_by(book_id=id).all()
    rating_done=False
    r_user=None
    for x in rated:
        if x.user_id==current_user.id:
            rating_done=True
            given=int(x.rating)
            r_user=x
            break
    if request.method=='POST':
        try:
            if book.rated_users:
                total_rating=int(int(book.rated_users)*float(book.avg_rating))
                new_rating=int(request.form.get('rating'))
                total_users=int(book.rated_users)
                if not rating_done:
                    total_users=int(book.rated_users)+1
                    avg=round((total_rating+new_rating)/total_users,2)
                    b_rate=Book_Rated_Users(book_id=id,user_id=current_user.id,rating=new_rating)
                    db.session.add(b_rate)
                else:
                    total_rating-=given
                    avg=round((total_rating+new_rating)/total_users,2)
                    r_user.rating=new_rating
                    db.session.add(r_user)
            else:
                new_rating=int(request.form.get('rating'))
                avg=new_rating/1
                total_users=1
                b_rate=Book_Rated_Users(book_id=id,user_id=current_user.id,rating=new_rating)
                db.session.add(b_rate)
        except exc.IntegrityError:
            return 'Error!'
        book.rated_users=total_users
        book.avg_rating=avg
        db.session.add(book)
        db.session.commit()
        return redirect('/sections')
    # print(sections)
    return render_template('ratings.html',book=book,x=r_user)

def accept_file(filename):
    return('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

@app.route('/upload/book', methods=['GET','POST']) #upload books C
@login_required
def upload_books():
    if current_user.role=='Admin':
        section_list=Sections.query.all()
        if request.method=='POST':
            try:
            #     if 'file' not in request.files:
            #         flash('No file part')
            #         return redirect(request.url)
            #     file = request.files['file']
            #     if file.filename == '':
            #         flash('No selected file')
            #         return redirect(request.url)
            #     if file and accept_file(file.filename):
            #         filename = secure_filename(file.filename)
            #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                name=request.form.get('name')
                content=request.form.get('content')
            #     content=os.path.join(app.config['UPLOAD_FOLDER'], filename) #!!!!!!#*****
                author=request.form.get('author')
                sec_id=request.form.get('section')
                bookx=Books(name=name,author=author,upload_on=date.today(),content=content)
                db.session.add(bookx)
                db.session.commit()
                b=Books.query.filter_by(name=name,author=author).first()
                book_sec=Books_in_Section(book_id=b.id,section_id=sec_id)
                ratex=Book_Rating(book_id=b.id)
                db.session.add(book_sec)
                db.session.add(ratex)
                db.session.commit()
                
                return redirect('/sections')
            except exc.IntegrityError:
                return 'Already exists! <div><a href="/upload/book">Try different Book</a></div>'
        return render_template('upload_books.html',section_list=section_list)
    else:
        return 'Access Denied!'

@app.route('/sections/<int:sec_id>') #books in section x
@login_required
def books_page(sec_id):
    sec_l=Books_in_Section.query.filter_by(section_id=sec_id).all()
    l=[]
    l_ids=[]
    book_access=Book_Issue_Records.query.filter_by(user_id=current_user.id).all()
    rating=Book_Rating.query.all()
    u_b=[] # all books ownedby user
    mis=[] # books not ownedby user from 'THIS' section
    for x in sec_l:
        l.append(Books.query.filter_by(id=x.book_id).first())
        if l[-1]:
            l_ids.append(l[-1].id)
    for y in book_access:
        status=timelimit(y.book_id)
        if status:
            y.status=status
            db.session.add(y)
            db.session.commit()
        u_b.append(y.book_id)
    for z in l_ids:
        if z not in u_b:
            mis.append(z)
    rating=Book_Rating.query.all()
    if rating:
        rating.sort(key=lambda x: (x.avg_rating or 0),reverse=True)
    b=[]
    for x in rating:
        for y in l:
            if x.book_id==y.id:
                b.append(y)
    return render_template('books.html',book=b,book_access=book_access,miss=mis,rating=rating)

@app.route('/book/<int:id>') #read book R
@login_required
def read_book(id):
    book=Books.query.filter_by(id=id).first()
    cont=book.content
    return render_template('read_book.html',book=book,content=cont)

@app.route('/book/update/<int:id>',methods=['GET','POST']) #update book details U
@login_required
def update_book(id):
    # book_x=Sections.query.filter_by(id=id).first()
    book=Books.query.filter_by(id=id).first()
    if request.method=='POST':
        book.name=request.form.get('name')
        book.author=request.form.get('author')
        db.session.add(book)
        db.session.commit()

        return redirect('/sections')
    return render_template('upload_books.html',book=book)

@app.route('/book/remove<id>') #confirm before deleting book
@login_required
def remove_book_confirmation(id):
    return f'<a href="/book/remove/{id}">Confirm?</a>'

@app.route('/book/remove/<int:id>') #delete book D
@login_required
def remove_book(id):
    if current_user.role=='Admin':
        bk=Books.query.get_or_404(id)
        db.session.delete(bk)
        bk_in_sec=Books_in_Section.query.filter_by(book_id=id).first()
        issuedbooks=Book_Issue_Records.query.filter_by(book_id=id).all()
        rating=Book_Rating.query.filter_by(book_id=id).first()
        ratedusers=Book_Rated_Users.query.filter_by(book_id=id).all()
        # print(ratedusers,rating,issuedbooks,bk_in_sec)
        if rating :db.session.delete(rating)
        if ratedusers: 
            for x in ratedusers:
                db.session.delete(x)
        if issuedbooks: 
            for x in issuedbooks:
                db.session.delete(x)
        if bk_in_sec: db.session.delete(bk_in_sec)
        # print(ratedusers,rating,issuedbooks,bk_in_sec)
        db.session.commit()
        return redirect('/sections')
    else:
        return 'Access Denied!'

#profile page
@app.route('/profile/<int:id>') #profile page
@login_required
def user_prof(id):
    if id==current_user.id:
        return render_template('user_info.html')
    else:
        return 'Login to your account'

#stats summary 
@app.route('/stats')
@login_required
def statistics():
    if current_user.role=='Admin':
        books=Books.query.all()
        sections=Sections.query.all()
        users=Users.query.all()
        return render_template('statistics.html',books=books,sections=sections,users=users)
    elif current_user.role=='User':
        books=Book_Issue_Records.query.filter_by(user_id=current_user.id).all()
        for y in books:
            status=timelimit(y.book_id)
            if status:
                y.status=status
                db.session.add(y)
                db.session.commit()
        for x in books:
            if x.status=='Pending':
                books.remove(x)
        return render_template('statistics.html',books=books)
    
@app.route('/requestbook/<int:book_id>') # request for a book
@login_required
def reqbook(book_id):
    b_count=Book_Issue_Records.query.filter_by(user_id=current_user.id).all()
    count=0
    valid=['Pending','Accept']
    for x in b_count:
        if x.status in valid:
            count+=1

    if count>4:
        print('Error')
        flash('Limit Exceeded!','error')
        return render_template('limit_exceeded.html')
    else:
        try:
            b=Books.query.filter_by(id=book_id).first()
            print(b.id,current_user.id)
            issuedate=datetime.now()
            validtill=issuedate+timedelta(minutes=3)
            requesting=Book_Issue_Records(book_id=b.id,user_id=current_user.id,date_of_request=issuedate,valid_upto=validtill)
            db.session.add(requesting)
            db.session.commit()
            book_rec=Book_Issue_Records.query.all()
            book=Books.query.all()
            user=Users.query.all()
        except exc.IntegrityError:
            return redirect('/review_page')
    # return render_template('/book_requests.html',book_rec=book_rec,book=book,user=user)
    return redirect('/review_page')

@app.route('/revoke_access/<id>') # return/revoke book
@login_required
def revoke_access(id):
    book_rec=Book_Issue_Records.query.filter_by(user_id=id[1],book_id=id[0]).first()
    book_rec.status='Returned'
    db.session.add(book_rec)
    # db.session.delete(book_rec)
    # print(book_rec)
    db.session.commit()
    return redirect('/review_page')

# all requests,payments,etc... in one page
@app.route('/review_page')
@login_required
def review_page():
    book_rec=Book_Issue_Records.query.all()
    book=Books.query.all()
    user=Users.query.all()
    for y in book_rec:
        status=timelimit(y.book_id)
        if status:
            y.status=status
            db.session.add(y)
            db.session.commit()
    # print(book_rec,book,user)
    user_books=[]
    for x in book_rec:
        if x.user_id==current_user.id:
            user_books.append(x)
    return render_template('request_review.html',book_rec=book_rec,book=book,user=user,user_books=user_books)

@app.route('/review/<id>',methods=['GET','POST']) #review of a book_issue_request
@login_required
def review_details(id):
    book_rec=Book_Issue_Records.query.filter_by(user_id=id[1],book_id=id[0]).first()
    if request.method=='POST':
        status=request.form.get('Status')
        book_rec.status=status
        db.session.add(book_rec)
        db.session.commit()
        return redirect('/review_page')
    return render_template('review_details.html',book_rec=book_rec)

@app.route('/payment_for/<id>') # pay to dload
@login_required
def payment_page(id):
    b=Book_Issue_Records.query.filter_by(user_id=id[1],book_id=id[0]).first()
    b.status='Paid'
    b.date_of_request=datetime.now()
    b.valid_upto=datetime.now()+timedelta(days=100)
    db.session.add(b)
    db.session.commit()
    return redirect('/review_page')

#convert to pdf
class MyPDF(FPDF):
    def __init__(self,title):
        super().__init__()
        self.title=title

    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self.title, 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Page %s" % self.page_no(), 0, 0, "C")

@app.route('/download/<id>') #download paid book
def download_book(id):
    book_rec=Book_Issue_Records.query.filter_by(user_id=id[1],book_id=id[0]).first()
    if id[1]==str(current_user.id):
        if book_rec:
            if book_rec.status=='Paid':
                book=Books.query.filter_by(id=id[0]).first()
                pdf=MyPDF(title=book.name)
                pdf.add_page()
                # pdf.header(book.name)
                pdf.set_font("Arial", size=12)
                pdf.set_title(book.name)
                pdf.set_author(book.author)
                pdf.multi_cell(0,5,book.content)
                pdf.output('static/'+book.name+'.pdf','F')
                # pdf.output(os.path.join(app.config['UPLOAD_FOLDER'], book.name+'.pdf'),'F')
                # return f'<a href="/static/{book.name}.pdf"><button class="btn btn-outline-dark">Download</button></a>'
                return redirect('/static/'+book.name+'.pdf')
            return 'Pay for it first'
        return 'Request Book!'
    # print(type(id),type(id[0]),type(id[1]))
    return 'Access Denied!'

@app.route('/search') #search funcionality
def search_func():
    search_for="%"+request.args.get('search_for')+"%"
    book_name=Books.query.filter(Books.name.like(search_for)).all()
    book_author=Books.query.filter(Books.author.like(search_for)).all()
    section_name=Sections.query.filter(Sections.name.like(search_for)).all()
    book_search=book_name+book_author
    section_search=section_name
    bk_rating=Book_Rating.query.all()
    sect_rating=Section_Ratings.query.all()
    return render_template('search_for.html',book_search=book_search,section_search=section_search,bk_rating=bk_rating,sect_rating=sect_rating)

# checking validity of book
def timelimit(book_id):
    book_issued=Book_Issue_Records.query.filter_by(book_id=book_id,user_id=current_user.id).first()
    if book_issued:
        if book_issued.valid_upto <= datetime.now():
            print(book_issued.book_id)
            print(book_issued.valid_upto)
            print(datetime.now())
            return 'Returned'
        else:
            print(book_issued.valid_upto-datetime.now())
    return ''


@app.errorhandler(401) #error handler
def unathourized(e):
    return redirect('/login')

@app.route('/logout') #loggingout user
@login_required
def log_out():
    logout_user()
    return redirect('/login')

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0')
    # app.run()
