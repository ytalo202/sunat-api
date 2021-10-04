from flask import Flask, jsonify, request, make_response
from sunat import ask_sunat
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import json
import argparse
from datetime import datetime, timedelta, timezone
from werkzeug.security import safe_str_cmp
from flask_jwt import JWT, jwt_required, current_identity
import logging
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_restful import reqparse
from functools import wraps

# import jwt

app = Flask(__name__)
# mysql://username:password@server/db
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/ask_sunat_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'lolxD'
# time = 20 * (60 * 24 * 365)
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=time)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(weeks=5215)
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(0)

jwt = JWTManager(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)


# class Task(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(70), unique=True)
#     description = db.Column(db.String(100))
#
#     def __init__(self, title, description):
#         self.title = title
#         self.description = description

@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username != "test" or password != "test":
        return jsonify({"msg": "Bad username or password"}), 401
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@app.route("/", methods=["GET"])
def index():
    raise ValueError('A very specific bad thing happened.')
    # Exception("Sorry, no numbers below zero")
    return jsonify({'test':'oks'})

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    string_obj_voucher = db.Column(db.String(4294000000))
    number = db.Column(db.Integer)
    ruc = db.Column(db.String(11))
    serie = db.Column(db.String(4))
    sun_document = db.Column(db.String(11))
    type = db.Column(db.Integer, default=0)
    reason_id = db.Column(db.Integer, default=0)

    # 0 tipo comienza la busqueda
    # 1 tipo encontrado
    # 2 no encontrado
    # 3 algun error
    # 4 procesando...

    def __init__(self, number, ruc, serie, sun_document, type):
        self.number = number
        self.ruc = ruc
        self.serie = serie
        self.sun_document = sun_document
        self.type = type


db.create_all()


# class TaskSchema(ma.Schema):
#     class Meta:
#         fields = ('id', 'title', 'description')

class VoucherSchema(ma.Schema):
    class Meta:
        fields = ('id', 'number', 'ruc', 'serie', 'sun_document', 'type', 'string_obj_voucher', 'reason_id')


voucher_schema = VoucherSchema()
vouchers_schema = VoucherSchema(many=True)


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'password')


users = [
    User(1, username='user1', password='abcxyz'),
    User(2, username='user2', password='abcxyz')
]

user_schema = UserSchema()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# task_schema = TaskSchema()
# tasks_schema = TaskSchema(many=True)

# @app.route('/tasks', methods=['POST'])
# def create_task():
#     title = request.json['title']
#     description = request.json['description']
#     new_task = Task(title, description)
#     db.session.add(new_task)
#     db.session.commit()
#     return task_schema.jsonify(new_task)
#
# @app.route('/tasks', methods=['GET'])
# def get_tasks():
#     tasks = Task.query.all()
#     # result = tasks_schema.dump(tasks)
#     # return jsonify(result)
#     return tasks_schema.jsonify(tasks)
#
# @app.route('/tasks/<id>', methods=['GET'])
# def get_task(id):
#     task = Task.query.get(id)
#     return task_schema.jsonify(task)
#
# @app.route('/tasks_title/<title>', methods=['GET'])
# def get_task_title(title):
#     # missing = Task.query.filter_by(description=title).first()
#     missing = Task.query.filter_by(description=title).first_or_404()
#     return task_schema.jsonify(missing)
#
#
# @app.route('/tasks/<id>', methods=['PUT'])
# def update_task(id):
#     task = Task.query.get(id)
#     title = request.json['title']
#     description = request.json['description']
#     task.title = title
#     task.description = description
#     db.session.commit()
#     return task_schema.jsonify(task)
#
# @app.route('/tasks/<id>', methods=['DELETE'])
# def delete_task(id):
#     task = Task.query.get(id)
#     db.session.delete(task)
#     db.session.commit()
#     return task_schema.jsonify(task)

def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@jwt_required
def create_dev_token():
    username = get_jwt_identity()
    expires = datetime.timedelta(days=365)
    token = create_access_token(username, expires_delta=expires)
    return jsonify({'token': token}), 201


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


jwt = JWT(app, authenticate, identity)


@app.route('/validate-voucher', methods=['POST'])
@jwt_required()
def validateVoucher():
    ruc = request.json['ruc']
    serie = request.json['serie']
    number = request.json['number']
    sun_document = request.json['sun_document']

    voucher = Voucher.query.filter_by(number=number) \
        .filter_by(serie=serie) \
        .filter_by(ruc=ruc) \
        .filter_by(sun_document=sun_document) \
        .first()

    if (voucher.type == 1) :
        voucher.string_obj_voucher = json.loads(voucher.string_obj_voucher)

    return voucher_schema.jsonify(voucher)

@app.route('/delete-voucher', methods=['POST'])
@jwt_required()
def endVoucher():
    ruc = request.json['ruc']
    serie = request.json['serie']
    number = request.json['number']
    sun_document = request.json['sun_document']

    voucher = Voucher.query.filter_by(number=number) \
        .filter_by(serie=serie) \
        .filter_by(ruc=ruc) \
        .filter_by(sun_document=sun_document) \
        .first()

    db.session.delete(voucher)
    db.session.commit()
    return jsonify({"result":"ok"})

@app.route('/ask-voucher', methods=['POST'])
@jwt_required()
def askVoucher():
    ruc = request.json['ruc']
    serie = request.json['serie']
    number = request.json['number']
    sun_document = request.json['sun_document']

    voucher = Voucher.query.filter_by(number=number) \
        .filter_by(serie=serie) \
        .filter_by(ruc=ruc) \
        .filter_by(sun_document=sun_document) \
        .first()

    if voucher is None:
        voucher = Voucher(number, ruc, serie, sun_document, 0)
        db.session.add(voucher)
        db.session.commit()

    sun_user = request.json['sun_user']
    sun_password = request.json['sun_password']

    # if voucher.type != 4 and voucher.type != 1:
    #     voucher.type = 4
    if voucher.type != 1:
        # voucher.type = 4
        # db.session.commit()
        # try:
        result = ask_sunat(ruc, serie, number, sun_document, sun_user, sun_password)
        if result['type'] == 1:
            stringify_data = json.dumps(result['data'], separators=(',', ':'))
            voucher.string_obj_voucher = stringify_data

        voucher.type = result['type']
        voucher.reason_id = result['reason_id']
        db.session.commit()
        # except Exception:
        #     voucher.type = 3
        #     db.session.commit()

    if (voucher.type == 1):
        voucher.string_obj_voucher = json.loads(voucher.string_obj_voucher)

    if (voucher.type == 4):
        voucher.type = 3
        db.session.commit()
        return jsonify({"result": "error", "message": "Procesando..."})

    return voucher_schema.jsonify(voucher)


if __name__ == '__main__':
    app.run(debug=True, port=4000)
