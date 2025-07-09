from argon2 import PasswordHasher
from typehints import *

def add_faculty_info(db_connector: Connection,
					 cursor: Cursor, /, *,
					 faculty_id: Optional[int] = None,
					 phone: Optional[Union[int, str]] = None,
					 salary: Optional[float] = None,
					 password: Optional[str] = None,
					 verbose: bool = True) -> None:
	try:
		if not password:
			raise ValueError("Password is missing")
		ph: PasswordHasher = PasswordHasher()
		cursor.execute("""INSERT INTO `faculty_info`
					   VALUES (%s, %s, %s, %s)""",
					   (faculty_id, phone, salary, ph.hash(password)))
		db_connector.commit()
	except Exception as exception:
		exception: tuple = exception.args
		db_connector.rollback()
		if verbose:
			if exception[0] == 1062:
				raise IntegrityError("Faculty information already exists in `faculty_info` table.\n\
						If you want to update the information, use `update_faculty_info()` function.")
			elif exception[0] == 1452:
				raise IntegrityError("Faculty ID does not exist in `faculties` table.")
		raise ValueError("Faculty ID does not exist in `faculties` table or Faculty information already exists")

def add_section_class(db_connector: Connection,
					  cursor: Cursor, /, *,
					  section_id: Optional[int] = None,
					  class_id: Optional[int] = None) -> None:
	cursor.execute("""INSERT INTO `section_class`
				   (`section_id`, `class_id`)
				   VALUES (%s, %s)""", (section_id, class_id))
	db_connector.commit()

def add_section_student(db_connector: Connection,
						cursor: Cursor, /, *,
						section_id: Optional[int] = None,
						student_id: Optional[int] = None) -> None:
	cursor.execute("""INSERT INTO `section_students`
				   (`section_id`, `student_id`)
				   VALUES (%s, %s)""", (section_id, student_id))
	db_connector.commit()

def add_faculty_section_course(db_connector: Connection,
						cursor: Cursor, /, *,
						id: Optional[int] = None,
						faculty_id: Optional[int] = None,
						section_id: Optional[int] = None,
						course_code: Optional[str] = None) -> None:
	cursor.execute("""INSERT INTO `faculty_section_course`
				   (`id`, `faculty_id`, `section_id`, `course_code`)
				   VALUES (%s, %s, %s, %s)""",
				   (id, faculty_id, section_id, course_code))
	db_connector.commit()

def add_student_elective(db_connector: Connection,
						 cursor: Cursor, /, *,
						 student_id: Optional[int] = None,
						 course_code: Optional[str] = None) -> None:
	cursor.execute("""INSERT INTO `student_electives`
				   (`student_id`, `course_code`)
				   VALUES (%s, %s)""", (student_id, course_code))
	db_connector.commit()

def add_period(db_connector: Connection,
			   cursor: Cursor, /, *,
			   id: Optional[int] = None,
			   start_time: Optional[str] = None,
			   end_time: Optional[str] = None,
			   is_break: bool = False) -> None:
	def __add_one(start):
		hr, *min = start.split(":")
		hr = (int(hr) + 1) % 24
		return str(hr) + ":" + ":".join(min)

	if not end_time:
		end_time = __add_one(start_time)
	cursor.execute("""INSERT INTO `periods`
				   (`id`, `start_time`, `end_time`, `is_break`)
				   VALUES (%s, %s, %s, %s)""",
				   (id, start_time, end_time, is_break))
	db_connector.commit()

def add_timetable(db_connector: Connection,
				  cursor: Cursor, /, *,
				  day: Optional[str] = None,
				  period_id: Optional[int] = None,
				  faculty_section_course_id: Optional[int] = None,
				  class_id: Optional[int] = None) -> None:
	cursor.execute("""INSERT INTO `timetables`
				   (`day`, `period_id`, `faculty_section_course_id`, `class_id`)
				   VALUES (%s, %s, %s, %s)""",
				   (day, period_id, faculty_section_course_id, class_id))
	db_connector.commit()