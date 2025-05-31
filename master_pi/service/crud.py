def get_by_field(cursor, table, field, value, args):
    """
    Retrieve one or more rows from a table based on a specific field value.

    Args:
        cursor (MySQLCursor): Database cursor.
        table (str): Table name.
        field (str): Field name to match.
        value (any): Value to search for.
        args (str): "all" to fetch all matches, anything else for one.

    Returns:
        dict or list or None or str: Fetched result(s), None if not found, or error message.
    """
    try:
        cursor.execute(f"SELECT * FROM {table} WHERE {field} = %s", (value,))

        if args == "all":
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()

        if result:
            return result
        else:
            return None
        
    except Exception as e:
        print("ERROR: " + str(e))
        return f"ERROR|{str(e)}"


def update_field(cursor, table, fields_values, id):
    """
    Update specific fields for a record identified by ID.

    Args:
        cursor (MySQLCursor): Database cursor.
        table (str): Table name.
        fields_values (dict): Dictionary of field names and new values.
        id (int): ID of the row to update.

    Returns:
        str: "SUCCESS" or "ERROR|<message>".
    """
    try:
        set_clause = ", ".join([f"{field} = %s" for field in fields_values.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE id = %s"
        values = tuple(fields_values.values()) + (id,)
        cursor.execute(query, values)
        return "SUCCESS"
    except Exception as e:
        print("ERROR: " + str(e))
        return f"ERROR|{str(e)}"


def add_into_table(cursor, table, data):
    """
    Insert a new record into a table.

    Args:
        cursor (MySQLCursor): Database cursor.
        table (str): Table name.
        data (dict): Key-value pairs for column names and values.

    Returns:
        str: "SUCCESS" or "ERROR|<message>".
    """
    try:
        columns = ", ".join(data.keys())
        values_placeholder = ", ".join(["%s"] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({values_placeholder})"
        cursor.execute(query, values)
        return "SUCCESS"
    except Exception as e:
        print("ERROR: " + str(e))
        return f"ERROR|{str(e)}"


def get_all_from_table(cursor, table):
    """
    Retrieve all records from a table.

    Args:
        cursor (MySQLCursor): Database cursor.
        table (str): Table name.

    Returns:
        list or None or str: List of all records, None if empty, or error message.
    """
    try:
        cursor.execute(f"SELECT * FROM {table}")
        result = cursor.fetchall()
        return result if result else None
    except Exception as e:
        print("ERROR: " + str(e))
        return f"ERROR|{str(e)}"
