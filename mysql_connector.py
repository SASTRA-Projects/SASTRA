from typehints import Connection, Cursor, Optional, Tuple
import pymysql

timeout = 180
db_connector: Optional[Connection] = None
cursor: Optional[Cursor] = None


def connect(user: str,
			password: str, *,
			host: str = "mysql-93e938b-harikrishnasri3.f.aivencloud.com",
			charset: str = "utf8mb4",
			port: int = 17216) -> Tuple[Connection, Cursor]:
	global db_connector, cursor
	db_connector = pymysql.connect(
		charset=charset,
		connect_timeout=timeout,
		cursorclass=Cursor,
		host=host,
		password=password,
		read_timeout=timeout,
		port=port,
		user=user,
		write_timeout=timeout,
		autocommit=False
	)
	if db_connector:
		cursor = db_connector.cursor()
	if cursor:
		cursor.execute("""CREATE DATABASE IF NOT EXISTS `SASTRA`""")
		cursor.execute("""USE `SASTRA`""")
	return (db_connector, cursor)


def create_db(cursor: Cursor, /, *,
			  database: Optional[str] = None) -> None:
	cursor.execute("""CREATE DATABASE IF NOT EXISTS `%s`""", (database,))


def use_db(db_connector: Connection,
		   cursor: Cursor, /, *,
		   database: Optional[str] = None) -> None:
	db_connector.autocommit(False)
	cursor.execute("""USE `%s`""", (database,))


def close() -> None:
	if cursor:
		cursor.close()
	if db_connector:
		db_connector.commit()
		db_connector.close()
	exit()


if __name__ == "__main__":
	close()
