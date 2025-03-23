from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Workout(db.Model):
    __tablename__ = 'workouts'  # Nombre de la tabla en la base de datos
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    duracion = db.Column(db.Integer, nullable=False)
    # Otros campos según sea necesario
