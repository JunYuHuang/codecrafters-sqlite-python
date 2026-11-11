from dataclasses import dataclass
import io
import re
import struct
import sys
import sqlparse

# Sizes are in bytes
DATABASE_HEADER_SIZE = 100
LEAF_PAGE_HEADER_SIZE = 8

# Database Header fields
HEADER_STRING_SIZE = 16
PAGE_SIZE_SIZE = 2

# Overwritten based on database's actual page size
PAGE_SIZE = 4096

# Page Header Constants
PAGE_TYPE_SIZE = 1
FIRST_FREE_BLOCK_SIZE = 2
CELL_COUNT_SIZE = 2
CELL_POINTER_SIZE = 2

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

def parse_cell_pointers(
    database_file: io.BufferedReader, rootpage: int = 1
) -> list[int]:
    page_offset = (rootpage - 1) * PAGE_SIZE
    if rootpage == 1:
        page_offset += DATABASE_HEADER_SIZE
    cell_count_start_pos = (
        page_offset + PAGE_TYPE_SIZE + FIRST_FREE_BLOCK_SIZE
    )
    database_file.seek(cell_count_start_pos)
    cell_count = int.from_bytes(
        database_file.read(CELL_COUNT_SIZE), byteorder="big"
    )

    cell_pointers_start_pos = LEAF_PAGE_HEADER_SIZE
    if rootpage > 1:
        cell_pointers_start_pos += page_offset
    if rootpage == 1:
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

def parse_leaf_cell(
    database_file: io.BufferedReader,
    cell_offset: int,
    rootpage: int
) -> dict:
    res = {
        "record_size": -1,
        "rowid": -1,
        "record": {
            "header": { "header_size": -1 },
            "body": {}
        }
    }
    page_offset = (rootpage - 1) * PAGE_SIZE
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
        cell_offset += serial_type_dict["size"]

    return res

# Assumes SQL statement format `select <count(*)|column> from <table>`
def parse_sql_select(statement: str) -> dict:
    statement = statement.lower()
    res = {}
    parts = statement.split(" ")
    assert(len(parts) == 4)

    res["action"] = parts[0]
    res["column"] = parts[1]
    res["table"] = parts[3]
    return res

# Assumes SQL statement format `select <column 1>, ...<column N> from <table>`
def parse_sql_select_multi_column(statement: str) -> dict:
    statement = statement.lower()
    res = { "columns": [] }
    columns_start_pos = len("select") + 1
    columns_end_pos = statement.find(" from") - 1
    columns = statement[columns_start_pos:columns_end_pos + 1].split(", ")
    for column in columns:
        res["columns"].append(column)
    parts = statement.split(" ")
    res["table"] = parts[-1]

    return res

def rootpage_of(database_file: io.BufferedReader, target_table: str) -> int:
    if target_table.lower() == "sqlite_schema":
        return 1

    cell_offsets: list[int] = parse_cell_pointers(database_file)
    for offset in cell_offsets:
        cell_dict = parse_schema_leaf_cell(database_file, offset)
        table_name = cell_dict["record"]["body"]["tbl_name"]
        if table_name == target_table:
            return cell_dict["record"]["body"]["rootpage"]

    print(f"[Error]: Rootpage of table '{target_table}' not found")
    return -1

def sql_of(database_file: io.BufferedReader, target_table: str) -> int:
    cell_offsets: list[int] = parse_cell_pointers(database_file)
    for offset in cell_offsets:
        cell_dict = parse_schema_leaf_cell(database_file, offset)
        table_name = cell_dict["record"]["body"]["tbl_name"]
        if table_name == target_table:
            return cell_dict["record"]["body"]["sql"]

    print(f"[Error]: SQL of table '{target_table}' not found")
    return ""

# TODO: make less fragile (b/c SQL statements can have commas in more places)
# e.g., use `sqlparse` module / library instead
def column_index_of(sql_create: str, target_column: str) -> (list | tuple):
    target_column = target_column.lower()
    sql_create_parts: list[str] = sql_create.split(",")
    sql_create_parts_len = len(sql_create_parts)
    for i in range(sql_create_parts_len):
        if sql_create_parts[i].find(target_column) != -1:
            return i

    print((
        f"[Error]: Column '{target_column}' does not exist in table created" +
        f"in SQL DDL:\n{sql_create}"
    ))
    return -1

def parse_leaf_page_header(
    database_file: io.BufferedReader, rootpage: int
) -> dict:
    res = {}
    page_offset = (rootpage - 1) * PAGE_SIZE
    if rootpage == 1:
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

def main() -> None:
    database_file_path = sys.argv[1]
    command = sys.argv[2]
    database_file: io.BufferedReader = open(database_file_path, "rb")

    database_header_dict = parse_database_header(database_file)
    PAGE_SIZE = database_header_dict["page_size"]

    command = command.lower()
    if command == ".dbinfo":
        print(f"database page size: {database_header_dict["page_size"]}")
        print(f"number of tables: {database_header_dict["cell_count"]}")
    elif command == ".tables":
        table_names = []
        cell_offsets: list[int] = parse_cell_pointers(database_file)
        for offset in cell_offsets:
            cell_dict = parse_schema_leaf_cell(database_file, offset)
            table_name = cell_dict["record"]["body"]["tbl_name"]
            if table_name != "sqlite_sequence":
                table_names.append(table_name)
        res = " ".join(table_names)
        print(res)
    elif re.match(r'^select count\(\*\) from \w+$', command):
        sql_dict: dict = parse_sql_select(command)
        rootpage: int = rootpage_of(database_file, sql_dict["table"])
        leaf_page_header_dict = parse_leaf_page_header(database_file, rootpage)
        print(leaf_page_header_dict["cell_count"])
    elif re.match(r'^select \w+ from \w+$', command):
        sql_dict = parse_sql_select(command)
        column: str = sql_dict["column"]
        table: str = sql_dict["table"]
        sql_create: str = sql_of(database_file, table)
        column_index: int = column_index_of(sql_create, column)
        rootpage: int = rootpage_of(database_file, table)
        rows = []
        cell_offsets: list[int] = parse_cell_pointers(database_file, rootpage)
        for offset in cell_offsets:
            cell_dict = parse_leaf_cell(database_file, offset, rootpage)
            rows.append(cell_dict["record"]["body"][column_index])
        rows_str: str = "\n".join(rows)
        print(rows_str)
    elif re.match(r'^select \w+(\,\s\w+)+ from \w+$', command):
        sql_dict = parse_sql_select_multi_column(command)
        columns: list[str] = sql_dict["columns"]
        table: str = sql_dict["table"]
        sql_create: str = sql_of(database_file, table)

        column_indices: list[int] = []
        for column in columns:
            column_index = column_index_of(sql_create, column)
            column_indices.append(column_index)

        rootpage: int = rootpage_of(database_file, table)
        rows = []
        cell_offsets: list[int] = parse_cell_pointers(database_file, rootpage)
        for offset in cell_offsets:
            cell_dict = parse_leaf_cell(database_file, offset, rootpage)
            row: list[str] = []
            for column_index in column_indices:
                if row:
                    row.append("|")
                row.append(cell_dict["record"]["body"][column_index])
            rows.append("".join(row))
        rows_str: str = "\n".join(rows)
        print(rows_str)
    else:
        print(f"Invalid command: {command}")

    database_file.close()

if __name__ == "__main__":
    main()
