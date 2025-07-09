from typehints import *

def delete_campus(db_connector: Connection,
				  cursor: Cursor, /, *,
				  campus: str) -> None:
	cursor.execute("""DELETE FROM `campuses`
				   WHERE `name`=%s""", (campus,))
	db_connector.commit()