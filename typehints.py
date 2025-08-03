from typing import Dict, List, Optional, TypeAlias, Union, Tuple, Set
import pymysql
import werkzeug

Connection: TypeAlias = pymysql.connections.Connection
Cursor: TypeAlias = pymysql.cursors.DictCursor

Response: TypeAlias = werkzeug.wrappers.Response
NotFound: TypeAlias = werkzeug.exceptions.NotFound
IntegrityError: TypeAlias = pymysql.err.IntegrityError
