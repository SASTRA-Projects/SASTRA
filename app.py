from flask import Flask, make_response, redirect, render_template, request, session, url_for
from typehints import NotFound, Optional, Response, Union
import fetch_data
import mysql_connector as sql
import secrets
import show_data

app = Flask(__name__, template_folder="templates")
app.jinja_env.filters.pop("attr", None)
app.jinja_env.autoescape = True
app.secret_key = secrets.token_hex(16)

DAYS: list[str] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


@app.before_request
def check_login() -> Optional[Response]:
	if not session.get("logged_in") and request.endpoint != "login" and request.endpoint != "authenticate":
		return redirect(url_for("login"))
	return None

def nocache(view):
	def no_cache_response(*args, **kwargs):
		response = make_response(view(*args, **kwargs))
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Pragma"] = "no-cache"
		response.headers["Expires"] = "0"
		return response
	no_cache_response.__name__ = view.__name__
	return no_cache_response

@app.route("/login", methods=["GET", "POST"])
@nocache
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
						role="User")
		except Exception:
			return render_template("failed.html", reason="Unknown error occurred")
	else:
		return render_template("failed.html", reason="Login information not entered properly!")

@app.route("/faculty")
@nocache
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
												password=request.form["password"])
				session["faculty"] = True
				return redirect(url_for("show_faculty_details"))
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
		campus_id = show_data.get_campus_id(sql.cursor, campus=campus)
		if campus_id is None:
			return render_template("failed.html", reason="No such Campus found!!")
		return render_template("school.html", schools=show_data.get_schools(sql.cursor, campus_id=campus_id), campus=campus)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/school/<string:campus>/<string:school>")
def show_buildings(campus: str, school: str) -> str:
	if sql.cursor:
		campus_id = show_data.get_campus_id(sql.cursor, campus=campus)
		if campus_id is None:
			return render_template("failed.html", reason="No such Campus found!!")
		school_id = show_data.get_school_id(sql.cursor, campus_id=campus_id, school=school)
		if school_id is None:
			return render_template("failed.html", reason=f"No such School found in {campus}!")
		return render_template("building.html", buildings=show_data.get_buildings(sql.cursor, school_id=school_id), school=school)
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
		programmes = show_data.get_programmes(sql.cursor, degree=degree)
		return render_template("programme.html", programmes=programmes, degree=degree)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/programme/<string:degree>/<string:stream>")
def show_courses(degree: str, stream: str) -> str:
	if sql.cursor:
		courses = fetch_data.get_courses(sql.cursor, programme_id=show_data.get_programme_id(sql.cursor, degree=degree, stream=stream))
		return render_template("course.html", courses=courses, degree=degree, stream=stream)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/programme/<string:degree>/<string:stream>/<string:campus>")
def show_years(degree: str, stream: str, campus: str) -> str:
	if sql.cursor:
		duration = show_data.get_degree_duration(sql.cursor, degree=degree)
		if duration is None:
			return render_template("failed.html", reason="Invalid Degree or Duration not found")
		years = list(range(1, duration + 1))
		return render_template("year.html", degree=degree, stream=stream, campus=campus, years=years)
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/programme/<degree>/<stream>/<year>/<campus>")
def show_sections(degree, stream, year, campus):
    try:
        
        campus_id = show_data.get_campus_id(sql.cursor, campus=campus)        
        sections = fetch_data.get_sections(
            sql.cursor,
            degree=degree,
            stream=stream,
            campus_id=campus_id,
            year=year
        )
        return render_template(
            "section.html",
            sections=sections,
            degree=degree,
            stream=stream,
            year=year,
            campus=campus
        )
    except Exception as e:
        return f"An error occurred: {e}", 500
	
def show_timetables(section_id: int) -> str:
	if sql.cursor:
		periods= fetch_data.get_periods(sql.cursor)
		section = fetch_data.get_section(sql.cursor, section_id=section_id)
		campus = show_data.get_campus_name(sql.cursor, id=section["campus_id"])
		title = f"{campus}-{section['degree']} {section['stream'] or ''} {section['section']} (Year {section['year']})"
		for period in periods:
			period["time_range"] = f"{period['start_time']}-{period['end_time']}"
		grid = {day: {period["id"]: "" for period in periods} for day in DAYS}
		timetables = fetch_data.get_timetables(sql.cursor, section_id=section_id)
		for row in timetables:
			day = row["day"]
			period_id = row["period_id"]
			content = f"{row['course_code']}-{row['faculty_id']}({row['room_no']})"
			if row["is_lab"]:
				content += "(Lab)"
			if content:
				if grid[day][period_id]:
					grid[day][period_id] += "/"
				grid[day][period_id] += content

		course_data = {}
		for fc in timetables:
			faculty = fetch_data.get_faculty(sql.cursor, id=fc["faculty_id"])["name"]
			course_code = fc["course_code"]
			course = fetch_data.get_course(sql.cursor, code=course_code)
			if course_code not in course_data:
				course_data[course_code] = {
					"name": course["name"],
					"faculties": set(),
					"credits": course["credits"],
					"L": course["L"],
					"P": course["P"],
					"T": course["T"],
				}
			course_data[course_code]["faculties"].add(f"{faculty}({fc['faculty_id']})")

		for course in course_data.values():
			course["faculties"] = ", ".join(course["faculties"])
		return render_template("timetable.html", days=DAYS, periods=periods, grid=grid, course_data=course_data, title=title)
	return render_template("failed.html", reason="Unknown error occurred")	

