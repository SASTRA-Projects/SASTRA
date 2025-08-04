from argon2 import PasswordHasher, exceptions
from typehints import Cursor, Dict, Optional, Tuple, Union

"""
Shows the data for tables,
for which data will change frequently.
"""
def get_courses(cursor: Cursor, /, *,
                programme_id: Optional[int] = None,
                elective: Optional[bool] = None,
                lab: Optional[bool] = None) -> Tuple[Dict[str, Union[bool, int, str]], ...]:
    if programme_id:
        if elective is None and lab is None:
            cursor.execute("""SELECT `code`, `name`,
                           `department`, `credits`,
                           `L`, `P`, `T`, `is_elective`
                           FROM `courses`
                           JOIN `programme_courses`
                           ON `code`=`course_code`
                           AND `programme_id`=%s""", (programme_id,))
        elif lab is None:
            cursor.execute("""SELECT `code`, `name`,
                           `department`, `credits`,
                           `L`, `P`, `T`
                           FROM `courses`
                           JOIN `programme_courses`
                           ON `code`=`course_code`
                           AND `programme_id`=%s
                           AND `is_elective`=%s""", (programme_id, elective,))
        elif elective is None:
            cursor.execute("""SELECT *
                           FROM `courses`
                           JOIN `programme_courses`
                           ON `code`=`course_code`
                           AND `programme_id`=%s
                           AND `P` > %s
                           AND `P` < %s""", ((programme_id,) + ((0, 256) if lab else (-1, 1))))
        else:
            cursor.execute("""SELECT `code`, `name`,
                           `department`, `credits`,
                           `L`, `P`, `T`
                           FROM `courses`
                           JOIN `programme_courses`
                           ON `code`=`course_code`
                           AND `programme_id`=%s
                           AND `P` > %s
                           AND `P` < %s
                           AND `is_elective`=%s""", ((programme_id,) + ((0, 256) if lab else (-1, 1)) + (elective,)))
    elif lab is None:
        cursor.execute("""SELECT * FROM `courses`""")
    elif lab:
        cursor.execute("""SELECT * FROM `courses`
                        WHERE `P` > %s""", (0,))
    else:
        cursor.execute("""SELECT * FROM `courses`
                        WHERE `P`=%s""", (0,))
    return cursor.fetchall()

