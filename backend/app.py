from flask import Blueprint
from flask_restful import Api
from resources.Lms import LmsResource
from resources.Login import Login
from resources.Subject import Subject
from resources.Register import Register

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Routes
api.add_resource(Login, '/auth/login')
api.add_resource(Register, '/auth/register')
api.add_resource(LmsResource, '/lms')
api.add_resource(Subject, '/subject')