@app.route("/faculty/details")
def show_faculty_details() -> str:
	if sql.cursor:
		if not session.get("faculty") or not session.get("faculty_details"):
			return render_template("failed.html", reason="Illegal access or value is missing.")
		faculty = session["faculty_details"]
		return render_template("faculty.html", faculty=faculty, campus=show_data.get_campus_name(sql.cursor, id=faculty["campus_id"]))
	return render_template("failed.html", reason="Unknown error occurred")

@app.route("/faculty/timetable")
def show_faculty_timetable() -> str:
	if sql.cursor:
		if not session.get("faculty") or not session.get("faculty_details"):
			return render_template("failed.html", reason="Illegal access or value is missing.")
		id = session["faculty_details"]["id"]
		name = fetch_data.get_faculty(sql.cursor, id=id)["name"]

		periods = fetch_data.get_periods(sql.cursor)
		for period in periods:
			period["time_range"] = f"{period['start_time']}-{period['end_time']}"

		grid = {day: {period["id"]: "" for period in periods} for day in DAYS}
		timetables = fetch_data.get_timetables(sql.cursor, faculty_id=id)
		for row in timetables:
			day = row["day"]
			period_id = row["period_id"]
			content = f"{row['course_code']}-{row['faculty_id']}({row['room_no']})"
			if row["is_lab"]:
				content += "(Lab)"
			if content:
				if grid[day][period_id]:
					grid[day][period_id] += "/"
				grid[day][period_id] += content

		course_data = {}
		for fc in timetables:
			faculty = name
			course_code = fc["course_code"]
			course = fetch_data.get_course(sql.cursor, code=course_code)
			if course_code not in course_data:
				course_data[course_code] = {
					"name": course["name"],
					"faculties": set(),
					"credits": course["credits"],
					"L": course["L"],
					"P": course["P"],
					"T": course["T"],
				}
			course_data[course_code]["faculties"].add(f"{faculty}({fc['faculty_id']})")

		for course in course_data.values():
			course["faculties"] = ", ".join(course["faculties"])

		title = "Timetable"
		return render_template("timetable.html", title=title, days=DAYS, periods=periods, grid=grid, course_data=course_data)

@app.route("/timetable/<int:section_id>")
def show_timetables(section_id: int) -> str:
	if sql.cursor:
		periods= fetch_data.get_periods(sql.cursor)
		section = fetch_data.get_section(sql.cursor, section_id=section_id)
		campus = show_data.get_campus_name(sql.cursor, id=section["campus_id"])
		title = f"{campus}-{section['degree']} {section['stream'] or ''} {section['section']} (Year {section['year']})"
		for period in periods:
			period["time_range"] = f"{period['start_time']}-{period['end_time']}"
		grid = {day: {period["id"]: "" for period in periods} for day in DAYS}
		timetables = fetch_data.get_timetables(sql.cursor, section_id=section_id)
		for row in timetables:
			day = row["day"]
			period_id = row["period_id"]
			content = f"{row['course_code']}-{row['faculty_id']}({row['room_no']})"
			if row["is_lab"]:
				content += "(Lab)"
			if content:
				if grid[day][period_id]:
					grid[day][period_id] += "/"
				grid[day][period_id] += content

		course_data = {}
		for fc in timetables:
			faculty = fetch_data.get_faculty(sql.cursor, id=fc["faculty_id"])["name"]
			course_code = fc["course_code"]
			course = fetch_data.get_course(sql.cursor, code=course_code)
			if course_code not in course_data:
				course_data[course_code] = {
					"name": course["name"],
					"faculties": set(),
					"credits": course["credits"],
					"L": course["L"],
					"P": course["P"],
					"T": course["T"],
				}
			course_data[course_code]["faculties"].add(f"{faculty}({fc['faculty_id']})")

		for course in course_data.values():
			course["faculties"] = ", ".join(course["faculties"])
		return render_template("timetable.html", days=DAYS, periods=periods, grid=grid, course_data=course_data, title=title)
	return render_template("failed.html", reason="Unknown error occurred")

@app.errorhandler(404)
def page_not_found(error: NotFound) -> tuple[str, int]:
	return (render_template("404.html"), 404)

if __name__ == "__main__":
	app.config.update(
		SESSION_COOKIE_SAMESITE="Strict",
		SESSION_COOKIE_HTTPONLY=True,
		SESSION_COOKIE_SECURE=True
	)
	app.run(host="0.0.0.0", port=5000, debug=False)
