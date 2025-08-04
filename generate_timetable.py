from itertools import combinations
from typehints import Connection, Cursor, Optional, Tuple
import delete_data
import fetch_data
import insert_data
import random
import show_data


def generate_timetable(db_connector: Connection, cursor: Cursor,
					   campus_id: Optional[int] = None,
					   days: Tuple[str] = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"),
					   period_ids: Tuple[int] = tuple(range(1,9))) -> None:

	PERIODS = {(day, period_id) for day in days for period_id in period_ids}

	def get_minor_elective_hrs(section_id):
		minor_electives = {crs["course_code"] for crs in fetch_data.get_section_minor_electives(cursor, section_id=section_id)}
		if not minor_electives:
			return set()

		cursor.execute("""SELECT `day`, `period_id`
					   FROM `timetables`
					   JOIN `faculty_section_course`
					   ON `id`=`faculty_section_course_id`
					   AND `course_code` IN %s
					   AND `section_id`=%s""", (minor_electives, section_id))
		return {(period["day"], period["period_id"]) for period in cursor.fetchall()}

	def get_free_classes(no_of_students, day, period_id):
		cursor.execute("""SELECT `id`
					   FROM `classes`
					   JOIN `campus_buildings` `CB`
					   ON `CB`.`building_id`=`classes`.`building_id`
					   AND `CB`.`campus_id`=%s
					   AND `capacity` >= %s
					   AND NOT `is_lab`
					   EXCEPT
					   SELECT `id`
					   FROM `classes`
					   JOIN `timetables`
					   ON `class_id`=`id`
					   AND `day`=%s
					   AND `period_id`=%s""",
					   (campus_id, no_of_students, day, period_id))
		return {cls["id"] for cls in cursor.fetchall()}

	def get_free_periods(section_id):
		cursor.execute("""SELECT `day`, `period_id`
				 	   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   AND `section_id`=%s""", (section_id,))
		day_periods = {(dp["day"], dp["period_id"]) for dp in cursor.fetchall()}
		return PERIODS - get_minor_elective_hrs(section_id) - day_periods

	def no_of_elective_students(degree, stream, elective):
		cursor.execute("""SELECT `stream`
					   FROM `student_electives` `SE`
					   JOIN `section_students` `SS`
					   ON `SS`.`student_id`=`SE`.`student_id`
					   JOIN `sections`
					   ON `sections`.`id`=`SS`.`section_id`
					   AND `campus_id`=%s
					   AND `degree`=%s
					   AND `course_code`=%s""",
					   (campus_id, degree, elective))
		return len([1 for s in cursor.fetchall() if stream is s["stream"] or stream==s["stream"]])

	def get_section_course(degree, stream, course_code):
		if stream:
			cursor.execute("""SELECT DISTINCT(`section_id`) AS `section_id`
						   FROM `faculty_section_course`
						   JOIN `sections`
						   ON `section_id`=`sections`.`id`
						   AND `campus_id`=%s
						   AND `degree`=%s
						   AND `stream`=%s
						   AND `course_code`=%s""",
						   (campus_id, degree, stream, course_code))
		else:
			cursor.execute("""SELECT DISTINCT(`section_id`) AS `section_id`
						   FROM `faculty_section_course`
						   JOIN `sections`
						   ON `section_id`=`sections`.`id`
						   AND `campus_id`=%s
						   AND `degree`=%s
						   AND `stream` IS NULL
						   AND `course_code`=%s""",
						   (campus_id, degree, stream, course_code))
		return {section["section_id"] for section in cursor.fetchall()}

	def sort_course(course_code):
		course = fetch_data.get_course(cursor, code=course_code)
		return (course["P"], course["L"]+course["P"]+course["T"])

	def lab_capacities(department, day, period_id):
		cursor.execute("""SELECT COUNT(*) / `P` AS `labs_per_week`,
					   `section_id`, `degree`, `stream`, `course_code`
					   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   JOIN `courses`
					   ON `course_code`=`code`
					   JOIN `classes`
					   ON `classes`.`id`=`class_id`
					   AND `is_lab`
					   JOIN `sections`
					   ON `sections`.`id`=`section_id`
					   AND `campus_id`=%s
					   AND `classes`.`department`=%s
					   GROUP BY `section_id`, `course_code`""",
					   (campus_id, department))
		sec_crs = cursor.fetchall()
		cursor.execute("""SELECT COUNT(*) AS `no_of_students`,
					   `FSC`.`section_id`, `course_code`,
					   `get_is_elective`(`code`, `FSC`.`section_id`) AS `is_elective`
					   `FSC`.`section_id`, `course_code`,
					   `get_is_elective`(`code`, `FSC`.`section_id`) AS `is_elective`
					   FROM `faculty_section_course` `FSC`
					   JOIN `courses`
					   ON `course_code`=`code`
					   JOIN `sections`
					   ON `sections`.`id`=`FSC`.`section_id`
					   JOIN `section_students` `SS`
					   ON `SS`.`section_id`=`sections`.`id`
					   AND `campus_id`=%s
					   AND `courses`.`department`=%s
					   GROUP BY `FSC`.`section_id`, `code`""",
					   (campus_id, department))
		no_of_students = [std for std in cursor.fetchall() if not std["is_elective"]]
		no_of_students = [std for std in cursor.fetchall() if not std["is_elective"]]
		cursor.execute("""SELECT COUNT(*) AS `no_of_sections`,
					   `course_code`, `degree`, `stream`
					   FROM `faculty_section_course` `FSC`
					   JOIN `sections`
					   ON `sections`.`id`=`FSC`.`section_id`
					   JOIN `courses`
					   ON `code`=`course_code`
					   AND `campus_id`=%s
					   AND `department`=%s
					   AND `get_is_elective`(`code`, `section_id`)
					   AND `get_is_elective`(`code`, `section_id`)
					   AND `P`
					   GROUP BY `code`, `degree`, `stream`""",
					   (campus_id, department))
		no_of_sections = cursor.fetchall()
		cursor.execute("""SELECT COUNT(*) AS `no_of_students`,
					   `course_code`, `degree`, `stream`
					   FROM `section_students` `SS`
					   JOIN `sections`
					   ON `SS`.`section_id`=`sections`.`id`
					   JOIN `student_electives` `SE`
					   ON `SS`.`student_id`=`SE`.`student_id`
					   JOIN `courses`
					   ON `course_code`=`code`
					   AND `get_is_elective`(`code`, `SS`.`section_id`)
					   AND `get_is_elective`(`code`, `SS`.`section_id`)
					   AND `P`
					   AND `campus_id`=%s
					   AND `department`=%s
					   GROUP BY `code`, `degree`, `stream`""",
					   (campus_id, department))
		no_of_elective_students = cursor.fetchall()
		cursor.execute("""SELECT `class_id`, `capacity`, `section_id`,
					   `course_code`, `degree`, `stream`,
					   `get_is_elective`(`course_code`, `section_id`) AS `is_elective`
					   `course_code`, `degree`, `stream`,
					   `get_is_elective`(`course_code`, `section_id`) AS `is_elective`
					   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   JOIN `classes`
					   ON `classes`.`id`=`class_id`
					   AND `is_lab`
					   AND `day`=%s
					   AND `period_id`=%s
					   JOIN `courses`
					   ON `course_code`=`code`
					   JOIN `sections`
					   ON `section_id`=`sections`.`id`
					   AND `campus_id`=%s
					   AND `courses`.`department`=%s""",
					   (day, period_id, campus_id, department))
		class_capacity = list(cursor.fetchall())
		cursor.execute("""SELECT `classes`.`id` AS `class_id`, `capacity`
					   FROM `classes`
					   JOIN `campus_buildings` `CB`
					   ON `CB`.`building_id`=`classes`.`building_id`
					   AND `is_lab`
					   AND `campus_id`=%s
					   AND `department`=%s""", ( campus_id, department))
		classes = cursor.fetchall()
		elective_std_sec = {(std["degree"], std["stream"], std["course_code"]): std["no_of_students"] // sec["no_of_sections"]
					  		for std in no_of_elective_students
							for sec in no_of_sections
							if std["degree"] == sec["degree"]
							and std["stream"] == sec["stream"]
							and std["course_code"] == sec["course_code"]}
		cls_sec_crs = {(sc["course_code"], sc["section_id"]): sc["labs_per_week"]
						for cls in class_capacity
					   for sc in sec_crs
					   if sc["course_code"] == cls["course_code"]
					   and sc["section_id"] == cls["section_id"]}
		std_sec = {(std["section_id"], std["course_code"]): std["no_of_students"]
				   for std in no_of_students
				   for std in no_of_students
				   for cls in class_capacity
				   if std["course_code"] == cls["course_code"]
				   and std["section_id"] == cls["section_id"]}
		for cls in class_capacity:
			if cls["is_elective"]:
				cls["capacity"] -= elective_std_sec[(cls["degree"], cls["stream"], cls["course_code"])] // cls_sec_crs[(cls["course_code"], cls["section_id"])]
			else:
				cls["capacity"] -= std_sec[(cls["section_id"], cls["course_code"])] // cls_sec_crs[(cls["course_code"], cls["section_id"])]

		for cls in classes:
			if not any(cls["class_id"] == c["class_id"] for c in class_capacity):
				class_capacity.append(cls)

		return class_capacity

	def max_lab_capacity(department, day, period_id, no_of_students=0):
		class_capacity = lab_capacities(department, day, period_id)
		class_capacity = sorted(list({(cls["class_id"], int(cls["capacity"])) for cls in class_capacity}), key=lambda x: x[1], reverse=True)
		return [[*cls] for cls in class_capacity if cls[1] > no_of_students]

	def sorted_and_reverse(courses=None, no_of_electives=None, combs=[]):
		rev = lambda combs: sorted(combs | {c for comb in combs if (c := comb[::-1]) and c not in combs}, key=lambda x: (-len(x), x))
		if combs:
			return rev(set(combs))
		else:
			combs = {comb for i in range(1, no_of_electives+1) for comb in combinations(courses, i)}
			combs = {comb  if len(comb) > 1 else (comb[0], comb[0]) for comb in combs}
			return rev(combs)

	def transitive(allowed, c1, c2):
		c3 = (c1[0], c2[-1])
		for c in allowed:
			if c == c3:
				return tuple({*c1, *c2, *c3})
		else:
			return None

	def try_compress(section_id):
		def compress(day, period_id, faculty_id, section_id, course_code, class_id, *, forward=0):
			course = fetch_data.get_course(cursor, code=course_code)
			from_to = (day, period_id, day, period_id + forward)
			if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
			if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
				section = fetch_data.get_section(cursor, section_id=section_id)
				degree, stream = section["degree"], section["stream"]
				possible = True
				for section in fetch_data.get_sections(cursor, campus_id=campus_id, degree=degree):
					faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course_code)
					section_course = (section["id"], course_code)
					possible = all(possible and is_transfer_possible(*from_to, faculty["faculty_id"], *section_course)[0]
					   			   for faculty in faculties)
					if not possible:
						print(f"Unable to compress {day}{period_id}",
							  f"{section["year"]}{section["degree"]}-{section["stream"]}{section["section"]}")
						return False
			else:
				faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course_code)
				possible = all(is_transfer_possible(*from_to, faculty["faculty_id"], section_id, course_code, class_id)[0]
					  		   for faculty in faculties)
				if not possible:
					print(f"Unable to compress {day}{period_id}",
						  f"{section["year"]}{section["degree"]}-{section["stream"]}{section["section"]}")
						  f"{section["year"]}{section["degree"]}-{section["stream"]}{section["section"]}")
					return False

			timetable["period_id"] -= forward
			delete_data.delete_timetable(db_connector, cursor, **timetable)
			timetable["period_id"] += forward
			insert_data.add_timetable(db_connector, cursor, **timetable)
			return True

		cursor.execute("""SELECT `day`, `period_id`, `faculty_id`, `class_id`
					   FROM `timetables`
					   JOIN `faculty_section_course`
					   ON `id`=`faculty_section_course_id`
					   AND `section_id`=%s
					   ORDER BY `day`, `period_id`""", (section_id,))
		timetable = dict.fromkeys(days, [])
		for period in cursor.fetchall():
			timetable[period["day"]].append((period["period_id"], period["faculty_id"], section_id, period["class_id"]))

		for day in days:
			for period in timetable[day]:
				if period[0] == 5:
					for i in range(3, 0, -1):
						if not compress(day, i, *period[1:4], forward=1): return
					if not compress(day, 8, *period[1:4], forward=-1): return
					break
			else:
				for i in range(4, 0, -1):
					if not compress(day, i, *period[1:4], forward=1): return
				for i in range(7, 9):
					if not compress(day, i, *period[1:4], forward=-1): return

	def is_section_busy(section_id, day, period_id):
		cursor.execute("""SELECT 1
					   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   AND `section_id`=%s
					   AND `day`=%s
					   AND `period_id`=%s""", (section_id, day, period_id))
		return True if cursor.fetchone() else False

	def is_faculty_busy(faculty_id, day, period_id):
		cursor.execute("""SELECT 1
					   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   AND `faculty_id`=%s
					   AND `day`=%s
					   AND `period_id`=%s
					   LIMIT 1""", (faculty_id, day, period_id))
		return True if cursor.fetchone() else False

	def faculty_came_thrice(faculty_id, section_id, day):
		cursor.execute("""SELECT COUNT(*) AS `cnt`
					   FROM `timetables`
					   JOIN `faculty_section_course` `FSC`
					   ON `FSC`.`id`=`faculty_section_course_id`
					   AND `faculty_id`=%s
					   AND `section_id`=%s
					   AND `day`=%s
					   LIMIT 1""", (faculty_id, section_id, day))
		return cursor.fetchone()["cnt"] == 3

	def is_transfer_possible(from_day, from_period_id, to_day, to_period_id, faculty_id, section_id, course_code, class_id):
		if (from_day, from_period_id) == (to_day, to_period_id):
			return (True, "Same period")

		course = fetch_data.get_course(cursor, code=course_code)
		cls = fetch_data.get_class(cursor, class_id=class_id)
		if is_section_busy(section_id, to_day, to_period_id):
			return (False, "Section has other class")

		if is_faculty_busy(faculty_id, to_day, to_period_id):
			return (False, "Faculty has other class")

		if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
		if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
			section = fetch_data.get_section(cursor, section_id=section_id)
			degree, stream = section["degree"], section["stream"]
			sections = fetch_data.get_sections(cursor, campus_id=campus_id, degree=degree, stream=stream)

		if cls["is_lab"]:
			lab_capacity = lab_capacities(cls["department"], to_day, to_period_id)
			if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
			if fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id):
				no_of_sections = len(section_ids)
				cursor.execute("""SELECT 1
							   FROM `section_students` `SS`
							   JOIN `sections`
							   ON `SS`.`section_id`=`sections`.`id`
							   JOIN `student_electives` `SE`
							   ON `SS`.`student_id`=`SE`.`student_id`
							   AND `campus_id`=%s
							   AND `degree`=%s
							   AND `stream`=%s
							   AND `course_code`=%s""",
							   (campus_id, degree, stream, course_code))
				no_of_students = -(-len(cursor.fetchall()) // no_of_sections)
			else:
				no_of_students = len(fetch_data.get_section_students(cursor, section_id=section_id))
			if lab_capacity < no_of_students:
				return (False, "Lab has lesser capacity")
		return (True, fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id))
		return (True, fetch_data.is_elective(cursor, course_code=course_code, section_id=section_id))

	def can_allocate(day, period_id, section_id, course_code, class_id):
		faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course_code)
		if any(is_faculty_busy(faculty["faculty_id"], day, period_id) for faculty in faculties):
			return (False, "Faculty is busy")

	programmes = show_data.get_programmes(cursor, campus_id=campus_id)
	sections = fetch_data.get_sections(cursor, campus_id=campus_id)
	section_ids = {section["id"] for section in sections}
	student_electives = fetch_data.get_student_electives(cursor)

	# 1. Allocate elective labs: Assume no elective if stream is None
	for programme in programmes:
		courses = fetch_data.get_courses(cursor, programme_id=programme["id"], elective=True)
		_sections =  [section for section in sections if section["degree"]==programme["degree"]]
		for year in range(1, show_data.get_degree_duration(cursor, degree=programme["degree"]) + 1):
			_section_ids = {section["id"] for section in _sections if section["year"]==year}
			_student_ids = {student["student_id"] for section_id in _section_ids
							for student in fetch_data.get_section_students(cursor, section_id=section_id)}
			_student_electives = {course["code"]: student_ids for course in courses
								  if (student_ids := {se["student_id"] for se in student_electives
													  if se["course_code"] == course["code"] and se["student_id"] in _student_ids})}
			if not _student_electives:
				continue
			_courses = set(_student_electives.keys())
			no_of_electives = 0
			student_id = tuple(_student_electives[tuple(_courses)[0]])[0]
			for course, student_ids in _student_electives.items():
				if student_id in student_ids:
					no_of_electives += 1

			if no_of_electives > 1:
				allowed = set(sorted_and_reverse(courses=_courses, no_of_electives=no_of_electives))
				not_allowed = set()
				students = set()
				for se1 in student_electives:
					for student_id in se1[1]:
						if student_id in students:
							continue
						else:
							students.add(student_id)
						num = 0
						electives = set()
						for se2 in student_electives:
							if student_id in se2[1]:
								num += 1
								electives.add(se2["course_code"])
								if num == no_of_electives:
									break
						electives = tuple(sorted(electives))
						not_allowed.add(electives)
						not_allowed.add(electives[::-1])

				allowed -= not_allowed
				allowed = sorted_and_reverse(combs=allowed)
				for c1 in allowed:
					for c2 in allowed:
						if c1 != c2 and c1[-1] == c2[0]:
							allowed.remove(c1)
							allowed.remove(c2)
							course = transitive(allowed, c1, c2)
							if not course:
								allowed.append(c1)
								allowed.append(c2)
							else:
								allowed.append(course)
								course = course[::-1]
								if course not in allowed:
									allowed.append(course)
								break

				allowed = [set(course) for course in allowed]
				for course in allowed:
					allowed.remove(course)
					if course not in allowed:
						allowed.insert(0, course)

				allowed = sorted(tuple(tuple(course) for course in allowed), key=lambda x: len(x), reverse=True)
				over = set()
				not_allowed = set()
				for course in allowed:
					if all(c in over for c in course):
						not_allowed.add(course)
					elif not any(c in over for c in course):
						over |= set(course)
					else:
						for c2 in course:
							if c2 not in over:
								if (c2,) == course:
									break # not deleting it
								elif (c2,) not in allowed:
									allowed.append((c2,))
						else:
							not_allowed.add(course)

				assert course != over, "Unable to allot for all the electives"
				for course in not_allowed:
					allowed.remove(course)

			else:
				allowed = [tuple(_courses)]

			assert len(allowed) <= no_of_electives+1, f"Cannot allocate efficiently within {no_of_electives+1} periods"
			periods = PERIODS - get_minor_elective_hrs(list(_section_ids)[0])
			allowed = [tuple(sorted(((course, crs["L"], crs["P"], crs["T"])
									  for _courses in allowed
									  for course in _courses
									  if (crs := fetch_data.get_course(cursor, code=course))),
									  key=lambda x: (sum(x[1:4]), x[2]),
									  reverse=True))]
			for _courses in allowed:
				_elective_hrs = set()
				for course in _courses:
					_crs_hrs = set()
					lab_periods = [period for period in periods if period[1] % 2 == 1]
					if not (_section_ids := get_section_course(programme["degree"], programme["stream"], course[0])):
						continue

					no_of_sections = len(_section_ids)
					no_of_students = len(_student_electives[course[0]])
					_no_of_students = num = -(-no_of_students // no_of_sections)
					_half = -(-_no_of_students // 2)
					if course[2]:
						_course = fetch_data.get_lab_departments(cursor, course_code=course[0])
						assert course, "Programming Error, No labs found!"

						_course = _course[0]
						hrs = _course["P"]
						lab_departments = _course["lab_departments"]
						no_of_labs = len(lab_departments)
						assert no_of_labs == 1 or 2 * no_of_labs == hrs, "Number of lab-departments did not match with practical hours"

						labs = []
						for ld in lab_departments:
							class_day_period = []
							if ld == "":
								for period in lab_periods:
									class_capacity = tuple([cls, num] for cls in get_free_classes(num, *period))
									if len(class_capacity) >= no_of_sections:
										class_day_period.append((class_capacity, period))
							else:
								for period in lab_periods:
									class_day_period.append((max_lab_capacity(ld, *period, no_of_students=-(-num // 2)), period))
							assert class_day_period, "No lab is available..."
							assert ld != "" or len(class_day_period) >= no_of_sections, "Not enough classes"
							labs.append([class_day_period, ld])

						if no_of_labs == 1:
							labs *= (hrs // 2)

						while hrs:
							try:
								_labs = []
								_second_labs = []
								_lab_idx = 0
								_next_idx = -1
								no_of_times = 1

								if labs[-1][1] == "":
									class_day_period = sorted(labs[-1][0], key=lambda cdp: len(cdp[0]), reverse=True)
									while class_day_period[0][1] not in lab_periods:
										class_day_period.pop(0)

									for idx, cdp in enumerate(class_day_period):
										if cdp[1] in _elective_hrs:
											_lab_idx = idx
											break
									_labs.extend(tuple(range(no_of_sections)))
								else:
									class_day_period = sorted(labs[-1][0],
								   					   key=lambda cdp: tuple(cdp[0][i][1] for i in range(len(cdp[0]))),
													   reverse=True)
									total_capacity = 0
									while class_day_period[0][1] not in lab_periods:
										class_day_period.pop(0)

									for idx, cdp in enumerate(class_day_period):
										if cdp[1] not in _elective_hrs:
											continue
										_labs.clear()
										try:
											for i in range(no_of_sections):
												capacity = class_day_period[idx][0][i][1]
												total_capacity += capacity // _half
												_labs.extend((i,) * (capacity // _half))
												if total_capacity >= 2 * no_of_sections:
													break
											else:
												continue
										except IndexError:
											continue

										day, period_id = class_day_period[_lab_idx][1]
										if -(-no_of_students // 2) <= total_capacity < no_of_students: # need of second lab
											no_of_times = 2
											check_day = (lambda cdp: cdp[0] == day) \
														if any(cdp[1][0] != day for cdp in class_day_period) \
														else lambda cdp: cdp[1] == period_id
											for idx2, cdp2 in enumerate(class_day_period): # try on elective hrs
												if cdp2[1] not in _elective_hrs or check_day(cdp2[1]):
													continue
												_second_labs.clear()
												total_capacity = 0
												try:
													for i in range(no_of_sections):
														total_capacity += cdp2[0][i][1] // _half
														_second_labs.extend((i,) * (capacity // _half))
														if total_capacity >= 2 * no_of_sections:
															break
													else:
														continue
												except IndexError:
													continue
												_next_idx = idx2
												second_day, second_period_id = class_day_period[_next_idx][1]
												break
											else: # try for any hrs
												for idx2, cdp2 in enumerate(class_day_period):
													if check_day(cdp2[1]):
														continue
													_second_labs.clear()
													total_capacity = 0
													try:
														for i in range(no_of_sections):
															total_capacity += cdp2[0][i][1] // _half
															_second_labs.extend((i,) * (capacity // _half))
															if total_capacity >= 2 * no_of_sections:
																break
														else:
															continue
													except IndexError:
														continue
													_next_idx = idx2
													second_day, second_period_id = class_day_period[_next_idx]
													break
												else:
													continue

										elif total_capacity < no_of_students:
											continue

										_lab_idx = idx
									else: # not possible on elective hrs
										total_capacity = 0
										_labs.clear()
										try:
											for i in range(no_of_sections):
												capacity = class_day_period[_lab_idx][0][i][1]
												total_capacity += capacity // _half
												_labs.extend((i,) * (capacity // _half))
												if total_capacity >= 2 * no_of_sections:
													break
											else:
												continue
										except IndexError:
											continue

										day, period_id = class_day_period[_lab_idx][1]
										if -(-no_of_students // 2) <= total_capacity < no_of_students: # need of second lab
											check_day = (lambda cdp: cdp[0] == day) \
														if any(cdp[1][0] != day for cdp in class_day_period) \
														else lambda cdp: cdp[1] == period_id
											for idx2, cdp2 in class_day_period:
												if check_day(cdp2[1]):
													continue
												total_capacity = 0
												try:
													for i in range(no_of_sections):
														total_capacity += cdp2[0][i][1] // _half
														if total_capacity >= 2 * no_of_sections:
															break
												except IndexError:
													continue
												_next_idx = idx2
												second_day, second_period_id = class_day_period[_next_idx][1]
												break
											else:
												continue

								for section_id in _section_ids:
									faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course[0])
									if no_of_times == 2:
										_no_of_students = _half
										mid = -(-len(faculties) // 2)
										_faculties = faculties[:mid]
									else:
										_faculties = faculties
									for idx, fsc in enumerate(_faculties):
										class_id = class_day_period[_lab_idx][0][_labs[idx]][0]
										insert_data.add_timetable(db_connector, cursor,
																  day=day,
																  period_id=period_id,
																  faculty_section_course_id=fsc["id"],
																  class_id=class_id)
										insert_data.add_timetable(db_connector, cursor,
																  day=day,
																  period_id=period_id+1,
																  faculty_section_course_id=fsc["id"],
																  class_id=class_id)
									class_day_period.pop(_lab_idx)
									if _second_labs:
										mid = -(-len(faculties) // 2)
										_faculties = faculties[mid:]
										for idx, fsc in enumerate(_faculties):
											class_id = class_day_period[_next_idx][0][_second_labs[idx]][0]
											insert_data.add_timetable(db_connector, cursor,
																	  day=second_day,
																	  period_id=second_period_id,
																	  faculty_section_course_id=fsc["id"],
																	  class_id=class_id)
											insert_data.add_timetable(db_connector, cursor,
																	  day=second_day,
																	  period_id=second_period_id+1,
																	  faculty_section_course_id=fsc["id"],
																	  class_id=class_id)
											class_day_period.pop(_next_idx)
										_crs_hrs.add((second_day, second_period_id))
										_crs_hrs.add((second_day, second_period_id+1))

								_crs_hrs.add((day, period_id))
								_crs_hrs.add((day, period_id+1))
								print(day, period_id, course, "lab")
								hrs -= 2
								labs.pop()

							except Exception as exception:
								exception = exception.args
								print(exception, course, faculties, 1, day, period_id)
								for section_id in _section_ids:
									faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course[0])
									if _second_labs:
										_faculties = faculties[:-(-len(faculties) // 2)]
									else:
										_faculties = faculties
									for fsc in faculties:
										delete_data.delete_timetable(db_connector, cursor,
																	day=day, period_id=period_id, faculty_section_course_id=fsc["id"],
																	class_id=class_day_period[_lab_idx][0][_labs[idx]][0])
										delete_data.delete_timetable(db_connector, cursor,
																	day=day, period_id=period_id+1, faculty_section_course_id=fsc["id"],
																	class_id=class_day_period[_lab_idx][0][_labs[idx]][0])
									if _second_labs:
										for fsc in faculties[-(-len(faculties) // 2):]:
												delete_data.delete_timetable(db_connector, cursor,
																			day=second_day,
																			period_id=second_period_id,
																			faculty_section_course_id=fsc["id"],
																			class_id=class_day_period[_next_idx][0][__second_labs[idx]][0])
												delete_data.delete_timetable(db_connector, cursor,
																			day=second_day,
																			period_id=second_period_id+1,
																			faculty_section_course_id=fsc["id"],
																			class_id=class_day_period[_next_idx][0][__second_labs[idx]][0])

								if len(exception) < 2:
									return None
								elif "faculty" in exception[1] or "lunch" in exception[1]:
									for cdp in class_day_period:
										if cdp[1] == (day, period_id):
											labs[-1].remove(cdp)
											break
									if _second_labs:
										for cdp in class_day_period:
											if cdp[1] == (second_day, second_period_id):
												labs[-1].remove(cdp)
												break
								elif "more than 3" in exception[1]:
									if _second_labs:
										for cdp in class_day_period:
											if cdp[1][0] == second_day:
												labs[-1].remove(cdp)
									else:
										for cdp in class_day_period:
											if cdp[1][0] == day:
												labs[-1].remove(cdp)
											break
								continue

					if course[1] + course[3]:
						periods -= _crs_hrs
						hrs = course[1] + course[3]
						class_day_period = []
						for period in periods:
							class_capacity = tuple([cls] for cls in get_free_classes(num, *period))
							if len(class_capacity) >= no_of_sections:
								class_day_period.append((class_capacity, period))

						assert class_day_period, "No lab available for all the sections"
						class_day_period = sorted(class_day_period, key=lambda cdp: len(cdp[0]), reverse=True)
						while hrs:
							try:
								_cls_idx = 0
								for idx, cdp in enumerate(class_day_period):
									if cdp[1] in _elective_hrs:
										_cls_idx = idx
										break

								day, period_id = class_day_period[_cls_idx][1]
								classes = class_day_period[_cls_idx][0][:no_of_sections]
								classes = class_day_period[_cls_idx][0][:no_of_sections]
								for idx, section_id in enumerate(_section_ids):
									fsc = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course[0])[:no_of_sections]
									for _fsc, class_id in zip(sorted(fsc, key=lambda x: x["id"]), classes):
										insert_data.add_timetable(db_connector,
																  cursor,
																  day=day,
																  period_id=period_id,
																  faculty_section_course_id=_fsc["id"],
																  class_id=class_id)
									fsc = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course[0])[:no_of_sections]
									for _fsc, class_id in zip(sorted(fsc, key=lambda x: x["id"]), classes):
										insert_data.add_timetable(db_connector,
																  cursor,
																  day=day,
																  period_id=period_id,
																  faculty_section_course_id=_fsc["id"],
																  class_id=class_id)
									class_day_period.pop(_cls_idx)
								_elective_hrs.add((day, period_id))
								print(day, period_id, course, "theory")
								hrs -= 1

							except Exception as exception:
								exception = exception.args
								print(exception, course, fsc, 2, day, period_id)
								for section_id in _section_ids:
									fsc = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=course[0])[0]
									for idx in range(no_of_sections):
										delete_data.delete_timetable(db_connector, cursor,
																	day=day, period_id=period_id, faculty_section_course_id=fsc["id"],
																	class_id=class_day_period[_cls_idx][0][idx][0])
								if len(exception) < 2:
									return None
								elif "faculty" in exception[1] or "lunch" in exception[1]:
									for cdp in class_day_period:
										if cdp[1][0] == day:
											class_day_period.remove(cdp)
								elif "more than 3" in exception[1]:
									for cdp in class_day_period:
										if cdp[1] == (day, period_id):
											class_day_period.remove(cdp)
											break
								continue
						periods |= _crs_hrs

				periods -= _elective_hrs
				db_connector.commit()

	# 2. Allocate lab courses
	for section_id in section_ids:
		periods = {(day, period_id) for day, period_id in get_free_periods(section_id) if period_id % 2}
		no_of_students = len(fetch_data.get_section_students(cursor, section_id=section_id))
		faculty_courses = fetch_data.get_faculty_section_courses(cursor, section_id=section_id)
		twice = []
		ctwice = False
		for fc in faculty_courses:
			course = fetch_data.get_lab_departments(cursor, course_code=fc["course_code"], elective=False)
			if not course:
				continue
			course = course[0]
			hrs = course["P"]
			faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section_id, course_code=fc["course_code"])
			for fsc in faculties:
				if fsc["id"] != fc["id"]:
					faculty_courses.remove(fsc)

			lab_departments = course["lab_departments"]
			no_of_labs = len(lab_departments)
			assert no_of_labs == 1 or 2 * no_of_labs == hrs, "Number of lab-departments did not match with practical hours"

			labs = []
			cls = 0
			for ld in lab_departments:
				class_day_period = []
				if ld == "":
					for period in periods:
						if not (cls := get_free_classes(no_of_students, *period) & get_free_classes(no_of_students, period[0], period[1]+1)):
							pass
						class_day_period.append((([_cls, no_of_students] for _cls in cls), period))
				else:
					for period in periods:
						class_day_period.append((max_lab_capacity(ld, *period, no_of_students=-(-no_of_students // 2)), period))
				assert class_day_period, "No lab is available..."
				labs.append((class_day_period, ld))

			if no_of_labs == 1:
				labs *= (hrs // 2)

			while hrs:
				try:
					no_of_times = 1
					class_day_period = sorted(labs[-1][0], key=lambda cdp: tuple(cdp[0][i][1] for i in range(len(cdp[0]))), reverse=True)
					while class_day_period[0][1] not in periods:
						class_day_period.pop(0)
					class_id, capacity = class_day_period[0][0][0]
					day, period_id = class_day_period[0][1]
					if (day, period_id) in twice:
						no_of_times = 2
					if capacity < no_of_students:
						if ctwice:
							for cdp in class_day_period:
								if cdp[1] == twice[0]:
									class_id, capacity = cdp[0][0]
									day, period_id = twice[0]
									break
						no_of_times = 2

					if capacity < no_of_students // no_of_times or not class_day_period:
						if not ctwice:
							print("Too many students & too less capacity in all the labs...", class_day_period, capacity, no_of_students)
						else:
							ctwice = False # Lab is too busy at this time...
							continue
						print(exception)
						return None

					_faculties = faculties
					if no_of_times == 2:
						_faculties = faculties[:-(-len(faculties) // 2)]
					for fsc in _faculties:
						insert_data.add_timetable(db_connector, cursor,
												  day=day,
												  period_id=period_id,
												  faculty_section_course_id=fsc["id"],
												  class_id=class_id)
						insert_data.add_timetable(db_connector, cursor,
												  day=day,
												  period_id=period_id+1,
												  faculty_section_course_id=fsc["id"],
												  class_id=class_id)
					class_day_period[0][0][0][1] -= no_of_students // no_of_times
					if no_of_times-1:
						_faculties = faculties[-(-len(faculties) // 2):]
						if not ctwice:
							ctwice = True
							twice.append((day, period_id))
							class_id, capacity = class_day_period[1][0][0]
							day, period_id = class_day_period[1][1]
						else:
							periods.remove((day, period_id))
							for cdp in class_day_period:
								if cdp[1] == twice[1]:
									class_id, capacity = cdp[0][0]
									day, period_id = twice[1]
									break
							twice.clear()
							ctwice = False
						if capacity < no_of_students // 2:
							print("Too many students & too less capacity in all the labs...", class_day_period, capacity, no_of_students)

						for fsc in _faculties:
							insert_data.add_timetable(db_connector, cursor,
													  day=day,
													  period_id=period_id,
													  faculty_section_course_id=fsc["id"],
													  class_id=class_id)
							insert_data.add_timetable(db_connector, cursor,
													  day=day,
													  period_id=period_id+1,
													  faculty_section_course_id=fsc["id"],
													  class_id=class_id)
						class_day_period[1][0][0][1] -= no_of_students // no_of_times
						if ctwice:
							twice.append((day, period_id))
							ctwice = True
					if not ctwice:
						periods.remove((day, period_id))
					ctwice = True if twice else False
					hrs -= 2
					labs.pop()
					print(section_id, day, period_id, fc, class_id)
				except Exception as exception:
					exception = exception.args
					for fsc in faculties:
						delete_data.delete_timetable(db_connector, cursor,
													 day=day, period_id=period_id, faculty_section_course_id=fsc["id"], class_id=class_id)
						delete_data.delete_timetable(db_connector, cursor,
													 day=day, period_id=period_id+1, faculty_section_course_id=fsc["id"], class_id=class_id)
					if len(exception) < 2:
						print(exception)
						return None
					elif "more than 3 class" in exception[1] or "more than 2 labs" in exception[1]:
						for cdp in class_day_period:
							if cdp[1][0] == day:
								labs[-1][0].remove(cdp)
						ctwice = False
					elif exception[1] == "Same faculty cannot take more than one class at the same time":
						for cdp in class_day_period:
							if cdp[1] == (day, period_id):
								labs[-1][0].remove(cdp)
								break
					elif exception[1] == "Invalid Schedule: This hour is supposed for lunch" or "Elective" in exception[1]:
						for cdp in class_day_period:
							if cdp[1] == (day, period_id):
								labs[-1][0].remove(cdp)
								break
						periods.remove((day, period_id))
					print(f"Error {section_id} {day}{period_id} {fc["faculty_id"]}, {fc["id"]} {fc["course_code"]}: {exception}{no_of_students}")
					continue
			db_connector.commit()
			db_connector.commit()

	# 3. Allocate non-elective, non-lab hrs
	for section in sections:
		period_ids = (1, 2, 3, 4, 6, 7, 8)
		period_ids_weights = (4, 10, 15, 15, 14, 7, 3)
		days_weights = 5 * (1,)
		periods = [(day, period_id) for period_id in period_ids for day in days]
		periods_weights = [day_w * period_w for period_w in period_ids_weights for day_w in days_weights]
		minor_electives = get_minor_elective_hrs(section["id"])
		for period in minor_electives:
			idx = periods.index(period)
			periods_weights.pop(idx)
			periods.pop(idx)

		no_of_students = len(fetch_data.get_section_students(cursor, section_id=section["id"]))
		faculty_courses = fetch_data.get_faculty_section_courses(cursor, section_id=section["id"])
		if class_id := fetch_data.get_section_classes(cursor, section_id=section["id"]):
			class_id = class_id[0]["class_id"]

		print(section)
		for fc in faculty_courses:
			course = fetch_data.get_course(cursor, code=fc["course_code"])
			if not course or fetch_data.is_elective(cursor, course_code=fc["course_code"], section_id=section["id"]):
			if not course or fetch_data.is_elective(cursor, course_code=fc["course_code"], section_id=section["id"]):
				continue
			hrs = course["L"] + course["T"]
			faculties = fetch_data.get_faculty_section_courses(cursor, section_id=section["id"], course_code=fc["course_code"])
			for fsc in faculties:
				if fsc["id"] != fc["id"]:
					faculty_courses.remove(fsc)

			while hrs:
				try:
					day, period_id = random.choices(periods, weights=periods_weights)[0]
					if not class_id:
						roaming_id = list(get_free_classes(no_of_students, day, period_id))[0]
					insert_data.add_timetable(db_connector, cursor,
											  day=day,
											  period_id=period_id,
											  faculty_section_course_id=fc["id"],
											  class_id=(class_id or roaming_id))
					hrs -= 1
					idx = periods.index((day, period_id))
					periods_weights.pop(idx)
					periods.pop(idx)
				except Exception as exception:
					exception = exception.args
					delete_data.delete_timetable(db_connector, cursor,
												day=day, period_id=period_id,
												faculty_section_course_id=fc["id"], class_id=(class_id or roaming_id))
					if len(exception) < 2:
						print(exception, period_ids_weights, len(periods), day, period, class_id, roaming_id)
						return None
					elif exception[0] == 1644 and exception[1].find("more than") == -1:
						idx = periods.index((day, period_id))
						periods_weights.pop(idx)
						periods.pop(idx)
					print(f"Error {section["id"]},{day}{period_id} {fc["faculty_id"]}, {fc["id"]} {fc["course_code"]}: {exception}")
					continue
			print("Success")
			db_connector.commit()
			print("Success")
			db_connector.commit()
