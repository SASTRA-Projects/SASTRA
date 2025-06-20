from flask import Flask, redirect, render_template, request, session, url_for
from typehints import *
import secrets
import show_data
import fetch_data
import mysql_connector as sql

app: Flask = Flask(__name__, template_folder="templates")
app.jinja_env.filters.pop("attr", None)
app.jinja_env.autoescape = True
app.secret_key = secrets.token_hex(16)

@app.before_request
def check_login() -> Optional[Response]:
	if not session.get("logged_in") and request.endpoint != "login" and request.endpoint != "authenticate":
		return redirect(url_for("login"))
	return None

@app.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
	if request.method == "GET":
		if session.get("logged_in"):
			return redirect(url_for("index"))
		else:
			return render_template("login.html", user="User", auth="/login", role="User")

	elif request.form.get("user") and request.form.get("password"):
		try:
			sql.connect(user=request.form["user"], password=request.form["password"])
			import views
			import triggers
			if sql.db_connector and sql.cursor:
				views.create_views(sql.db_connector, sql.cursor)
				triggers.create_triggers(sql.db_connector, sql.cursor)
				session["logged_in"] = True
			return redirect(url_for("index"))
		except sql.pymysql.err.OperationalError:
			return render_template("login.html",
						user="User",
						auth="/authenticate",
						error_message="Invalid username or password",
						role="User"
				)
		except Exception:
			return render_template("failed.html", reason="Unknown error occurred")
	else:
		return render_template("failed.html", reason="Login information not entered properly!")

@app.route("/faculty")
def log_faculty() -> Union[Response, str]:
	if not session.get("faculty") or not session.get("faculty_details"):
		return render_template("login.html", user="ID", userType="number", auth="/auth_faculty", role="faculty")
	return redirect(url_for("faculty_details"))

@app.route("/auth_faculty", methods=["POST"])
def auth_faculty() -> Union[Response, str]:
	if request.form.get("user") and request.form.get("password"):
		try:
			if sql.cursor:
				session["faculty_details"] = fetch_data.get_faculty_details(
												sql.cursor,
												id=int(request.form["user"]),
												password=request.form["password"]
											)
				session["faculty"] = True
				return redirect(url_for("faculty_details"))
			return render_template("failed.html", reason="Unauthorized Login!")
		except AssertionError:
			return render_template("login.html", user="ID", userType="number", auth="/auth_faculty", role="faculty", error_message="Invalid ID or Password")
		except Exception:
			return render_template("login.html", user="ID", userType="number", auth="/auth_faculty", role="faculty", error_message="Invalid ID")
	return render_template("failed.html", reason="Login information not entered properly!")

@app.route("/home")
@app.route("/")
def index() -> str:
	return render_template("index.html")

@app.route("/about")
def about() -> str:
	return render_template("about.html")

@app.route("/campus")
def show_campuses() -> str:
	if sql.cursor:
		return render_template("campus.html", campuses=show_data.get_campuses(sql.cursor))
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/campus/<string:campus>")
def show_schools(campus: str) -> str:
	if sql.cursor:
		campus_id: Optional[int] = show_data.get_campus_id(sql.cursor, campus=campus)
		if campus_id is None:
			return render_template("failed.html", reason="No such Campus found!!")
		return render_template("school.html", schools=show_data.get_schools(sql.cursor, campus_id=campus_id), campus=campus)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/school/<string:campus>/<string:school>")
def show_buildings(campus: str, school: str) -> str:
	if sql.cursor:
		campus_id: Optional[int] = show_data.get_campus_id(sql.cursor, campus=campus)
		if campus_id is None:
			return render_template("failed.html", reason="No such Campus found!!")
		school_id: Optional[int] = show_data.get_school_id(sql.cursor, campus_id=campus_id, school=school)
		if school_id is None:
			return render_template("failed.html", reason=f"No such School found in {campus}!")
		return render_template("building.html", buildings=show_data.get_buildings(sql.cursor, school_id=school_id), school=school)
	return render_template("failed.html", reason="Unknown error occurred")

#@app.route("/department")
#def show_departments() -> str:
	if sql.cursor:
		return render_template("department.html", departments=show_data.get_departments(sql.cursor))
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/degree")
def show_degrees() -> str:
	if sql.cursor:
		return render_template("degree.html", degrees=show_data.get_degrees(sql.cursor))
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/programme")
def show_programmes() -> str:
	if sql.cursor:
		return render_template("programme.html", programmes=show_data.get_programmes(sql.cursor))
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/degree/<string:degree>")
def show_degree_programmes(degree: str) -> str:
	if sql.cursor:
		programmes: Tuple[Optional[Dict[str, str]], ...] = show_data.get_programmes(sql.cursor, degree=degree)
		return render_template("programme.html", programmes=programmes, degree=degree)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/programme/<string:degree>/<string:stream>/<int:programme_id>")
def show_programme_courses(degree: str, stream: str, programme_id: int):
    if not sql.cursor:
        return render_template("failed.html", reason="Unknown error occurred")
    programme = show_data.get_programme(sql.cursor, programme_id=programme_id)
    courses = fetch_data.get_courses_by_programme(sql.cursor, programme_id=programme_id)
    return render_template("course.html", programme=f"{degree} - {stream}", courses=courses)

@app.route("/faculty/details")
def faculty_details() -> str:
	if sql.cursor:
		if not session.get("faculty") or not session.get("faculty_details"):
			raise ValueError("Illegal access or value is missing.")
		faculty = session["faculty_details"]
		return render_template("faculty.html", faculty=faculty, campus=show_data.get_campus_name(sql.cursor, id=faculty["campus_id"]))
	return render_template("failed.html", reason="Unknown error occurred")

@app.errorhandler(404)
def page_not_found(error: NotFound) -> tuple[str, int]:
	return (render_template("404.html"), 404)

if __name__ == "__main__":
	app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
	app.config['SESSION_COOKIE_HTTPONLY'] = True
	app.config['SESSION_COOKIE_SECURE'] = True

	app.config.update(SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPSONLY=True)
	app.run(host="0.0.0.0", port=5000, debug=False)
