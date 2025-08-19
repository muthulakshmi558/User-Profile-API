from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)

# --------------------
# Model
# --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}

# --------------------
# DB init + sample data (6 users)
# --------------------
def create_db_with_samples():
    db.create_all()
    if User.query.first() is None:
        samples = [
            User(name="Aarav Kumar", email="aarav.kumar@example.com"),
            User(name="Priya Sharma", email="priya.sharma@example.com"),
            User(name="Rohan Patel", email="rohan.patel@example.com"),
            User(name="Sneha Reddy", email="sneha.reddy@example.com"),
            User(name="Vikram Singh", email="vikram.singh@example.com"),
            User(name="Meera Iyer", email="meera.iyer@example.com")
        ]
        db.session.bulk_save_objects(samples)
        db.session.commit()

# ✅ Ensure DB is initialized at import (works on Render/Gunicorn too)
with app.app_context():
    create_db_with_samples()

# --------------------
# Resources / Routes
# --------------------
class UsersList(Resource):
    def get(self):
        users = User.query.all()
        return {"status": 200, "data": [u.to_dict() for u in users]}, 200

    def post(self):
        data = request.get_json()
        if not data or not data.get("name") or not data.get("email"):
            return {"status": 400, "message": "Missing 'name' or 'email' in request body"}, 400

        new_user = User(name=data["name"], email=data["email"])
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"status": 400, "message": "Email already exists"}, 400

        return {"status": 201, "message": "User created", "data": new_user.to_dict()}, 201

class UserResource(Resource):
    def get(self, id):
        user = User.query.get(id)
        if not user:
            return {"status": 404, "message": "User not found"}, 404
        return {"status": 200, "data": user.to_dict()}, 200

    def put(self, id):
        user = User.query.get(id)
        if not user:
            return {"status": 404, "message": "User not found"}, 404

        data = request.get_json()
        if not data:
            return {"status": 400, "message": "Request body required"}, 400

        if "name" in data:
            user.name = data["name"]
        if "email" in data:
            user.email = data["email"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"status": 400, "message": "Email already exists"}, 400

        return {"status": 200, "message": "User updated", "data": user.to_dict()}, 200

    def delete(self, id):
        user = User.query.get(id)
        if not user:
            return {"status": 404, "message": "User not found"}, 404
        db.session.delete(user)
        db.session.commit()
        return {"status": 200, "message": "User deleted"}, 200

# --------------------
# Home route
# --------------------
@app.route("/")
def home():
    return {
        "status": 200,
        "message": "Welcome to User Profile API 👑",
        "endpoints": {
            "GET /users": "List all users",
            "POST /users": "Create new user",
            "GET /users/<id>": "Fetch single user",
            "PUT /users/<id>": "Update user",
            "DELETE /users/<id>": "Delete user"
        }
    }

# register routes
api.add_resource(UsersList, "/users")
api.add_resource(UserResource, "/users/<int:id>")

# --------------------
# Local run
# --------------------
if __name__ == "__main__":
    app.run(debug=True)
