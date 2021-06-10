
from flask import Flask, jsonify
from webargs import fields
from webargs.flaskparser import use_args

app = Flask(__name__)
@app.route("/user/<int:uid>")
@use_args({"per_page": fields.Int()}, location="query")
def user_detail(args, uid):
    return ("The user page for user {uid}, showing {per_page} posts.").format(
        uid=uid, per_page=args["per_page"]
    )

# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code