# Contributing to SASTRA Timetable Project

Welcome, contributor! 🎉

Thank you for your interest in improving the **SASTRA**, a comprehensive scheduling system for SASTRA Deemed University.

This guide outlines how to contribute effectively, ensuring consistency and code quality across all modules.

---

## 🚀 Tech Stack

* **Frontend**: Plain HTML (Jinja2 templating), CSS, JavaScript (in-template)
* **Backend**: Python 3.10+ with Flask
* **Database**: MySQL (managed on Aiven Cloud)
* **DB Access**: Raw SQL queries via `pymysql`
* **Hosting**: [Render](https://sastra-3yx3.onrender.com/)

---

## 📌 Prerequisites

* Python 3.10+
* MySQL client tools
* Git commands
* Code editor with Python, HTML, and JS support (e.g., VSCode)
* Familiarity with `venv` (Optional), type hints, doctring conventions, and raw SQL via PyMySQL

---

## ✅ How to Contribute

### 1. Fork & Clone

See [README.md](https://github.com/SASTRA-Projects/SASTRA/blob/main/README.md) for other OS.

(For Linux)
```bash
git clone https://github.com/SASTRA-Projects/SASTRA.git
cd SASTRA
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Setup `.env`

Copy to `.env` and fill in the DB credentials:

```
DB_HOST=<host>
DB_USER=<user>
DB_PASSWORD=<password>
DB_NAME=SASTRA
```

---

## ✍️ Coding Guidelines

### Python

* Use **type hints** for **all** functions and variables.
* All public functions must include:

  * **Multiline docstrings** using NumPy/Sphinx style.
  * **At least one usage example** with `.. code-block:: python` for clarity.
* Use `black` for formatting and `ruff` for linting.
* Example:

```python
def add_campus(db_connector: Connection,
               cursor: Cursor, /, *,
               id: Optional[int] = None,
               campus: Optional[str] = None) -> None:
    r"""
    Add a new campus record to the `campuses` table.

    Parameters
    ==========
    - **db_connector**: Connection
      The database connection object.
    - **cursor**: Cursor
      Cursor for executing SQL commands.
    - **id**: Optional[int]
      Campus ID (optional).
    - **campus**: Optional[str]
      Name of the campus.

    Examples
    ========
    .. code-block:: python

        >>> from SASTRA.mysql_connector import *
        >>>
        >>> connector, cursor = connect(
				user=user,
				password=password,
				host=host
			)
        >>> connector, cursor = connect(user="root", password="secret")
        >>> add_campus(connector, cursor, id=2, campus="SRC")
    """
    cursor.execute("""INSERT INTO `campuses` (`id`, `name`) VALUES (%s, %s)""", (id, campus))
    db_connector.commit()
```

### DB Access

* Write raw SQL queries directly using `pymysql`.
* Connection setup must use secure practices and be type-annotated.
* Use parameterized queries at all times:

> [!IMPORTANT]
> The table & column names in the queries are case-sensitive.
>
> Use single quotes ('') in `mysql` (client), not double quotes("").
>
> Use backticks (\`\`) for table & column names.
>
> Use triple double-quotes (""" """) for queries in `pymysql`
> for consistent styling.

```python
cursor.execute("""SELECT * FROM `users` WHERE id = %s""", (user_id,))
```

### HTML/CSS/JS

* HTML uses plain HTML5 with Jinja2 templating.
* CSS should preferably be external but currently inlined.
* JavaScript must be scoped per page.

---

## 🧪 Testing & Validation

* Test Flask routes manually via browser/Postman.
* Confirm SQL correctness with direct testing (using CLI).
* Use browser dev-tools to verify frontend behavior.
* Also verify its behavior on different sized devices.

---

## 📟 Commit Message Format

Use the following format:

```
[short description]

[optional longer explanation]

Example:
add trigger creation for table updates
```
---

## 📂 Pull Requests & Issues

* Follow the **Pull Request Template** (auto-loaded when opening a PR)
* Use **Issue Template** to raise bugs/feature requests
* PRs that do not follow the structure will be auto-requested for changes
* Every PR **must** be linked to an Issue (by typing `Fixds #<id>` in description)

---

## 👮 Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) to keep this a welcoming space for all.

---

## 💬 Need Help?

Raise an issue, open a discussion, or reach out to the maintainers via GitHub.

Live site: [https://sastra-3yx3.onrender.com](https://sastra-3yx3.onrender.com)

Maintained by [SASTRA-Projects](https://github.com/SASTRA-Projects)

---

Thank you for helping build this project!