def get_lab_departments(cursor: Cursor, /, *,
                        course_code: Optional[str] = None,
                        programme_id: Optional[int] = None,
                        elective: Optional[bool] = None) -> Tuple[Dict[str, str], ...]:
    if course_code:
        if programme_id:
            if elective is not None:
                cursor.execute("""SELECT `name`, `credits`, `L`, `P`, `T`,
                               IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                               `courses`.`department` AS `course_department`
                               FROM `lab_departments` `LD`
                               RIGHT JOIN `courses`
                               ON `LD`.`course_code`=`code`
                               JOIN `programme_courses` `PC`
                               ON `code`=`PC`.`course_code`
                               WHERE `P` > 0
                               AND `code`=%s
                               AND `programme_id`=%s
                               AND `is_elective`=%s""",
                               (course_code, programme_id, elective))
            else:
                cursor.execute("""SELECT `name`, `credits`,
                               `L`, `P`, `T`, `is_elective`,
                               IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                               `courses`.`department` AS `course_department`
                               FROM `lab_departments` `LD`
                               RIGHT JOIN `courses`
                               ON `LD`.`course_code`=`code`
                               JOIN `programme_courses` `PC`
                               ON `code`=`PC`.`course_code`
                               WHERE `P` > 0
                               AND `code`=%s
                               AND `programme_id`=%s""",
                               (course_code, programme_id))
        else:
            cursor.execute("""SELECT `name`, `credits`, `L`, `P`, `T`,
                           IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                           `courses`.`department` AS `course_department`
                           FROM `lab_departments` `LD`
                           RIGHT JOIN `courses`
                           ON `LD`.`course_code`=`code`
                           WHERE `P` > 0
                           AND `code`=%s""", (course_code,))
        courses = cursor.fetchall()
        if not courses:
            return courses
        else:
            courses[0]["lab_departments"] = [courses[0]["lab_department"]]
            courses[0].pop("lab_department")
        for course in courses[1:]:
            courses[0]["lab_departments"].append(course["lab_department"])
            courses.remove(course)
        return courses

    elif programme_id:
        if elective is not None:
            cursor.execute("""SELECT `code`, `name`, `credits`, `L`, `P`, `T`,
                           IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                           `courses`.`department` AS `course_department`
                           FROM `lab_departments` `LD`
                           RIGHT JOIN `courses`
                           ON `LD`.`course_code`=`code`
                           JOIN `programme_courses` `PC`
                           ON `code`=`PC`.`course_code`
                           WHERE `P` > 0
                           AND `programme_id`=%s
                           AND `is_elective`=%s""", (programme_id, elective))
        else:
            cursor.execute("""SELECT `code`, `name`, `credits`, `L`, `P`, `T`,
                           `is_elective`, IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                           `courses`.`department` AS `course_department`
                           FROM `lab_departments` `LD`
                           RIGHT JOIN `courses`
                           ON `LD`.`course_code`=`code`
                           JOIN `programme_courses` `PC`
                           ON `code`=`PC`.`course_code`
                           WHERE `P` > 0
                           AND `programme_id`=%s""", (programme_id,))
    else:
        cursor.execute("""SELECT `code`, `name`, `credits`, `L`, `P`, `T`,
                       IFNULL(`LD`.`department`, `courses`.`department`) AS `lab_department`,
                       `courses`.`department` AS `course_department`
                       FROM `lab_departments` `LD`
                       RIGHT JOIN `courses`
                       ON `course_code`=`code`
                       WHERE `P` > 0""")
    courses = cursor.fetchall()
    for course in courses:
        course["lab_departments"] = [course["lab_department"]]
        course.pop("lab_department")
        for c in courses:
            if course["code"] == c["code"] and c != course:
                course["lab_departments"].append(c["lab_department"])
                courses.remove(c)
    return courses

def get_course(cursor: Cursor, /, *,
               code: Optional[str] = None) -> Optional[Dict[str, Union[bool, int, str]]]:
    cursor.execute("""SELECT `name`, `department`,
                   `credits`, `L`, `P`, `T`
                   FROM `courses`
                   WHERE `code`=%s""", (code,))
    return cursor.fetchone()

def get_programme_campuses(cursor, degree: str, stream: str):
    cursor.execute("""
        SELECT DISTINCT campuses.name
        FROM programmes
        JOIN campuses ON programmes.campus_id = campuses.id
        WHERE programmes.degree = %s AND programmes.stream = %s
    """, (degree, stream))
    return [row[0] for row in cursor.fetchall()]

def get_programme_courses(cursor: Cursor, /, *,
                          campus_id: Optional[int] = None,
                          programme_id: Optional[int] = None,
                          course_code: Optional[str] = None) -> Union[Tuple[Dict[str, Union[str, int]]], bool]:
    if campus_id:
        if programme_id:
            if course_code:
                cursor.execute("""SELECT 1
                               FROM `programme_courses` `PC`
                               JOIN `programmes`
                               ON `programmes`.`id`=`PC`.`programme_id`
                               AND `campus_id`=%s
                               AND `programme_id`=%s
                               AND `course_code`=%s
                               LIMIT 1""",
                               (campus_id, programme_id, course_code))
                return True if cursor.fetchone() else False
            else:
                cursor.execute("""SELECT `course_code`
                               FROM `programme_courses` `PC`
                               JOIN `programmes`
                               ON `programmes`.`id`=`PC`.`programme_id`
                               AND `campus_id`=%s
                               AND `programme_id`=%s""",
                               (campus_id, programme_id))
        elif course_code:
            cursor.execute("""SELECT `programme_id`
                           FROM `programme_courses` `PC`
                           JOIN `programmes`
                           ON `programmes`.`id`=`PC`.`programme_id`
                           AND `campus_id`=%s
                           AND `course_code`=%s""",
                           (campus_id, course_code))
        else:
            cursor.execute("""SELECT `programme_id`, `course_code`
                           FROM `programme_courses` `PC`
                           JOIN `programmes`
                           ON `programmes`.`id`=`PC`.`programme_id`
                           AND `campus_id`=%s""",
                           (campus_id,))
    elif programme_id:
        if course_code:
            cursor.execute("""SELECT 1
                          FROM `programme_courses`
                          AND `programme_id`=%s
                          AND `course_code`=%s
                          LIMIT 1""",
                          (programme_id, course_code))
            return True if cursor.fetchone() else False
        else:
            cursor.execute("""SELECT `course_code`
                           FROM `programme_courses`
                           WHERE `programme_id`=%s""", (programme_id,))
    elif course_code:
        cursor.execute("""SELECT `programme_id`
                       FROM `programme_courses`
                       WHERE `course_code`=%s""", (course_code,))
    else:
        cursor.execute("""SELECT * FROM `programme_courses`""")
    return cursor.fetchall()

