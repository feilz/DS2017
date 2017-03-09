from flask import Blueprint

main2 = Blueprint('main', __name__)

from . import routes, events
