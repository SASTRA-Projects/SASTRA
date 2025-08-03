from typehints import Connection, Cursor, Optional

"""Delete rows from tables.
"""
def delete_timetable(db_connector: Connection,
					 cursor: Cursor, /, *,
					 day: Optional[str] = None,
					 period_id: Optional[int] = None,
					 faculty_section_course_id: Optional[int] = None,
					 class_id: Optional[int] = None) -> None:
	cursor.execute("""DELETE FROM `timetables`
				   WHERE `day`=%s
				   AND `period_id`=%s
				   AND `faculty_section_course_id`=%s
				   AND `class_id`=%s""", (day, period_id, faculty_section_course_id, class_id))
	db_connector.commit()
