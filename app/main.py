import copy
from dataclasses import dataclass
import io
import re
import struct
import sys
# import sqlparse

# Sizes are in bytes
DATABASE_HEADER_SIZE = 100
LEAF_PAGE_HEADER_SIZE = 8
INTERIOR_PAGE_HEADER_SIZE = 12

# Database Header fields
HEADER_STRING_SIZE = 16
PAGE_SIZE_SIZE = 2

# Overwritten based on database's actual page size
PAGE_SIZE = 4096

# Page Header constants
PAGE_TYPE_SIZE = 1
FIRST_FREE_BLOCK_SIZE = 2
CELL_COUNT_SIZE = 2
CELL_CONTENT_AREA_SIZE = 2
FRAGMENT_FREE_BYTES_SIZE = 1
RIGHT_CHILD_PAGE_NUMBER_SIZE = 4

# Cell constants
CELL_POINTER_SIZE = 2
PAGE_NUMBER_SIZE = 4

def parse_database_header(database_file: io.BufferedReader) -> dict:
    res = {}

    # Skip the first 16 bytes of the header
    database_file.seek(HEADER_STRING_SIZE)  
    page_size = int.from_bytes(
        database_file.read(PAGE_SIZE_SIZE), byteorder="big"
    )
    res["page_size"] = page_size

    cell_count_start_pos = (
        DATABASE_HEADER_SIZE + PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE
    )
    database_file.seek(cell_count_start_pos)
    cell_count = int.from_bytes(database_file.read(2), byteorder="big")
    res["cell_count"] = cell_count

    return res

def int_to_binary_str(integer: int, bit_length: int = 1) -> str:
    if type(bit_length) != int or bit_length <= 0:
        bit_length = 1
    return format(integer, f"0{bit_length}b")

def parse_varint(data: bytes, offset: int) -> dict:
    INF = float("inf")
    error_res = { "varint": INF, "offset": INF, "varint_size": INF }
    DATA_LEN = len(data)
    MAX_VARINT_BYTES = 9

    if offset >= DATA_LEN:
        print(f"[Error]: Offset {offset} in bytestream is out of bounds")
        return error_res

    byte_count = 1
    varint_bits: list[str] = []
    while offset < DATA_LEN and byte_count <= MAX_VARINT_BYTES:
        data_byte_int = int.from_bytes(data[offset:offset + 1], byteorder='big')
        data_byte_str = int_to_binary_str(data_byte_int, 8)

        # msb = Most Significant Bit i.e., leftmost bit in a byte for a
        # big-endian encoded unsigned integer
        msb_int = int(data_byte_str[:1], 2)

        offset += 1

        if byte_count >= MAX_VARINT_BYTES:
            varint_bits.append(data_byte_str)
            break

        # payload bits are the lower remaining 7 bits in the byte
        payload_bits_str = data_byte_str[1:]
        varint_bits.append(payload_bits_str)
        byte_count += 1

        if msb_int == 0:
            byte_count -= 1
            break

    varint_int = int("".join(varint_bits), base=2)
    return { "varint": varint_int, "offset": offset, "varint_size": byte_count }

def page_type(database_file: io.BufferedReader, page: int) -> str:
    if type(page) != int or page < 1:
        print(f"[Error]: Invalid page number '{page}'")
        return "INVALID_PAGE_TYPE"
    
    page_offset = (page - 1) * PAGE_SIZE
    if page == 1:
        page_offset += DATABASE_HEADER_SIZE
    database_file.seek(page_offset)
    page_type_int = int.from_bytes(
        database_file.read(PAGE_TYPE_SIZE), byteorder="big"
    )
    int_to_str = {
        0x0d: "table_leaf",
        0x05: "table_interior",
        0x0a: "index_leaf",
        0x02: "index_interior"
    }

    if page_type_int not in int_to_str:
        print(f"[Error]: Invalid page type for page '{page_type_int}'")
        return "INVALID_PAGE_TYPE"

    return int_to_str[page_type_int]

def parse_leaf_cell_pointers(
    database_file: io.BufferedReader, page: int = 1
) -> list[int]:
    page_offset = (page - 1) * PAGE_SIZE
    if page == 1:
        page_offset += DATABASE_HEADER_SIZE
    cell_count_start_pos = (
        page_offset + PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE
    )
    database_file.seek(cell_count_start_pos)
    cell_count = int.from_bytes(
        database_file.read(CELL_COUNT_SIZE), byteorder="big"
    )

    cell_pointers_start_pos = LEAF_PAGE_HEADER_SIZE
    if page > 1:
        cell_pointers_start_pos += page_offset
    if page == 1:
        cell_pointers_start_pos += DATABASE_HEADER_SIZE
    database_file.seek(cell_pointers_start_pos)
    pos = cell_pointers_start_pos
    res = []
    for _ in range(cell_count):
        database_file.seek(pos)
        pointer_int = int.from_bytes(
            database_file.read(CELL_POINTER_SIZE), byteorder="big"
        )
        res.append(pointer_int)
        pos += CELL_POINTER_SIZE

    return res