def get_classes(cursor: Cursor, /, *,
                campus_id: Optional[int] = None,
                building_id: Optional[int] = None,
                lab: Optional[bool] = None,
                department: Optional[str] = None,
                section_id: Optional[int] = None) -> Tuple[Dict[str, Union[bool, int]], ...]:
    if section_id:
        cursor.execute("""SELECT `classes`.`id` AS `id`, `room_no`, `capacity`
                       FROM `section_class`
                       JOIN `classes`
                       ON `class_id`=`classes`.`id`
                       AND `section_id`=%s""", (section_id,))
    elif building_id:
        if lab is not None:
            if department:
                cursor.execute("""SELECT `id`, `room_no`, `capacity`
                               FROM `classes`
                               WHERE `is_lab`=%s
                               AND `building_id`=%s
                               AND `department`=%s""",
                               (lab, building_id, department))
            else:
                cursor.execute("""SELECT `id`, `room_no`, `capacity`, `department`
                               FROM `classes`
                               WHERE `is_lab`=%s
                               AND `building_id`=%s""",
                               (lab, building_id))
        else:
            cursor.execute("""SELECT `id`, `room_no`, `capacity`, `is_lab`
                           FROM `classes`
                           WHERE `building_id`=%s""", (building_id,))
    elif campus_id:
        if lab is not None:
            if department:
                cursor.execute("""SELECT `id`, `room_no`, `capacity`
                               FROM `classes`
                               NATURAL JOIN `campus_buildings`
                               WHERE `is_lab`=%s
                               AND `campus_id`=%s
                               AND `department`=%s""",
                               (lab, campus_id, department))
            else:
                cursor.execute("""SELECT `id`, `room_no`, `capacity`, `department`
                               FROM `classes`
                               NATURAL JOIN `campus_buildings`
                               WHERE `is_lab`=%s
                               AND `campus_id`=%s""",
                               (lab, campus_id))
        else:
            cursor.execute("""SELECT `id`, `room_no`, `capacity`, `is_lab`
                           FROM `classes`
                           NATURAL JOIN `campus_buildings`
                           WHERE `campus_id`=%s""", (campus_id,))
    elif lab is not None:
        if department:
            cursor.execute("""SELECT `id`, `building_id`, `room_no`, `capacity`
                        FROM `classes`
                        WHERE `is_lab`=%s
                        AND `department`=%s""", (lab, department))
        else:
            cursor.execute("""SELECT `id`, `building_id`,
                        `room_no`, `capacity`, `department`
                        FROM `classes`
                        WHERE `is_lab`=%s""", (lab,))
    else:
        cursor.execute("""SELECT * FROM `classes`""")
    return cursor.fetchall()

def get_class(cursor: Cursor, /, *,
              class_id: Optional[int] = None) -> Optional[Dict[str, Union[bool, int]]]:
    cursor.execute("""SELECT `building_id`, `room_no`,
                   `capacity`, `is_lab`, `department`
                   FROM `classes`
                   WHERE `id`=%s""", (class_id,))
    return cursor.fetchone()

