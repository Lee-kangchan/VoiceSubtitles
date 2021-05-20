from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as current_app
from app.module import dbModule
main = Blueprint('main', __name__, url_prefix='/user')

@main.route('/login', methods = ['GET'])
def login(request):
  return render_template('/login.html')

@main.route('/login', methods = ['POST'])
def login2(request):

    db_class = dbModule.Database()
    selectQuery = "SELECT id FROM user where id = ? and password = ? "
    row = db_class.executeAll(selectQuery);
    return redirect(url_for('main'))
