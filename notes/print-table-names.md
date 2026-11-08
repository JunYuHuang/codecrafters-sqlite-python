# Your Task

In this stage, you'll implement the `.tables` [dot command](https://www.sqlite.org/cli.html#special_commands_to_sqlite3_dot_commands_), which prints the names of the user tables in a SQLite database.

## The `sqlite_schema.tbl_name` column

The names of the tables in a SQLite database are stored in the `tbl_name` column of the [`sqlite_schema`](https://www.sqlite.org/schematab.html) table. The `sqlite_schema` [page](https://www.sqlite.org/fileformat.html#b_tree_pages) stores the rows of the `sqlite_schema` table in chunks of data called "cells." Each cell contains a single row. You need to read all the cells and extract the value of `sqlite_schema.tbl_name` from each one.


## Cell pointer array

To figure out where the cells are located, read the `sqlite_schema` page's cell pointer array. This array specifies the offsets of every cell on the page. Here's what you need to know:

- The array appears directly after the page header.
- The elements (offsets) are 2-byte big-endian values.
- The offsets are relative to the start of the page.
- The array size is equal to the number of cells on the page (The page header specifies the number of cells on the page).

## Cell

Once you have all the offsets, you can read the cells. The type of cell on the `sqlite_schema` page is called a "table b-tree leaf cell." It's made up of three parts:

1. The size of the record, in bytes (varint)
2. The rowid (varint)
3. The record (record format)

Cells use variable-length integers, also called "varints." See the [official documentation](https://www.sqlite.org/fileformat.html#b_tree_pages) to learn how they work.

You can ignore the rowid—it's not relevant to this stage.

The part you're interested in is the record. "Record" is just another word for "row." That's the part that contains the `sqlite_schema.tbl_name` column.

### Record format

Records are stored in [record format](https://www.sqlite.org/fileformat.html#record_format):

1. Header:
    1. Size of the header, including this value (varint)
    2. Serial type code for each column in the record, in order (varint)
1. Body:
    1. The value of each column in the record, in order (format varies based on serial type code)

A "serial type code" specifies the data type and size of a column. See the [official documentation](https://www.sqlite.org/fileformat.html#record_format) for the table of all serial type codes.

### Example

The following is a cell from page 1 of `sample.db`:
```
00000ec0           78 03 07 17 1b  1b 01 81 47 74 61 62 6c  |   x.......Gtabl|
00000ed0  65 6f 72 61 6e 67 65 73  6f 72 61 6e 67 65 73 04  |eorangesoranges.|
00000ee0  43 52 45 41 54 45 20 54  41 42 4c 45 20 6f 72 61  |CREATE TABLE ora|
00000ef0  6e 67 65 73 0a 28 0a 09  69 64 20 69 6e 74 65 67  |nges.(..id integ|
00000f00  65 72 20 70 72 69 6d 61  72 79 20 6b 65 79 20 61  |er primary key a|
00000f10  75 74 6f 69 6e 63 72 65  6d 65 6e 74 2c 0a 09 6e  |utoincrement,..n|
00000f20  61 6d 65 20 74 65 78 74  2c 0a 09 64 65 73 63 72  |ame text,..descr|
00000f30  69 70 74 69 6f 6e 20 74  65 78 74 0a 29           |iption text.)   |
```

Here's an analysis of the cell:
```
// Size of the record (varint): 120
78

// The rowid (safe to ignore)
03

// Record header
07     // Size of record header (varint): 7

17     // Serial type for sqlite_schema.type (varint):     23
       // Size of sqlite_schema.type =                     (23-13)/2 = 5

1b     // Serial type for sqlite_schema.name (varint):     27
       // Size of sqlite_schema.name =                     (27-13)/2 = 7

1b     // Serial type for sqlite_schema.tbl_name (varint): 27
       // Size of sqlite_schema.tbl_name =                 (27-13)/2 = 7

01     // Serial type for sqlite_schema.rootpage (varint): 1
       // 8-bit twos-complement integer

81 47  // Serial type for sqlite_schema.sql (varint):      199
       // Size of sqlite_schema.sql =                      (199-13)/2 = 93

// Record body
74 61 62 6c 65        // Value of sqlite_schema.type:     "table"
6f 72 61 6e 67 65 73  // Value of sqlite_schema.name:     "oranges"
6f 72 61 6e 67 65 73  // Value of sqlite_schema.tbl_name: "oranges"  <---
...
```

## Tests

Here's how the tester will execute your program:
```
$ ./your_sqlite3.sh sample.db .tables
```

Your program must print the names of the tables in the database file:
```
apples oranges
```

## Notes

- The actual `.tables` command accepts an optional pattern argument, and also adds additional spaces between each table name, for formatting purposes. You do not need to implement either of these features for your `.tables` command.
- If a cell's payload is too large to fit on a single page, the remainder of the payload will be stored on [cell payload overflow pages](https://www.sqlite.org/fileformat.html#cell_payload_overflow_pages). You do not need to handle payload overflow in this challenge.
- The record part of a cell is called "payload," in the official documentation.

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/sz4/code-examples).

### 2. Submit code

To run tests, make changes to your code and run the submit command:
```
codecrafters submit # Visit https://codecrafters.io/cli to install
```

To run tests, make changes to your code and run the following commands:
```
git add .
git commit --allow-empty -m "[any message]"
git push origin master
```

# Notes:

- PEDAC: Problem
    - input:
        - `argv`: string array of CLI arguments taken + passed when running the program
            - `argv[0]`: path to program i.e., `./your_program.sh`
            - `argv[1]`: path to a SQLite database e.g., `sample.db`
            - `argv[2]`: SQLite command to run e.g., `.dbinfo`
    - output:
        - none
    - side effects:
        - prints to terminal stdout:
            ```
            database page size: <size of each page in database, in bytes>
            number of tables: <count of (table) pages in database>
            ```
    - questions
        - how to traverse + parse a table b-tree page in a SQLite database file?
            - TODO
        - how are table pages in a SQLite database structured (in binary)?
            - TODO
        - how to determine if a page header's size is 8 or 12 Bytes?
            - assume it's 8 Bytes for now?
        - varints (variable-length integers) and how they are used by cells?
            - a varint uses 1 to 9 bytes, inclusive
            - a variant is encoded in big-endian bytes
            - a byte's leftmost bit or MSB (Most Significant Bit) determines if its following byte is part of the signed integer that represents the varint
                - if MSB == 1, following byte is part of varint
                - if MSB == 0, current byte is last byte of varint
            - final signed integer is reconstructed from all byte(s) by concatenating, in order:
                - lower / last 7 bits of bytes 1-8
                - all bites of byte 9
            - bitwise operator formula for parsing bytes that compose a signed varint:
                - applies to bytes 1 to 8 only; 9th byte uses all 8 bits for payload bits
                - varint_new_byte = (varint_prev_byte << 7) | (varint_byte & 0x7F)
                    - `<<` = bitwise left-shift
                    - `|` = bitwise logical OR
                    - `0x7F` = 127 = 0b01111111
                - example:
                    ```python
                    byte_1 = 0b1000_0001    # 129
                    byte_2 = 0b0000_0001    # 1
                    result = 0

                    # result = (0 << 7) | (0b1000_0001 & 0b0111_1111)
                    # result = (0 * 2^7) | (0b0000_0001)
                    # result = 0 | 1 = 1
                    result = (result << 7) | (byte_1 & 0x7f)

                    # result = (1 << 7) | (0b0000_0001 & 0b0111_1111)
                    # result = (1 * 2^7) | (0b0000_0001)
                    # result = 128 | 1
                    # result = 0b1000_0000 | 0b0000_0001
                    # result = 0b1000_0001 = 129
                    result = (result << 7 ) | (byte_2 & 0x7f)

                    print(result)   # 129
                    ```
        - bitwise operators to know and use?
            - AND; &; bit is 1 if both bits are 1, else bit is 0
                - e.g., 5 & 3 -> 0001 -> 1
            - OR; |; bit is 0 if both bits are 0, else bit is 1
                - e.g., 5 | 3 -> 0111 -> 7
            - XOR; ^; bit is 1 if both bits are different
                - e.g., 5 ^ 3 -> 0110 -> 6
            - NOT; ~; flip every bit
                - e.g., ~5 -> -6
            - left shift; <<; move bits left + enter zeroes on right (doubles value)
                - e.g., 5 << 1 -> 1010 -> 10
            - right shift; >>; move bits right + enter zeroes on left (divides value by 2^n)
                - e.g., 5 >> 1 -> 0010 -> 2
            - skip for now and using int -> binary string representation conversion hack
        - in a cell's record / row part, how to get column name?
            - ??
    - SQLite database = 1+ pages
        - `sqlite_schema` table
            - stores database schema
            - is in page 1
            - cell count in its page header
                - = 2-byte big-endian value
        - each page = 1+ cells (i.e., rows)
    - SQLite database page 1 structure:
        - database header (100 Bytes) +
        - page header (8 Bytes) +
        - n * cell pointers (n * 2 Bytes)
    - page header structure (8 Bytes):
        - page type (1 Byte) +
        - first free block (2 Bytes) +
        - cell count (2 Bytes) +
        - cell content area (2 Bytes) +
        - fragement free bytes (1 Byte)
    - useful learning links:
        - https://sqlite-internal.pages.dev/
        - https://fly.io/blog/sqlite-internals-btree/
        - https://link.springer.com/content/pdf/10.1007/978-3-030-98467-0_5.pdf
        - https://torymur.github.io/sqlite-repr/
- PEDAC: Examples
    - ex.1: run `.dbinfo` command
        - run in terminal:
            ```
            ./your_program.sh sample.db .dbinfo
            ```
        - terminal output:
            ```
            database page size: 4096
            number of tables: 3
            ```
    - ex.2: run `.tables` command
        - run in terminal:
            ```
            ./your_program.sh sample.db .tables
            ```
        - terminal output:
            ```
            apples oranges
            ```
- PEDAC: Data Structures And Algorithms
    - helper functions
        - `parse_varint(data: bytes, offset: integer) -> dict[string -> integer]`
            - set int `DATA_LEN` = length of `data`
            - set int array `error_list` to `[INFINITY, INFINITY]`
            - if `offset` <= `DATA_LEN`,
                - return `error_list`
            - set string array `varint_bits` empty
            - set int `byte_count` to 1
            - while `offset` < `DATA_LEN` and `byte_count` <= 9,
                - set bytes `data_byte` to `data[offset]`
                - set int `msb_int` to bit at `data_byte[0]` converted to an int
                - set string `lower_bits_str` to 7 remaining bits of `data_byte` converted to a string
                - if `byte_count` is 9,
                    - append all bits of `data_byte` converted to string to `varints_bits`
                - else,
                    - append `lower_bits_str` to `res`
                    - exit loop if `msb_int` is 0
                - increment `byte_count` by 1
                - increment `offset` by 1
            - set string `varint_bits_str` to all string elements of `varint_bits` joined together in order with empty space `` char
            - return `varint_bits_str` as string bits converted to a signed integer
        - `parse_database_header(database_file: file) -> hashmap`
            - optional: for aesthetics
        - `parse_schema_cell_pointers(database_file: file) -> array[integer]`
            - GGEZ done
        - `parse_schema_table(database_file: file) -> hashmap`
            - may not needed?
        - `parse_serial_type(serial_type: integer) -> dict`
            - done
        - `parse_leaf_cell(database_file: file, offset: integer) -> hashmap`
            - move file cursor / pointer to start position (0) in `database_file`
            - set bytes `leaf_bytes` to `PAGE_SIZE` bytes read from current file cursor position
            - set hashmap `res` empty
            - set `res["record"]` to empty hashmap
            - set `res["record"]["header"]` to empty hashmap
            - parse non-record field values
                - set hashmap `varint_dict` to `parse_varint(leaf_bytes, offset)`
                - set key `res["record_size"]` to int `varint_dict["varint"]`
                - set `offset` to `varint_dict["offset"]`
                - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                - set key `res["rowid"]` to int `varint_dict["varint"]`
                - set `offset` to `varint_dict["offset"]`
            - parse record header field values
                - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                - set key `res["record"]["header"]["header_size"]` to int `varint_dict["varint"]`
                - set `offset` to `varint_dict["offset"]`
                - parse 1st header serial type for column `type`
                    - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                    - set key `res["record"]["header"]["type"]` to int `varint_dict["varint"]`
                    - set `offset` to `varint_dict["offset"]`
                - parse 2nd header serial type for column `name`
                    - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                    - set key `res["record"]["header"]["name"]` to int `varint_dict["varint"]`
                    - set `offset` to `varint_dict["offset"]`
                - parse 3rd header serial type for column `tbl_name`
                    - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                    - set key `res["record"]["header"]["tbl_name"]` to int `varint_dict["varint"]`
                    - set `offset` to `varint_dict["offset"]`
                - parse 4th header serial type for column `rootpage`
                    - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                    - set key `res["record"]["header"]["rootpage"]` to int `varint_dict["varint"]`
                    - set `offset` to `varint_dict["offset"]`
                - parse 5th header serial type for column `sql`
                    - set `varint_dict` to `parse_varint(leaf_bytes, offset)`
                    - set key `res["record"]["header"]["sql"]` to int `varint_dict["varint"]`
                    - set `offset` to `varint_dict["offset"]`
            - parse record body field values
                - set key `res["record"]["body"]` to empty hashmap
                - parse 1st body value `type`
                    - set int `serial_type` to `res["record"]["header"]["type"]`
                    - set hashmap `serial_type_dict` to `parse_serial_type(serial_type)`
                    - move file cursor / pointer to position `offset` in `database_file`
                    - set bytes `body_bytes` to `serial_type_dict["size"]` bytes read from current file cursor position
                    - set key `res["record"]["body"]["type"]` to `body_bytes` converted to a string
                    - set `offset` to itself + `serial_type_dict["size"]`
                - parse 2nd body value `name`
                    - set int `serial_type` to `res["record"]["header"]["name"]`
                    - set hashmap `serial_type_dict` to `parse_serial_type(serial_type)`
                    - set `offset` to itself + `serial_type_dict["size"]`
                    - move file cursor / pointer to position `offset` in `database_file`
                    - set bytes `body_bytes` to `serial_type_dict["size"]` bytes read from current file cursor position
                    - set key `res["record"]["body"]["name"]` to `body_bytes` converted to a string
                    - set `offset` to itself + `serial_type_dict["size"]`
                - parse 3rd body value `tbl_name`
                    - set int `serial_type` to `res["record"]["header"]["tbl_name"]`
                    - set hashmap `serial_type_dict` to `parse_serial_type(serial_type)`
                    - set `offset` to itself + `serial_type_dict["size"]`
                    - move file cursor / pointer to position `offset` in `database_file`
                    - set bytes `body_bytes` to `serial_type_dict["size"]` bytes read from current file cursor position
                    - set key `res["record"]["body"]["tbl_name"]` to `body_bytes` converted to a string
                - parse 4th body value `rootpage`
                    - set int `serial_type` to `res["record"]["header"]["rootpage"]`
                    - set hashmap `serial_type_dict` to `parse_serial_type(serial_type)`
                    - set `offset` to itself + `serial_type_dict["size"]`
                    - move file cursor / pointer to position `offset` in `database_file`
                    - set bytes `body_bytes` to `serial_type_dict["size"]` bytes read from current file cursor position
                    - set key `res["record"]["body"]["rootpage"]` to `body_bytes` converted to an int
                - parse 5th body value `sql`
                    - set int `serial_type` to `res["record"]["header"]["sql"]`
                    - set hashmap `serial_type_dict` to `parse_serial_type(serial_type)`
                    - set `offset` to itself + `serial_type_dict["size"]`
                    - move file cursor / pointer to position `offset` in `database_file`
                    - set bytes `body_bytes` to `serial_type_dict["size"]` bytes read from current file cursor position
                    - set key `res["record"]["body"]["sql"]` to `body_bytes` converted to a string
            - return `res`
    - set int `DATABASE_HEADER_SIZE` to 100
    - set int `LEAF_PAGE_HEADER_SIZE` to 8
    - set int `INTERIOR_PAGE_HEADER_SIZE` to 12
    - set int `PAGE_SIZE` to 4096
    - set string `database_file_path` to `argv[1]`
    - set string `command` to `argv[2]`
    - open file (descriptor) object `database_file` from path `database_file_path` as bytes with read permissions
    - if `command` is `.dbinfo`,
        - set int `cell_count_start_pos` to 100 + 1 + 2 = 103
        - set `cell_count_bytes` to bytes read from `database_file` in index (inclusive) range [`cell_count_start_pos`, `cell_count_start_pos` + 1]
        - set int `cell_count` to `cell_count_bytes` converted to text via UTF-8 encoding, then converted to an int
        - print to terminal the database page size and number of tables `cell_count`
    - else if `command` is `.tables`,
        - set array `table_names` to empty string array
        - set array `cell_offsets` to `parse_schema_cell_pointers(database_file)`
        - for each int `offset` in `cell_offsets`,
            - set hashmap `cell_dict` to `parse_leaf_cell(database_file, offset)`
            - set `table_name` to `cell_dict["record"]["body"]["tbl_name"]`
            - if `table_name` is not string `sqlite_sequence`,
                - append `table_name` to `table_names`
        - print `table_names` as a string that joins each element with a space char ` `
    - close file object at path `database_file`