from typehints import *

def get_campuses(cursor: Cursor, /, *,
				 programme_id: Optional[int] = None) -> Tuple[Optional[Dict[str, Union[int, str]]], ...]:
	if programme_id:
		cursor.execute("""SELECT `campuses`.`id`,
					   `campuses`.`name`
					   FROM `campuses`
					   JOIN `campus_programmes` AS `CP`
					   ON `campuses`.`id`=`CP`.`campus_id`
					   AND `CP`.`programme_id`=%s""",
					   (programme_id,))
	else:
		cursor.execute("""SELECT * FROM `campuses`""")
	return cursor.fetchall()

def get_campus_id(cursor: Cursor, /, *,
				  campus: Optional[str] = None) -> Optional[int]:
	cursor.execute("""SELECT `id` FROM `campuses`
				   WHERE `name` LIKE %s""", (campus,))
	result: Optional[Dict[str, int]] = cursor.fetchone()
	if result:
		return result["id"]
	return None

def get_campus_name(cursor: Cursor, /, *,
					id: Optional[int] = None) -> Optional[str]:
	cursor.execute("""SELECT `name` FROM `campuses`
				   WHERE `id`=%s""", (id,))
	result: Optional[Dict[str, str]] = cursor.fetchone()
	if result:
		return result["name"]
	return None

def get_schools(cursor: Cursor, /, *,
				campus_id: Optional[int] = None,
				department: Optional[str] = None) -> Tuple[Optional[Dict[str, Union[int, str]]], ...]:
	if campus_id and department:
		cursor.execute("""SELECT `schools`.`id`, `schools`.`name`
					   FROM `schools`
					   JOIN `school_departments` AS `SD`
					   ON `schools`.`id`=`SD`.`school_id`
					   AND `schools`.`campus_id`=%s
					   AND `SD`.`department` LIKE %s""",
					   (campus_id, department))
	elif campus_id:
			cursor.execute("""SELECT `id`, `name` FROM `schools`
						   WHERE `campus_id`=%s""", (campus_id))
	elif department:
		cursor.execute("""SELECT `schools`.`id`,
					   `schools`.`name`,
					   `schools`.`campus_id`
					   FROM `schools`
					   JOIN `school_departments` AS `SD`
					   ON `schools`.`id`=`SD`.`school_id`
					   AND `SD`.`department` LIKE %s""",
					   (department,))
	else:
		cursor.execute("""SELECT `id`, `name` FROM `campuses`""")
	return cursor.fetchall()

def get_school_id(cursor: Cursor, /, *,
				  campus_id: Optional[int] = None,
				  school: Optional[str] = None) -> Optional[int]:
	if campus_id:
		cursor.execute("""SELECT `id` FROM `schools`
					   WHERE `campus_id`=%s
					   AND `name`=%s""", (campus_id, school))
	else:
		cursor.execute("""SELECT `id`, `name` FROM `schools`
					   WHERE `name`=%s""", (school,))
	result: Optional[Dict[str, int]] = cursor.fetchone()
	if result:
		return result["id"]
	return None

def get_school_name(cursor: Cursor, /, *,
					id: Optional[int] = None) -> Optional[str]:
	cursor.execute("""SELECT `name` FROM `schools`
					WHERE `id`=%s)""", (id,))
	result: Optional[Dict[str, str]] = cursor.fetchone()
	if result:
		return result["name"]
	return None

def get_buildings(cursor: Cursor, /, *,
				  school_id: Optional[int] = None,
				  campus_id: Optional[int] = None) -> Tuple[Optional[Dict[str, int]], ...]:
	if school_id:
		cursor.execute("""SELECT `id`, `no_of_rooms` FROM `buildings`
					   WHERE `school_id`=%s""", (school_id,))
	elif campus_id:
		cursor.execute("""SELECT `id`, `no_of_rooms`
					   FROM `campus_buildings`
					   WHERE `campus_id`=%s""", (campus_id,))
	else:
		cursor.execute("""SELECT `id`, `no_of_rooms` FROM `buildings`""")
	return cursor.fetchall()

def get_departments(cursor: Cursor, /, *,
					school_id: Optional[int] = None) -> Tuple[Optional[Dict[str, str]], ...]:
	if school_id:
		cursor.execute("""SELECT `department` FROM `school_departments`
					   WHERE `school_id`=%s""", (school_id,))
	else:
		cursor.execute("""SELECT * FROM `departments`""")
	return cursor.fetchall()

def get_degrees(cursor: Cursor, /) -> Tuple[Optional[Dict[str, str]], ...]:
	cursor.execute("""SELECT * FROM `degrees`""")
	return cursor.fetchall()

def get_degree_duration(cursor: Cursor, /, *,
						degree: Optional[str] = None) -> Optional[int]:
	cursor.execute("""SELECT `duartion` FROM `degrees`
				   WHERE `degree` LIKE %s""", (degree,))
	result: Optional[Dict[str, int]] = cursor.fetchone()
	if result:
		return result["duration"]
	return None

def get_streams(cursor: Cursor, /, *,
				department: Optional[str] = None) -> Tuple[Optional[Dict[str, str]], ...]:
	if department:
		cursor.execute("""SELECT `stream`
					   FROM `school_streams`
					   WHERE `department` LIKE %s""", (department,))
	else:
		cursor.execute("""SELECT * FROM `streams`""")
	return cursor.fetchall()

def get_programmes(cursor: Cursor, /, *,
				   degree: Optional[str] = None,
				   stream: Optional[str] = None) -> Tuple[Optional[Dict[str, str]], ...]:
	if degree and stream:
		cursor.execute("""SELECT `id` FROM `programmes`
					   WHERE `degree` LIKE %s
					   AND `stream` LIKE %s""",
					   (degree, stream))
	elif degree:
		cursor.execute("""SELECT `id`, `stream` FROM `programmes`
					   WHERE `degree` LIKE %s""", (degree,))
	elif stream:
		cursor.execute("""SELECT `id`, `degree` FROM `programmes`
					   WHERE `stream` LIKE %s""", (stream,))
	else:
		cursor.execute("""SELECT * FROM `programmes`""")
	return cursor.fetchall()

def get_programme(cursor: Cursor, /, *,
				  programme_id: Optional[int] = None) -> Optional[Dict[str, str]]:
	cursor.execute("""SELECT `degree`, `stream`
				   FROM `programmes`
				   WHERE `id`=%s""", (programme_id,))
	return cursor.fetchone()

def get_campuses_with_programme(cursor: Cursor, /, *,
								programme_id: Optional[int] = None) -> Tuple[Optional[Dict[str, str]], ...]:
	cursor.execute("""SELECT `campus_id` FROM `campus_programmes`
				   WHERE `programme_id`=%s""", (programme_id,))
	return cursor.fetchall()