def get_sections(cursor: Cursor, /, *,
                 campus_id: Optional[int] = None,
                 degree: Optional[str] = None,
                 stream: Optional[str] = None,
                 year: Optional[int] = None) -> Tuple[Dict[str, Union[int, str]], ...]:
    if campus_id:
        if degree:
            if stream:
                if year:
                    cursor.execute("""SELECT `id`, `section`
                                   FROM `sections`
                                   WHERE `campus_id`=%s
                                   AND `degree`=%s
                                   AND `stream`=%s
                                   AND `year`=%s""",
                                   (campus_id, degree, stream, year))
                else:
                    cursor.execute("""SELECT `id`, `year`, `section`
                                   FROM `sections`
                                   WHERE `campus_id`=%s
                                   AND `degree`=%s
                                   AND `stream`=%s""",
                                   (campus_id, degree, stream))
            elif year:
                cursor.execute("""SELECT `id`, `stream`, `section`
                               FROM `sections`
                               WHERE `campus_id`=%s
                               AND `degree`=%s
                               AND `year`=%s""",
                               (campus_id, degree, year))
            else:
                cursor.execute("""SELECT `id`, `stream`, `year`, `section`
                               FROM `sections`
                               WHERE `campus_id`=%s
                               AND `degree`=%s""",
                               (campus_id, degree))
        elif stream:
            if year:
                cursor.execute("""SELECT `id`, `degree`, `section`
                               FROM `sections`
                               WHERE `campus_id`=%s
                               AND `stream`=%s
                               AND `year`=%s""",
                               (campus_id, stream, year))
            else:
                cursor.execute("""SELECT `id`, `degree`, `year`, `section`
                               FROM `sections`
                               WHERE `campus_id`=%s
                               AND `stream`=%s""",
                               (campus_id, stream))
        elif year:
            cursor.execute("""SELECT `id`, `degree`, `stream`, `section`
                           FROM `sections`
                           WHERE `campus_id`=%s
                           AND `year`=%s""",
                           (campus_id, year))
        else:
            cursor.execute("""SELECT `id`, `degree`,
                           `stream`, `year`, `section`
                           FROM `sections`
                           WHERE `campus_id`=%s""",
                           (campus_id,))
    elif degree:
        if stream:
            if year:
                cursor.execute("""SELECT `id`, `campus_id`, `section`
                               FROM `sections`
                               WHERE `degree`=%s
                               AND `stream`=%s
                               AND `year`=%s""",
                               (degree, stream, year))
            else:
                cursor.execute("""SELECT `id`, `campus_id`,
                               `year`, `section`
                               FROM `sections`
                               WHERE `degree`=%s
                               AND `stream`=%s""",
                               (degree, stream))
        elif year:
            cursor.execute("""SELECT `id`, `campus_id`,
                           `stream`, `section`
                           FROM `sections`
                           WHERE `degree`=%s
                           AND `year`=%s""",
                           (degree, year))
        else:
            cursor.execute("""SELECT `id`, `campus_id`,
                           `stream`, `year`, `section`
                           FROM `sections`
                           WHERE `degree`=%s""",
                           (degree,))
    elif stream:
        if year:
            cursor.execute("""SELECT `id`, `campus_id`,
                           `degree`, `section`
                           FROM `sections`
                           WHERE `stream`=%s
                           AND `year`=%s""",
                           (stream, year))
        else:
            cursor.execute("""SELECT `id`, `campus_id`,
                           `degree`, `year`, `section`
                           FROM `sections`
                           WHERE `stream`=%s""",
                           (stream,))
    elif year:
        cursor.execute("""SELECT `id`, `campus_id`,
                       `degree`, `stream`, `section`
                       FROM `sections`
                       WHERE `year`=%s""",
                       (year,))
    else:
        cursor.execute("""SELECT * FROM `sections`""")
    return cursor.fetchall()

