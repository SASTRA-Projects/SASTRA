from typehints import *
import pymysql

timeout: int = 180

db_connector: Optional[Connection] = None
cursor: Optional[Cursor] = None

def connect(user: str,
            password: str, *,
            host: str = "mysql-93e938b-harikrishnasri3.f.aivencloud.com") -> Tuple[Connection, Optional[Cursor]]:
  global db_connector, cursor
  db_connector = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    host=host,
    password=password,
    read_timeout=timeout,
    port=17216,
    user=user,
    write_timeout=timeout,
  )
  if db_connector:
    cursor = db_connector.cursor()
    db_connector.autocommit(False)
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

def close() -> NoReturn:
  if db_connector:
    db_connector.commit()
    if cursor:
      cursor.close()
    db_connector.close()
  exit()

if __name__ == "__main__":
	close()