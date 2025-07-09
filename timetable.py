from typehints import *

def create_timetable(db_connector: Connection, cursor: Cursor) -> None:
	r"""
	Creates timetable table for the database.

	Parameters
	==========
	- **db_connector** : Connection
	  The database connection object used to interact with the database.

	- **cursor** : Cursor
	  A cursor object for executing SQL commands.

	Tables Created
	===============
	- **``periods``**: Stores id, start_time, end_time and is_break information.
	- **``timetable``**: To store the timetable each and every classes and sections.

	Examples
	=========
	.. code-block:: python

		>>> from SASTRA import *

		>>> # Create Connection object and Cursor object
		>>> connector, cursor = connect(
				user="root",
				password="secret_pwd",
				host="localhost"
			)
		
		>>> create_database(connector, cursor)
		>>> create_relations(connector, cursor)
		>>> create_timetable(connector, cursor)

	See Also
	========
	- `create_database()`: Defines base tables before relations are added.
	- `create_relations()`: Defines the relational tables.
	"""
	import relations
	relations.create_relations(db_connector, cursor)

	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `start_time`, `end_time`, `is_break`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `periods` (
				   `id` TINYINT UNSIGNED AUTO_INCREMENT,
				   `start_time` TIME NOT NULL,
				   `end_time` TIME NOT NULL,
				   `is_break` BOOLEAN NOT NULL,
				   PRIMARY KEY(`id`)
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `timetables` (
				   `day` ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday') NOT NULL,
				   `period_id` TINYINT UNSIGNED NOT NULL,
				   `faculty_section_course_id` INT UNSIGNED NOT NULL,
				   `class_id` MEDIUMINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`day`, `period_id`, `faculty_section_course_id`),
				   FOREIGN KEY(`faculty_section_course_id`) REFERENCES `faculty_section_course`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`period_id`) REFERENCES `periods`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`class_id`) REFERENCES `classes`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	db_connector.commit()