from dataclasses import dataclass
import io
import sys
# import sqlparse - available if you need it!

DATABASE_HEADER_SIZE = 100
CELL_SIZE_POS = DATABASE_HEADER_SIZE + 1 + 2
LEAF_PAGE_HEADER_SIZE = 8

def parse_database_header(database_file: io.BufferedReader) -> dict:
    res = {}

    database_file.seek(16)  # Skip the first 16 bytes of the header
    page_size = int.from_bytes(database_file.read(2), byteorder="big")
    res["page_size"] = page_size

    database_file.seek(CELL_SIZE_POS)
    cell_count = int.from_bytes(database_file.read(2), byteorder="big")
    res["cell_count"] = cell_count

    return res

def int_to_binary_str(integer: int, bit_length: int = 1) -> str:
    if type(bit_length) != int or bit_length <= 0:
        bit_length = 1
    return format(integer, f"0{bit_length}b")

# TODO: to test with more edge cases
def parse_varint(data: bytes, offset: int) -> dict:
    INF = float("inf")
    error_res = { "varint": INF, "offset": INF, "varint_size": INF }
    DATA_LEN = len(data)
    MAX_VARINT_BYTES = 9

    # print(f"Bytes {data} is of length {DATA_LEN}")

    if offset >= DATA_LEN:
        print(f"[Error]: Offset {offset} in bytestream is out of bounds")
        return error_res

    byte_count = 1
    varint_bits: list[str] = []
    while offset < DATA_LEN and byte_count <= MAX_VARINT_BYTES:
        data_byte_int = int.from_bytes(data[offset:offset + 1], byteorder='big')
        data_byte_str = int_to_binary_str(data_byte_int, 8)

        # msb = Most Significant Bit i.e., leftmost bit in a byte for a
        # big-endian encoded signed integer
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

def parse_schema_cell_pointers(database_file: io.BufferedReader) -> list[int]:
    database_file.seek(CELL_SIZE_POS)
    cell_count = int.from_bytes(database_file.read(2), byteorder="big")

    cell_pointers_start_pos = DATABASE_HEADER_SIZE + LEAF_PAGE_HEADER_SIZE
    database_file.seek(cell_pointers_start_pos)
    pos = cell_pointers_start_pos
    res = []
    for _ in range(cell_count):
        database_file.seek(pos)
        pointer_int = int.from_bytes(database_file.read(2), byteorder="big")
        res.append(pointer_int)
        pos += 2

    return res

# TODO: to implement + test
def parse_leaf_cell(database_file: io.BufferedReader, offset: int) -> dict:
    res = {}

    database_file.seek(offset)

    # TODO: how much of the file to read into a buffer? page size - offset?

    return res

def main() -> None:
    database_file_path = sys.argv[1]
    command = sys.argv[2]
    database_file: io.BufferedReader = open(database_file_path, "rb")

    # # TODO: test varint_parser()
    # varint_bytes_1 = int('10000001', base=2).to_bytes()
    # varint_bytes_1 += int('00000001', base=2).to_bytes()
    # varint_bytes_1 += int('10000001', base=2).to_bytes()
    # res = parse_varint(varint_bytes_1, 0)
    # print(res)

    # varint_bytes_2 = int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('10000001', base=2).to_bytes()
    # varint_bytes_2 += int('00000001', base=2).to_bytes()
    # varint_bytes_2 += int('00000001', base=2).to_bytes()
    # res = parse_varint(varint_bytes_2, 0)
    # print(res)

    # res = parse_varint(varint_bytes_2, 7)
    # print(res)

    if command == ".dbinfo":
        database_header_dict = parse_database_header(database_file)
        print(f"database page size: {database_header_dict["page_size"]}")
        print(f"number of tables: {database_header_dict["cell_count"]}")
    # TODO: to test
    elif command == ".tables":
        table_names = []
        cell_offsets: list[int] = parse_schema_cell_pointers(database_file)
        # for offset in cell_offsets:
        #     cell_dict = parse_leaf_cell(database_file, offset)
        #     table_name = cell_dict["record"]["body"]["tbl_name"]
        #     if table_name != "sqlite_sequence":
        #         table_names.append(table_name)
        # res = " ".join(table_names)
        # print(res)
    else:
        print(f"Invalid command: {command}")

    database_file.close()

if __name__ == "__main__":
    main()
