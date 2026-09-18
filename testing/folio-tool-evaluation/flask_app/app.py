from datetime import date

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "tinyfolio-development-key"


@app.route("/", methods=["GET", "POST"])
def index():
    assignments = session.get("assignments", [])
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        due_date = request.form.get("due_date", date.today().isoformat())
        priority = request.form.get("priority", "Low")

        if not name:
            error = "Assignment name is required."
        else:
            session["assignments"] = assignments + [
                {
                    "name": name,
                    "due_date": due_date,
                    "priority": priority,
                }
            ]
            return redirect(url_for("index"))

    return render_template(
        "index.html",
        assignments=assignments,
        error=error,
        today=date.today().isoformat(),
    )


if __name__ == "__main__":
    app.run(debug=True)
