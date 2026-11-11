# Your Task

This stage is similar to the previous one, just that the tester will query for multiple columns instead of just one.

Here's how the tester will execute your program:
```
$ ./your_program.sh sample.db "SELECT name, color FROM apples"
```

and here's the output it expects:
```
Granny Smith|Light Green
Fuji|Red
Honeycrisp|Blush Red
Golden Delicious|Yellow
```

Just like in the previous stage, the order of rows doesn't matter.

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/vc9/code-examples).

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
            - `argv[2]`: SQLite command to run e.g., `SELECT name FROM apples`
    - output:
        - none
    - side effects:
        - TODO
    - questions
        - in a (leaf) cell's record, what says how many columns or serial type codes the record has?
            - record header size
                - use int counter to track remaining bytes left in header as varint header serial type (bytes) are processed
                - column count = int counter value + 1
        - how to get column index of a named column in a table?
            - get `sqlite_schema.sql` string value of the table
            - get string array by splitting string value by comma `,` char
            - iterate thru string array
                - count `,` char occurrences in current iterated string
                - if column name found as substring in current iterated string,
                    - column index = count of `,` comma occurrences
        - how to get the column names from a SQL select statement string?
            - via `sqlparse` third-party module / library
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
    - ex.3: run `SELECT COUNT(*) FROM <table>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db "SELECT COUNT(*) FROM apples"
            ```
        - terminal output:
            ```
            4
            ```
    - ex.4: run `SELECT <column> FROM <table>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db "SELECT name FROM apples"
            ```
        - terminal output:
            ```
            Granny Smith
            Fuji
            Honeycrisp
            Golden Delicious
            ```
    - ex.5: run `SELECT <column 1>, ...<column N> FROM <table>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db "SELECT name, color FROM apples"
            ```
        - terminal output:
            ```
            Granny Smith|Light Green
            Fuji|Red
            Honeycrisp|Blush Red
            Golden Delicious|Yellow
            ```
- PEDAC: Data Structures And Algorithms
    - helper functions
        - `parse_sql_select_multi_column(statement: string) -> dict`
            - TODO
    - set string `database_file_path` to `argv[1]`
    - set string `command` to `argv[2]`
    - open file (descriptor) object `database_file` from path `database_file_path` as bytes with read permissions
    - if `command` follows the regex `SELECT <col 1>, ...<col N> FROM <table>`,
        - set hashmap `sql_dict` to `parse_sql_select_multi_column(command)`
        - set string `table` to `sql_dict["table"]`
        - set string `sql_create` to `sql_of(database_file, table)`
        - set int array `column_indices` empty
        - for int index `i` from 0 to `sql_dict["columns"]` exclusive,
            - push `column_index_of(sql_create, sql_dict["columns"][i])` to `column_indices`
        - set string `rootpage` to `rootpage_of(database_file, table)`
        - set string array `rows` empty
        - set int array `cell_offsets` to `parse_cell_pointers(database_file, offset)`
        - for int `offset` in `cell_offsets`,
            - set hashmap `cell_dict` to `parse_leaf_cell(database_file, offset, rootpage)`
            - set string `row` empty
            - for int index `i` from 0 to length of `column_indices` exclusive,
                - if `row` is empty string,
                    - append `row` with `cell_dict["record"]["body"][column_index]`
                - else,
                    - append `row` with `|` + `cell_dict["record"]["body"][column_index]`
            - push `row` to `rows`
        - set string `rows_str` to joining each string in `rows` with a newline char `\n`
        - print `rows_str`
    - close file object at path `database_file`