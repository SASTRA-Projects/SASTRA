from typehints import Connection, Cursor


def create_database(db_connector: Connection, cursor: Cursor) -> None:
	r"""
	Initializes the database schema for a university management system.

	This function **creates all necessary concrete tables** in a relational database, including
	campuses, schools, buildings, departments, degrees, streams, programmes, courses,
	faculties, students, and various mappings between them.

	It ensures **data integrity** by enforcing:
	- ``PRIMARY KEY`` constraints to maintain uniqueness.
	- ``FOREIGN KEY`` constraints for relational consistency.
	- ``CHECK`` constraints for logical validations.

	Parameters
	==========
	- **db_connector** : Connection
	  The database connection object used to interact with the database.

	- **cursor** : Cursor
	  A cursor object for executing SQL commands.

	Tables Created
	==============
	- **``campuses``**: Stores different campuses of the university.
	- **``schools``**: Represents various schools.
	- **``buildings``**: Associates buildings with schools.
	- **``departments``**: Represents academic departments like CSE, ECE.
	- **``degrees``**: Defines different degree types with durations.
	- **``streams``**: Specializations within a department.
	- **``programmes``**: A combination of ``degrees`` and ``streams``.
	- **``courses``**: Defines courses, including lecture (L), practical (P), and tutorial (T) hours.
	- **``lab_departments``**: Maps lab courses to departments, if the course and lab don't match on department.
	- **``campus_programmes``**: Maps programmes to campuses.
	- **``school_departments``**: Associates schools with departments.
	- **``programme_courses``**: Assigns courses to programmes.
	- **``classes``**: Represents classrooms and labs.
	- **``sections``**: Defines academic sections.
	- **``faculties``**: Stores faculty details.
	- **``students``**: Maintains student enrollment details.

	Examples
	========
	.. code-block:: python

		>>> from SASTRA import *

		>>> # Create Connection object and Cursor object
		>>> connector, cursor = connect(
				user="root",
				password="secret_pwd",
				host="localhost"
			) # Creates `SASTRA` by default, if not exists

		>>> create_database(connector, cursor)

	See Also
	========
	- :func:`connect` – To establish a connection with the database.
	- :func:`create_relations` – Creates relational tables for the database.
	- :func:`create_triggers` – To create triggers for the database.
	"""
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `name`
	- `name` \u2192 `id`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `campuses` (
				   `id` TINYINT UNSIGNED AUTO_INCREMENT,
				   `name` VARCHAR(40) NOT NULL,
				   PRIMARY KEY(`id`),
				   UNIQUE(`name`)
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `name`, `campus_id`
	- `name`, `campus_id` \u2192 `id`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `schools` (
				   `id` SMALLINT UNSIGNED AUTO_INCREMENT,
				   `name` VARCHAR(40) NOT NULL,
				   `campus_id` TINYINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`campus_id`) REFERENCES `campuses`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`name`, `campus_id`)
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `school_id`, `rooms`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `buildings` (
				   `id` SMALLINT UNSIGNED AUTO_INCREMENT,
				   `school_id` SMALLINT UNSIGNED NOT NULL,
				   `rooms` SMALLINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`school_id`) REFERENCES `schools`(`id`)
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `departments` (
				   `name` VARCHAR(40),
				   PRIMARY KEY(`name`)
	)""")
	"""
	Functional Dependencies
	=======================
	- `name` \u2192 `duration`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `degrees` (
				   `name` VARCHAR(20),
				   `duration` TINYINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`name`),
				   CHECK(`duration` <= 10 AND `duration` >= 1)
	)""")
	"""
	Functional Dependencies
	=======================
	- `name` \u2192 `department`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `streams` (
				   `name` VARCHAR(60),
				   `department` VARCHAR(40) NOT NULL,
				   PRIMARY KEY(`name`),
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `degree`, `stream`
	- `degree`, `stream` \u2192 `id`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `programmes` (
				   `id` MEDIUMINT UNSIGNED AUTO_INCREMENT,
				   `degree` VARCHAR(20) NOT NULL,
				   `stream` VARCHAR(60) NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`degree`) REFERENCES `degrees`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`stream`) REFERENCES `streams`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`degree`, `stream`)
	)""")
	"""
	Functional Dependencies
	=======================
	- `code` \u2192 `name`, `department`, `credits`, `L`, `P`, `T`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `courses` (
				   `code` VARCHAR(10),
				   `name` VARCHAR(60) NOT NULL,
				   `department` VARCHAR(40) NOT NULL,
				   `credits` TINYINT UNSIGNED NOT NULL,
				   `L` TINYINT UNSIGNED NOT NULL,
				   `P` TINYINT UNSIGNED NOT NULL,
				   `T` TINYINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`code`),
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   CHECK(`L` >= 0 AND `P` >= 0 AND `T` >= 0 AND (`L` + `P` + `T`) > 0)
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `lab_departments` (
				   `id` MEDIUMINT UNSIGNED AUTO_INCREMENT,
				   `course_code` VARCHAR(10) NOT NULL, -- must be lab, trigger
				   `department` VARCHAR(10) NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`course_code`) REFERENCES `courses`(`code`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`course_code`, `department`)
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `campus_programmes` (
				   `campus_id` TINYINT UNSIGNED NOT NULL,
				   `programme_id` MEDIUMINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`campus_id`, `programme_id`),
				   FOREIGN KEY(`campus_id`) REFERENCES `campuses`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`programme_id`) REFERENCES `programmes`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `school_departments` (
				   `school_id` SMALLINT UNSIGNED NOT NULL,
				   `department` VARCHAR(40) NOT NULL,
				   PRIMARY KEY(`school_id`, `department`),
				   FOREIGN KEY(`school_id`) REFERENCES `schools`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	"""
	Functional Dependencies
	=======================
	- `course_code`, `is_elective` \u2192 `is_elective`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `programme_courses` (
				   `course_code` VARCHAR(10) NOT NULL,
				   `programme_id` MEDIUMINT UNSIGNED NOT NULL,
				   `is_elective` BOOLEAN NOT NULL,
				   PRIMARY KEY(`course_code`, `programme_id`),
				   FOREIGN KEY(`course_code`) REFERENCES `courses`(`code`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`programme_id`) REFERENCES `programmes`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `building_id`, `room_no`, `capacity`, `is_lab`
	- `building_id`, `room_no` \u2192 `id`, `capacity`, `is_lab`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `classes` (
				   `id` MEDIUMINT UNSIGNED AUTO_INCREMENT,
				   `building_id` SMALLINT UNSIGNED NOT NULL,
				   `room_no` SMALLINT UNSIGNED NOT NULL,
				   `capacity` SMALLINT UNSIGNED NOT NULL,
				   `is_lab` BOOLEAN NOT NULL,
				   `department` VARCHAR(40) NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`building_id`) REFERENCES `buildings`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`building_id`, `room_no`)
	)""")
	"""
	Functional Dependencies
	=======================
	None Exist
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `sections` (
				   `id` MEDIUMINT UNSIGNED AUTO_INCREMENT,
				   `campus_id` TINYINT UNSIGNED NOT NULL,
				   `degree` VARCHAR(40) NOT NULL,
				   `stream` VARCHAR(40) NULL,
				   `section` VARCHAR(2) NOT NULL,
				   `year` TINYINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`degree`) REFERENCES `degrees`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`stream`) REFERENCES `streams`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`campus_id`, `degree`, `stream`, `section`, `year`)
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `name`, `campus_id`, `department`, `join_year`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `faculties` (
				   `id` MEDIUMINT UNSIGNED AUTO_INCREMENT,
				   `name` VARCHAR(40) NOT NULL,
				   `campus_id` TINYINT UNSIGNED NOT NULL,
				   `department` VARCHAR(40) NOT NULL,
				   `join_year` SMALLINT UNSIGNED NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`campus_id`) REFERENCES `campuses`(`id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   FOREIGN KEY(`department`) REFERENCES `departments`(`name`)
				   ON UPDATE CASCADE ON DELETE RESTRICT
	)""")
	"""
	Functional Dependencies
	=======================
	- `id` \u2192 `name`, `campus_id`, `join_year`, `programme_id`, `roll_no`, `phone`
	- `campus_id`, `join_year`, `programme_id`, `roll_no` \u2192 `id`, `name`
	"""
	cursor.execute("""CREATE TABLE IF NOT EXISTS `students` (
				   `id` INT UNSIGNED AUTO_INCREMENT,
				   `name` VARCHAR(40) NOT NULL,
				   `campus_id` TINYINT UNSIGNED NOT NULL,
				   `join_year` SMALLINT UNSIGNED NOT NULL,
				   `programme_id` MEDIUMINT UNSIGNED NOT NULL,
				   `roll_no` SMALLINT UNSIGNED NOT NULL,
				   `phone` CHAR(10) NOT NULL,
				   PRIMARY KEY(`id`),
				   FOREIGN KEY(`campus_id`, `programme_id`)
				   REFERENCES `campus_programmes`(`campus_id`, `programme_id`)
				   ON UPDATE CASCADE ON DELETE RESTRICT,
				   UNIQUE(`campus_id`, `join_year`, `programme_id`, `roll_no`),
				   CHECK(`phone` REGEXP '^[6-9][0-9]{9}$')
	)""")
	db_connector.commit()
