from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as current_app
from app.module import dbModule
from werkzeug import secure_filename
main = Blueprint('main', __name__, url_prefix='/')


@main.route('/main', methods=['GET'])
def index():
    testData = 'testData array'
    return render_template('/index.html', testDataHtml=testData)

@main.route('/video')
def video():
    return render_template()

@main.route('/video/insert')
def insert():
    f = request.files['file']
    f.save(secure_filename(f.filename))
    return redirect(url_for('main'));

@main.route('/detail')
def detail():
    return render_template()
@main.route('/select')
def select():
    db_class = dbModule.Database()
    selectQuery = "SELECT * FROM testtable"
    row = db_class.executeAll(selectQuery);

    print(row);

    return render_template('/index.html', data=row, result="hello",)