def get_section(cursor: Cursor, /, *,
                section_id: Optional[int] = None) -> Optional[Dict[str, Union[bool, int]]]:
    cursor.execute("""SELECT `campus_id`, `degree`, `stream`,
                   `year`, `section`
                   FROM `sections`
                   WHERE `id`=%s""", (section_id,))
    return cursor.fetchone()

def get_section_id(cursor: Cursor, /, *,
                   campus_id: Optional[int] = None,
                   degree: Optional[str] = None,
                   stream: Optional[str] = None,
                   year: Optional[int] = None,
                   section: Optional[str] = None) -> Optional[int]:
    sections = get_sections(cursor, campus_id=campus_id, degree=degree, stream=stream, year=year)
    if not (sections and campus_id and degree and stream and year and section):
        return None

    for s in sections:
        if s["section"] == section and isinstance(s["id"], int):
            return s["id"]
    return None

def get_section_classes(cursor: Cursor, /, *,
                        section_id: Optional[int] = None,
                        class_id: Optional[int] = None) -> Tuple[Union[bool, Dict[str, Union[int, str]], ...]]:
    if section_id:
        if class_id:
            cursor.execute("""SELECT 1
                           FROM `section_class`
                           WHERE `section_id`=%s
                           AND `class_id`=%s
                           LIMIT 1""", (section_id, class_id))
            return (True,) if cursor.fetchone() else (False,)

        else:
            cursor.execute("""SELECT `class_id`
                           FROM `section_class`
                           WHERE `section_id`=%s
                           LIMIT 1""", (section_id,))
    else:
        if class_id:
            cursor.execute("""SELECT `section_id`
                           FROM `section_class`
                           WHERE `class_id`=%s
                           LIMIT 1""", (class_id,))
        else:
            cursor.execute("""SELECT `section_id`, `class_id`
                           FROM `section_class`""")
    return cursor.fetchall()

def is_elective(cursor: Cursor, /, *,
                course_code: Optional[str] = None,
                section_id: Optional[int] = None) -> bool:
    cursor.execute("""SELECT `get_is_elective`(%s, %s) AS `is_elective`""",
                   (course_code, section_id))
    is_elective = cursor.fetchone()
    return is_elective["is_elective"] if is_elective else False

def get_faculties(cursor: Cursor, /, *,
                  campus_id: Optional[int] = None,
                  department: Optional[str] = None) -> Tuple[Dict[str, Union[int, str]], ...]:
    if campus_id:
        if department:
            cursor.execute("""SELECT `id`, `name`, `join_year`
                           FROM `faculties`
                           WHERE `campus_id`=%s
                           AND `department`=%s""", (campus_id, department))
        else:
            cursor.execute("""SELECT `id`, `name`, `department`, `join_year`
                           FROM `faculties`
                           WHERE `campus_id`=%s""", (campus_id,))
    elif department:
        cursor.execute("""SELECT  `id`, `name`, `campus_id`, `join_year`
                       FROM `faculties`
                       WHERE `department`=%s""", (department,))
    else:
        cursor.execute("""SELECT * FROM `faculties`""")
    return cursor.fetchall()

def get_faculty(cursor: Cursor, /, *,
                id: Optional[int] = None) -> Optional[Dict[str, Union[int, str]]]:
	cursor.execute("""SELECT `name` FROM `faculties`
				   WHERE `id`=%s""", (id,))
	return cursor.fetchone()

