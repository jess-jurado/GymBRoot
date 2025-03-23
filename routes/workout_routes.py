from flask import Blueprint

workout_bp = Blueprint('workout', __name__)

@workout_bp.route('/workouts', methods=['GET'])
def get_workouts():
    return "Workouts route"