def parse_interior_cell_pointers(
    database_file: io.BufferedReader, page: int = 1
) -> list[int]:
    page_offset = (page - 1) * PAGE_SIZE
    if page == 1:
        page_offset += DATABASE_HEADER_SIZE
    cell_count_start_pos = (
        page_offset + PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE
    )
    database_file.seek(cell_count_start_pos)
    cell_count = int.from_bytes(
        database_file.read(CELL_COUNT_SIZE), byteorder="big"
    )

    cell_pointers_start_pos = INTERIOR_PAGE_HEADER_SIZE
    if page > 1:
        cell_pointers_start_pos += page_offset
    if page == 1:
        cell_pointers_start_pos += DATABASE_HEADER_SIZE
    database_file.seek(cell_pointers_start_pos)
    pos = cell_pointers_start_pos
    res = []
    for _ in range(cell_count):
        database_file.seek(pos)
        pointer_int = int.from_bytes(
            database_file.read(CELL_POINTER_SIZE), byteorder="big"
        )
        res.append(pointer_int)
        pos += CELL_POINTER_SIZE

    return res

# Serial Type Reference: https://www.sqlite.org/fileformat.html#record_format
def parse_serial_type(serial_type: int) -> dict:
    INF = float("inf")
    SIGNED_INT = "signed_int"
    INVALID_TYPE = "INVALID_TYPE"

    if type(serial_type) != int or serial_type < 0:
        print(f"[Error]: Serial type {serial_type} is not valid")
        return { "size": INF, "meaning": INVALID_TYPE }
    
    # `size` is in bytes
    type_to_size_and_meaning = {
        0: { "size": 0, "meaning": "null" },
        1: { "size": 1, "meaning": SIGNED_INT },
        2: { "size": 2, "meaning": SIGNED_INT },
        3: { "size": 3, "meaning": SIGNED_INT },
        4: { "size": 4, "meaning": SIGNED_INT },
        5: { "size": 6, "meaning": SIGNED_INT },
        6: { "size": 8, "meaning": SIGNED_INT },
        7: { "size": 8, "meaning": "float" },
        8: { "size": 0, "meaning": "zero" },
        9: { "size": 0, "meaning": "one" },
        10: { "size": INF, "meaning": "internal" },
        11: { "size": INF, "meaning": "internal" },
    }

    if 0 <= serial_type <= 11:
        return type_to_size_and_meaning[serial_type]
    if serial_type >= 12 and serial_type % 2 == 0:
        return { "size": ((serial_type - 12) // 2), "meaning": "blob" }
    if serial_type >= 13 and serial_type % 2 != 0:
        # assume UTF-8 text encoding unless proven otherwise
        return { "size": ((serial_type - 13) // 2), "meaning": "text" }

    print(f"[Error]: Serial type {serial_type} is not valid")
    return { "size": INF, "meaning": INVALID_TYPE }

def parse_schema_leaf_cell(
    database_file: io.BufferedReader, offset: int
) -> dict:
    res = {
        "record_size": -1,
        "rowid": -1,
        "record": {
            "header": { "header_size": -1 },
            "body": {}
        }
    }

    database_file.seek(0)
    leaf_bytes = database_file.read(PAGE_SIZE)

    # Parse cell non-record values
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record_size"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    varint_dict = parse_varint(leaf_bytes, offset)
    res["rowid"] = varint_dict["varint"]
    offset = varint_dict["offset"]

    # Parse cell record header values:
    # `header_size`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["header_size"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    # `type`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["type"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    # `name`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["name"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    # `tbl_name`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["tbl_name"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    # `rootpage`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["rootpage"] = varint_dict["varint"]
    offset = varint_dict["offset"]
    # `sql`
    varint_dict = parse_varint(leaf_bytes, offset)
    res["record"]["header"]["sql"] = varint_dict["varint"]
    offset = varint_dict["offset"]

    # Parse cell record body values:
    # `type`
    serial_type = res["record"]["header"]["type"]
    serial_type_dict = parse_serial_type(serial_type)
    database_file.seek(offset)
    body_bytes = database_file.read(serial_type_dict["size"])
    res["record"]["body"]["type"] = body_bytes.decode()
    offset += serial_type_dict["size"]
    # `name`
    serial_type = res["record"]["header"]["name"]
    serial_type_dict = parse_serial_type(serial_type)
    database_file.seek(offset)
    body_bytes = database_file.read(serial_type_dict["size"])
    res["record"]["body"]["name"] = body_bytes.decode()
    offset += serial_type_dict["size"]
    # `tbl_name`
    serial_type = res["record"]["header"]["tbl_name"]
    serial_type_dict = parse_serial_type(serial_type)
    database_file.seek(offset)
    body_bytes = database_file.read(serial_type_dict["size"])
    res["record"]["body"]["tbl_name"] = body_bytes.decode()
    offset += serial_type_dict["size"]
    # `rootpage`
    serial_type = res["record"]["header"]["rootpage"]
    serial_type_dict = parse_serial_type(serial_type)
    database_file.seek(offset)
    body_bytes = database_file.read(serial_type_dict["size"])
    value = int.from_bytes(body_bytes, byteorder='big')
    res["record"]["body"]["rootpage"] = value
    offset += serial_type_dict["size"]
    # `sql`
    serial_type = res["record"]["header"]["sql"]
    serial_type_dict = parse_serial_type(serial_type)
    database_file.seek(offset)
    body_bytes = database_file.read(serial_type_dict["size"])
    res["record"]["body"]["sql"] = body_bytes.decode()
    offset += serial_type_dict["size"]

    return res

def parse_table_leaf_cell(
    database_file: io.BufferedReader,
    cell_offset: int,
    page: int,
    integer_primary_key_column_pos: int = -1
) -> dict:
    res = {
        "record_size": -1,
        "rowid": -1,
        "record": {
            "header": { "header_size": -1 },
            "body": {}
        }
    }
    page_offset = (page - 1) * PAGE_SIZE
    database_file.seek(page_offset)
    leaf_bytes = database_file.read(PAGE_SIZE)

    # Parse cell non-record values
    varint_dict = parse_varint(leaf_bytes, cell_offset)
    res["record_size"] = varint_dict["varint"]
    cell_offset = varint_dict["offset"]
    varint_dict = parse_varint(leaf_bytes, cell_offset)
    res["rowid"] = varint_dict["varint"]
    cell_offset = varint_dict["offset"]

    # Parse cell record header values: `header_size` + serial type codes (columns)
    varint_dict = parse_varint(leaf_bytes, cell_offset)
    res["record"]["header"]["header_size"] = varint_dict["varint"]
    cell_offset = varint_dict["offset"]

    header_size: int = res["record"]["header"]["header_size"]
    header_bytes_left = header_size - varint_dict["varint_size"]
    serial_type_index = 0
    while header_bytes_left > 0:
        varint_dict = parse_varint(leaf_bytes, cell_offset)
        res["record"]["header"][serial_type_index] = varint_dict["varint"]
        cell_offset = varint_dict["offset"]
        serial_type_index += 1
        header_bytes_left -= varint_dict["varint_size"]

    # Parse cell record body values:
    for column_value_index in range(serial_type_index):
        serial_type: int = res["record"]["header"][column_value_index]
        serial_type_dict = parse_serial_type(serial_type)
        database_file.seek(page_offset + cell_offset)
        body_bytes = database_file.read(serial_type_dict["size"])
        value = None
        if serial_type_dict["meaning"] == "blob":
            value = body_bytes
        elif serial_type_dict["meaning"] == "text":
            value = body_bytes.decode()
        elif serial_type_dict["meaning"] == "signed_int":
            # TODO: handle negative integers (via two's complement)
            value = int.from_bytes(body_bytes, byteorder="big")
        elif serial_type_dict["meaning"] == "float":
            # TODO: fix to convert bytes to 64-bit IEEE 754 float
            # Currently converts to 32-bit IEEE 754 float
            value = struct.unpack('>f', body_bytes)
        elif serial_type_dict["meaning"] == "zero":
            value = 0
        elif serial_type_dict["meaning"] == "one":
            value = 1
        else:
            value = None
        res["record"]["body"][column_value_index] = value
        if (
            integer_primary_key_column_pos != -1 and
            column_value_index == integer_primary_key_column_pos
        ):
            res["record"]["body"][column_value_index] = res["rowid"]
        cell_offset += serial_type_dict["size"]

    return res

def parse_table_interior_cell(
    database_file: io.BufferedReader,
    cell_offset: int,
    page: int
) -> dict:
    res = { "page_number": -1, "rowid": - 1 }
    page_offset = (page - 1) * PAGE_SIZE
    database_file.seek(page_offset)
    interior_bytes = database_file.read(PAGE_SIZE)

    # Parse child page number
    page_number_bytes = interior_bytes[cell_offset:cell_offset + PAGE_NUMBER_SIZE]
    res["page_number"] = int.from_bytes(page_number_bytes, byteorder='big')
    cell_offset += PAGE_NUMBER_SIZE

    varint_dict = parse_varint(interior_bytes, cell_offset)
    res["rowid"] = varint_dict["varint"]

    return res

# Assumes SQL statement format:
# `SELECT <col 1>[, ...<col N>] FROM <table> [WHERE <col x> = '<value>']`
def parse_sql_select(statement: str) -> dict:
    statement_lowered = statement.lower()
    res = { "columns": [] }
    columns_start_pos = len("select") + 1
    columns_end_pos = statement_lowered.find(" from") - 1
    columns = (
        statement_lowered[columns_start_pos:columns_end_pos + 1].split(", ")
    )
    for column in columns:
        res["columns"].append(column)
    
    from_pos = statement_lowered.find("from")
    where_start_pos = statement_lowered.find("where")
    table_start_pos = from_pos + len("from") + 1
    if where_start_pos == -1:
        res["table"] = statement_lowered[table_start_pos:]
    else:
        res["table"] = statement_lowered[table_start_pos:where_start_pos - 1]
        where_end_pos = where_start_pos + len("where") - 1
        where_filter = statement[where_end_pos + 2:].split(" = ")
        res["where_column"], res["where_value"] = where_filter

        # Remove enclosing single quotes if needed
        if res["where_value"][0] == "'" and res["where_value"][-1] == "'":
            res["where_value"] = res["where_value"][1:-1] 

    return res

def rootpage_of(database_file: io.BufferedReader, target_table: str) -> int:
    target_table = target_table.lower()
    if target_table == "sqlite_schema":
        return 1

    cell_offsets: list[int] = parse_leaf_cell_pointers(database_file)
    for offset in cell_offsets:
        cell_dict = parse_schema_leaf_cell(database_file, offset)
        table_name = cell_dict["record"]["body"]["tbl_name"]
        if table_name == target_table:
            return cell_dict["record"]["body"]["rootpage"]

    print(f"[Error]: Rootpage of table '{target_table}' not found")
    return -1

def sql_of(database_file: io.BufferedReader, target_table: str) -> int:
    cell_offsets: list[int] = parse_leaf_cell_pointers(database_file)
    for offset in cell_offsets:
        cell_dict = parse_schema_leaf_cell(database_file, offset)
        table_name = cell_dict["record"]["body"]["tbl_name"]
        if table_name == target_table:
            return cell_dict["record"]["body"]["sql"]

    print(f"[Error]: SQL of table '{target_table}' not found")
    return ""

# TODO: make less fragile (b/c SQL statements can have commas in more places)
# e.g., use `sqlparse` module / library instead
def column_index_of(sql_create: str, target_column: str) -> int:
    target_column = target_column.lower()
    sql_create_parts: list[str] = sql_create.split(",")
    sql_create_parts_len = len(sql_create_parts)
    for i in range(sql_create_parts_len):
        if sql_create_parts[i].find(target_column) != -1:
            return i

    print((
        f"[Error]: Column '{target_column}' does not exist in table created" +
        f"by SQL DDL:\n{sql_create}"
    ))
    return -1

# TODO: fix bug with this??
def integer_primary_key_column_index(sql_create: str) -> int:
    return column_index_of(sql_create, "integer primary key")

def parse_leaf_page_header(
    database_file: io.BufferedReader, page: int
) -> dict:
    res = {}
    page_offset = (page - 1) * PAGE_SIZE
    if page == 1:
        page_offset += DATABASE_HEADER_SIZE
    database_file.seek(page_offset)
    page_header_bytes = database_file.read(LEAF_PAGE_HEADER_SIZE)

    cell_count_start_pos = PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE
    cell_count_bytes = page_header_bytes[
        cell_count_start_pos:cell_count_start_pos + CELL_COUNT_SIZE
    ]
    cell_count_int = int.from_bytes(cell_count_bytes, byteorder='big')
    res["cell_count"] = cell_count_int

    return res

def right_child_page_number(
    database_file: io.BufferedReader, page: int
) -> int:
    if page_type(database_file, page) == "INVALID_PAGE_TYPE":
        return -1

    page_offset = (page - 1) * PAGE_SIZE
    if page == 1:
        page_offset += DATABASE_HEADER_SIZE
    right_child_page_number_start_pos = (
        page_offset + PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE +
        CELL_COUNT_SIZE + CELL_CONTENT_AREA_SIZE + FRAGMENT_FREE_BYTES_SIZE
    )
    database_file.seek(right_child_page_number_start_pos)
    return int.from_bytes(
        database_file.read(RIGHT_CHILD_PAGE_NUMBER_SIZE),
        byteorder='big'
    )

def dfs_full_table_scan(
    database_file: io.BufferedReader, params: dict, result_rows: list
) -> None:
    page_type_str = page_type(database_file, params["page"])

    if page_type_str != "table_leaf" and page_type_str != "table_interior":
        return

    if page_type_str == "table_leaf":
        cell_offsets: list[int] = parse_leaf_cell_pointers(
            database_file, params["page"]
        )
        for offset in cell_offsets:
            cell_dict = parse_table_leaf_cell(
                database_file, offset, params["page"],
                params["integer_primary_key_column_pos"]
            )
            record_dict = cell_dict["record"]["body"]

            if (
                params["where_value"] and
                record_dict[params["where_column_pos"]] != params["where_value"]
            ):
                continue

            row: list[str] = []
            for column_index in params["column_indices"]:
                if row:
                    row.append("|")
                row.append(str(record_dict[column_index]))
            result_rows.append("".join(row))
        return

    if page_type_str == "table_interior":
        cell_offsets: list[int] = parse_interior_cell_pointers(
            database_file, params["page"]
        )
        old_page = copy.copy(params["page"])
        for offset in cell_offsets:
            cell_dict = parse_table_interior_cell(
                database_file, offset, old_page
            )
            new_params = copy.copy(params)
            new_params["page"] = cell_dict["page_number"]
            dfs_full_table_scan(database_file, new_params, result_rows)

        rightmost_page: int = right_child_page_number(
            database_file, old_page
        )
        new_params = copy.copy(params)
        new_params["page"] = rightmost_page
        dfs_full_table_scan(database_file, new_params, result_rows)


def main() -> None:
    database_file_path = sys.argv[1]
    command = sys.argv[2]
    database_file: io.BufferedReader = open(database_file_path, "rb")

    database_header_dict = parse_database_header(database_file)
    global PAGE_SIZE
    PAGE_SIZE = database_header_dict["page_size"]

    if command == ".dbinfo":
        print(f"database page size: {database_header_dict["page_size"]}")
        print(f"number of tables: {database_header_dict["cell_count"]}")
    elif command == ".tables":
        table_names = []
        cell_offsets: list[int] = parse_leaf_cell_pointers(database_file)
        for offset in cell_offsets:
            cell_dict = parse_schema_leaf_cell(database_file, offset)
            table_name = cell_dict["record"]["body"]["tbl_name"]
            if table_name != "sqlite_sequence":
                table_names.append(table_name)
        res = " ".join(table_names)
        print(res)
    elif re.match(r'^SELECT COUNT\(\*\) FROM \w+$', command, re.IGNORECASE):
        sql_dict: dict = parse_sql_select(command)
        rootpage: int = rootpage_of(database_file, sql_dict["table"])
        leaf_page_header_dict = parse_leaf_page_header(database_file, rootpage)
        print(leaf_page_header_dict["cell_count"])
    elif re.match(
        r'^SELECT \w+(\, \w+)* FROM \w+( WHERE \w+ \= \'?.+\'?)?$',
        command,
        re.IGNORECASE
    ):
        sql_dict = parse_sql_select(command)
        column_names: list[str] = sql_dict["columns"]
        table: str = sql_dict["table"]
        sql_create: str = sql_of(database_file, table)

        col_name_to_pos: dict = {}
        for column_name in column_names:
            col_name_to_pos[column_name] = column_index_of(
                sql_create, column_name
            )

        where_column_pos = -1
        where_value = None
        if "where_column" in sql_dict:
            where_column_pos = column_index_of(
                sql_create, sql_dict["where_column"]
            )
            where_value = sql_dict["where_value"]

        rootpage: int = rootpage_of(database_file, table)

        # TODO: fix bug with this?
        rowid_column_pos: int = integer_primary_key_column_index(sql_create)

        params = {
            "page": rootpage,
            "column_indices": list(col_name_to_pos.values()),
            "where_column_pos": where_column_pos,
            "where_value": where_value,
            "integer_primary_key_column_pos": rowid_column_pos
        }
        rows = []
        dfs_full_table_scan(database_file, params, rows)
        # print(rows)

        # TODO: fix bug that sometimes causes tests to fail for some reason
        rows_str: str = "\n".join(rows)

        print(rows_str)
    else:
        print(f"Invalid command: {command}")

    database_file.close()

if __name__ == "__main__":
    main()