def get_faculty_id(cursor: Cursor, /, *,
                   campus_id: Optional[int] = None,
                   department: Optional[str] = None,
                   name: Optional[str] = None,
                   join_year: Optional[int] = None,
                   section_id: Optional[int] = None,
                   course_code: Optional[str] = None,
                   faculty_section_course_code: Optional[str] = None) -> Optional[Tuple[int]]:
    if section_id and course_code:
        cursor.execute("""SELECT `faculty_id` AS `id`
                       FROM `faculty_section_course`
                       WHERE `section_id`=%s
                       AND `course_code`=%s""", (section_id, course_code))
    elif faculty_section_course_code:
        cursor.execute("""SELECT `faculty_id` AS `id`
                       FROM `faculty_section_course` `FTC`
                       WHERE `FTC`.`id`=%s""", (faculty_section_course_code,))
    elif campus_id:
        if department:
            if name:
                if join_year:
                    cursor.execute("""SELECT `id`
                                   FROM `faculties`
                                   WHERE `campus_id`=%s
                                   AND `department`=%s
                                   AND `name`=%s
                                   AND `join_year`=%s""",
                                   (campus_id, department, name, join_year))
                else:
                    cursor.execute("""SELECT `id`
                                   FROM `faculties`
                                   WHERE `campus_id`=%s
                                   AND `department`=%s
                                   AND `name`=%s""",
                                   (campus_id, department, name))
            elif join_year:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `campus_id`=%s
                                AND `department`=%s
                                AND `join_year`=%s""",
                                (campus_id, department, join_year))
            else:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `campus_id`=%s
                                AND `department`=%s""",
                                (campus_id, department))
        elif name:
            if join_year:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `campus_id`=%s
                                AND `name`=%s
                                AND `join_year`=%s""",
                                (campus_id, name, join_year))
            else:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `campus_id`=%s
                                AND `name`=%s""",
                                (campus_id, name))
        elif join_year:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `campus_id`=%s
                            AND `join_year`=%s""",
                            (campus_id, join_year))
        else:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `campus_id`=%s""",
                            (campus_id,))
    elif department:
        if name:
            if join_year:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `department`=%s
                                AND `name`=%s
                                AND `join_year`=%s""",
                                (department, name, join_year))
            else:
                cursor.execute("""SELECT `id`
                                FROM `faculties`
                                WHERE `department`=%s
                                AND `name`=%s""",
                                (department, name))
        elif join_year:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `department`=%s
                            AND `join_year`=%s""",
                            (department, join_year))
        else:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `department`=%s""",
                            (department,))
    elif name:
        if join_year:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `name`=%s
                            AND `join_year`=%s""",
                            (name, join_year))
        else:
            cursor.execute("""SELECT `id`
                            FROM `faculties`
                            WHERE `name`=%s""",
                            (name,))
    elif join_year:
        cursor.execute("""SELECT `id`
                        FROM `faculties`
                        WHERE `join_year`=%s""",
                        (join_year,))
    else:
        cursor.execute("""SELECT `id` FROM `faculties`""")
    faculties = cursor.fetchall()
    if not faculties:
        return None
    return [faculty["id"] for faculty in faculties]

def get_students(cursor: Cursor, /, *,
                 campus_id: Optional[int] = None,
                 programme_id: Optional[int] = None) -> Tuple[Dict[str, Union[int, str]], ...]:
    if campus_id:
        if programme_id:
            cursor.execute("""SELECT `id`, `name`, `join_year`, `phone`
                           FROM `students`
                           WHERE `campus_id`=%s
                           AND `programme_id`=%s""", (campus_id, programme_id))
        else:
            cursor.execute("""SELECT `id`, `name`, `programme_id`, `join_year`, `phone`
                           FROM `students`
                           WHERE `campus_id`=%s""", (campus_id,))
    elif programme_id:
        cursor.execute("""SELECT  `id`, `name`, `campus_id`, `join_year`, `phone`
                       FROM `students`
                       WHERE `programme_id`=%s""", (programme_id,))
    cursor.execute("""SELECT * FROM `students`""")
    return cursor.fetchall()

def get_student(cursor: Cursor, /, *,
                id: Optional[int] = None,
                campus_id=None,
                join_year=None,
                programme_id=None,
                roll_no: Optional[int] = None) -> Optional[Dict[str, Union[int, str]]]:
    if id:
        cursor.execute("""SELECT `name` FROM `students`
				       WHERE `id`=%s""", (id,))
    else:
    	cursor.execute("""SELECT `name` FROM `students`
                       WHERE `campus_id`=%s
                       AND `join_id`=%s
                       AND `programme_id`=%s
                       AND `roll_no`=%s""",
                       (campus_id, join_year, programme_id, roll_no))
    return cursor.fetchone()

def get_faculty_details(cursor: Cursor, /, *,
                        id: Optional[int] = None,
                        password: Optional[str] = None) -> Optional[Dict[str, Union[float, int, str]]]:
    try:
        if isinstance(password, str) and password:
            cursor.execute("""SELECT * FROM `faculty_view`
                           WHERE `id`=%s""", (id,))
            faculty: Optional[Dict[str, Union[float, int, str]]] = cursor.fetchone()
            if faculty:
                pwd: Union[float, int, str] = faculty["password"]

            ph = PasswordHasher()
            ph.verify(pwd, password)
        else:
            raise ValueError("Password must be a non-empty string")

    except exceptions.VerifyMismatchError:
        if faculty and pwd:
            raise AssertionError("Incorrect Password")
    return faculty

def get_section_minor_electives(cursor: Cursor, /, *,
                                campus_id: Optional[int] = None,
                                section_id: Optional[int] = None,
                                course_code: Optional[str] = None) -> Tuple[Dict[str, Union[int, str]], ...]:
    if campus_id:
        cursor.execute("""SELECT `section_id`, `course_code`
                       FROM `section_minor_electives`
                       JOIN `sections`
                       ON `section_id`=`sections`.`id`
                       AND `campus_id`=%s""", (campus_id,))
    elif section_id:
        cursor.execute("""SELECT `course_code`
                       FROM `section_minor_electives`
                       WHERE `section_id`=%s""", (section_id,))
    elif course_code:
        cursor.execute("""SELECT `section_id`
                       FROM `section_minor_electives`
                       WHERE `course_code`=%s""", (course_code,))
    else:
        cursor.execute("""SELECT * FROM `section_minor_electives`""")
    return cursor.fetchall()

def get_section_students(cursor: Cursor, /, *,
                         section_id: Optional[int] = None,
                         student_id: Optional[int] = None) -> Tuple[Dict[str, int], ...]:
    if section_id:
        cursor.execute("""SELECT `student_id`
                       FROM `section_students`
                       WHERE `section_id`=%s""", (section_id,))
    elif student_id:
        cursor.execute("""SELECT `section_id`
                       FROM `section_students`
                       WHERE `student_id`=%s""", (student_id,))
    else:
        cursor.execute("""SELECT * FROM `section_students`""")
    return cursor.fetchall()

def get_faculty_section_courses(cursor: Cursor, /, *,
                               faculty_id: Optional[int] = None,
                               section_id: Optional[int] = None,
                               course_code: Optional[str] = None) -> Tuple[Dict[str, Union[int, str]], ...]:
    if faculty_id and section_id and course_code:
        cursor.execute("""SELECT `id`, `section_id`, `course_code`
                       FROM `faculty_section_course`
                       WHERE `faculty_id`=%s
                       AND `section_id`=%s
                       AND `course_code`=%s""",
                       (faculty_id, section_id, course_code))
    elif faculty_id and section_id:
        cursor.execute("""SELECT `id`, `course_code`
                       FROM `faculty_section_course`
                       WHERE `faculty_id`=%s
                       AND `section_id`=%s""",
                       (faculty_id, section_id))
    elif faculty_id and course_code:
        cursor.execute("""SELECT `id`, `section_id`
                       FROM `faculty_section_course`
                       WHERE `faculty_id`=%s
                       AND `course_code`=%s""",
                       (faculty_id, course_code))
    elif section_id and course_code:
        cursor.execute("""SELECT `id`, `faculty_id`
                       FROM `faculty_section_course`
                       WHERE `section_id`=%s
                       AND `course_code`=%s""",
                       (section_id, course_code))
    elif faculty_id:
        cursor.execute("""SELECT `id`, `section_id`, `course_code`
                       FROM `faculty_section_course`
                       WHERE `faculty_id`=%s""", (faculty_id,))
    elif section_id:
        cursor.execute("""SELECT `id`, `faculty_id`, `course_code`
                       FROM `faculty_section_course`
                       WHERE `section_id`=%s""", (section_id,))
    elif course_code:
        cursor.execute("""SELECT `id`, `faculty_id`, `section_id`
                       FROM `faculty_section_course`
                       WHERE `course_code`=%s""", (course_code,))
    else:
        cursor.execute("""SELECT * FROM `faculty_section_course`""")
    return cursor.fetchall()

def get_faculty_section_course(cursor: Cursor, /, *,
                               faculty_section_courses_id: Optional[int] = None) -> Optional[Dict[str, Union[int, str]]]:
    cursor.execute("""SELECT `faculty_id`, `sectio_id`, `course_code`
                   FROM `faculty_section_courses`
                   WHERE `id`=%s""", (faculty_section_courses_id,))
    return cursor.fetchall()

def get_student_electives(cursor: Cursor, /, *,
                          student_id: Optional[int] = None,
                          course_code: Optional[str] = None):
    if student_id:
        if course_code:
            cursor.execute("""SELECT 1
                           FROM `student_electives`
                           WHERE `student_id`=%s
                           AND `course_code`=%s
                           LIMIT 1""", (student_id, course_code))
            return True if cursor.fetchone() else False
        else:
            cursor.execute("""SELECT `course_code`
                           FROM `student_electives`
                           WHERE `student_id`=%s""", (student_id,))
    elif course_code:
        cursor.execute("""SELECT `student_id`
                       FROM `student_electives`
                       WHERE `course_code`=%s""", (course_code,))
    else:
        cursor.execute("""SELECT * FROM `student_electives`""")
    return cursor.fetchall()

def get_periods(cursor: Cursor, /, *,
                period_id: Optional[int] = None) -> Tuple[Dict[str, Union[bool, int, str]]]:
    def format(tdelta):
        total_minutes = tdelta.total_seconds() // 60
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"{hours:2d}:{minutes:02d}"

    if period_id:
        cursor.execute("""SELECT `start_time`, `end_time`, `is_break`
                       FROM `periods`
                       WHERE `id`=%s""", (period_id,))
    else:
        cursor.execute("""SELECT * FROM `periods`""")

    periods = cursor.fetchall()
    for period in periods:
        period["start_time"] = format(period["start_time"])
        period["end_time"] = format(period["end_time"])

    return periods

def get_timetables(cursor: Cursor, /, *,
                   faculty_id: Optional[int] = None,
                   section_id: Optional[int] = None,
                   course_code: Optional[str] = None,
                   class_id: Optional[int] = None) -> Tuple[Dict[str, Union[int, str]]]:
    if class_id:
        cursor.execute("""SELECT `day`, `period_id`,
                       `faculty_section_course_id`,
                       `building_id`, `room_no`, `capacity`,
                       `is_lab`, `department`
                       FROM `timetables`
                       JOIN `classes`
                       ON `class_id`=`classes`.`id`
                       AND `class_id`=%s""", (class_id,))
    else:
        cursor.execute("""SELECT `day`, `period_id`,
                       `faculty_section_course_id`, `class_id`,
                       `building_id`, `room_no`, `capacity`,
                       `is_lab`, `department`
                       FROM `timetables`
                       JOIN `classes`
                       ON `class_id`=`classes`.`id`""")

    timetables = cursor.fetchall()
    if faculty_id or section_id or class_id:
        faculty_section_course_ids = {fsc["id"]: {
                "faculty_id": fsc.get("faculty_id", faculty_id),
                "section_id": fsc.get("section_id", section_id),
                "course_code": fsc.get("course_code", course_code)
            }
            for fsc in get_faculty_section_courses(cursor,
                                                   faculty_id=faculty_id,
                                                   section_id=section_id,
                                                   course_code=course_code)}
        timetables = [(timetable | faculty_section_course_ids[id])
                      for timetable in timetables if (id := timetable["faculty_section_course_id"]) in faculty_section_course_ids]
    return timetables

