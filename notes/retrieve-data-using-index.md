# Your Task

In this stage, we'll implement an index scan. Rather than reading *all* rows in a table and then filtering in-memory, we'll use an index to perform a more intelligent search.

To test whether your implementation actually uses an index, the tester will use a database is ~1GB in size and expect your program to return query results in less than 3 seconds.

The test database contains a `companies` table with an index named `idx_companies_country` on the `country` column.

You can download a small version of this database to test locally, read the `Sample Databases` section in the `README` of your repository for details.

Here's how the tester will execute your program:
```
$ ./your_program.sh companies.db "SELECT id, name FROM companies WHERE country = 'eritrea'"
```

and here's the output it expects:
```
121311|unilink s.c.
2102438|orange asmara it solutions
5729848|zara mining share company
6634629|asmara rental
```

You can assume that all queries run by the tester will include `country` in the `WHERE` clause, so they can be served by the index. The tester will run multiple randomized queries and expect all of them to return results in under 3 seconds.

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/nz8/code-examples).

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
        - what are b-trees and how to traverse them?
            - b-tree = like binary search tree, but:
                - each node can hold a variable-length amount of keys / values
                - each node can be linked to 2+ child nodes
                - formulas that defines the lower and upper bounds of how many keys and child nodes an internal (i.e., non-leaf) node can have:
                    - doesn't apply to root node
                    - `B` = Branching factor / bound
                    - `x` = # of children per node
                    - `y` = # of keys per node
                    - `B` <= `x` < 2 * `B`
                    - `B` - 1 <= `y` < (2 * `B`) - 1
                - all leaf nodes must be at same depth / height (in B-tree)
                - leaf nodes have 0 children (i.e., child nodes)
            - how to traverse / find a leaf node with some specific data?
                - set current node to root node
                - for each key `key` in current node,
                    - if `key` == `target_value`,
                        - return current node
                    - if `key` is 1st key and `target_value` < `key`,
                        - go to current node's leftmost child node & recurse
                    - if `key` is last key and `key` > `target_value`,
                        - go to current node's rightmost child node & recurse
                    - if `key` < `target_value` < next key following `key`,
                        - go to current node's child between `key` and next key following `key` & recurse
                - `target_value` is not in B-tree -> return null
            - inorder traversal of a BST (Binary Search Tree) pseudocode:
                ```
                Inorder-Tree-Walk(x)
                    if x != NIL then
                        Inorder-Tree-Walk(x.left)
                        visit node
                        Inorder-Tree-Walk(x.right)
                ```
                - walk meaning?
                    - go to node?
                - visit node meaning?
                    - add node's value to array
            - how to traverse all nodes in a b-tree in inorder traversal so that nodes are visited in non-decreasing / ascending order?
                - inorder traversal
        - how are b-trees done in SQLite?
            - SQLite uses B+ trees: 2 b-tree types
                - "table b-trees"
                    - 64-bit signed int key(s)
                    - store data in leaf nodes only
                    - leaf nodes (pages)
                        - composition = 
                            - keys +
                            - data
                    - interior nodes (pages)
                        - composition =
                            - `K` keys +
                            - (`K` + 1) pointers to child nodes (pages)
                        - pointers = 32-bit unsigned int page number of child
                        - `K` >= 2, except when page 1 (root node) is an interior node
                    - `id` primary keys with `autoincrement` property point to cell's `rowid`
                - "index b-trees"
                    - arbitrary-lengthed (int?) keys
                    - store 0 data
                - b-tree page is interior or leaf page
            - values are only stored in bottom-most leaf nodes, not intermediary nodes
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
    - ex.6: run `SELECT <column 1>, ...<column N> FROM <table> WHERE <column> = <value>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db "SELECT name, color FROM apples WHERE color = 'Yellow'"
            ```
        - terminal output:
            ```
            Golden Delicious|Yellow
            ```
    - ex.7: run `SELECT <column 1>, ...<column N> FROM <table> WHERE <column> = <value>` command
        - run in terminal:
            ```
            ./your_program.sh superheroes.db "SELECT id, name FROM superheroes WHERE eye_color = 'Pink Eyes'"
            ```
        - terminal output:
            ```
            297|Stealth (New Earth)
            790|Tobias Whale (New Earth)
            1085|Felicity (New Earth)
            2729|Thrust (New Earth)
            3289|Angora Lapin (New Earth)
            3913|Matris Ater Clementia (New Earth)
            ```
    - ex.8: run `SELECT <column 1>, ...<column N> FROM <table> WHERE <column> = <value>` command
        - run in terminal:
            ```
            ./your_program.sh companies.db "SELECT id, name FROM companies WHERE country = 'eritrea'"
            ```
        - terminal output:
            ```
            121311|unilink s.c.
            2102438|orange asmara it solutions
            5729848|zara mining share company
            6634629|asmara rental
            ```
- PEDAC: Data Structures And Algorithms
    - helper functions
        - TODO
    - set string `database_file_path` to `argv[1]`
    - set string `command` to `argv[2]`
    - open file (descriptor) object `database_file` from path `database_file_path` as bytes with read permissions
    - if `command` follows the regex `SELECT <col 1>, ...<col N> FROM <table> WHERE <col> = '<value>'`,
        - set hashmap `sql_dict` to `parse_sql_select_multi_column(command)`
        - set string `table` to `sql_dict["table"]`
        - set string `sql_create` to `sql_of(database_file, table)`
        - set int array `column_indices` empty
        - for int index `i` from 0 to `sql_dict["columns"]` exclusive,
            - push `column_index_of(sql_create, sql_dict["columns"][i])` to `column_indices`
        - set int `where_column_index` to `column_index_of(sql_create, sql_dict["where_column"])`
        - set string `where_value` to `sql_dict["where_value"]`
        - set string `rootpage` to `rootpage_of(database_file, table)`
        - set string array `rows` empty
        - set int array `cell_offsets` to `parse_cell_pointers(database_file, offset)`
        - for int `offset` in `cell_offsets`,
            - set hashmap `cell_dict` to `parse_leaf_cell(database_file, offset, rootpage)`
            - if `cell_dict["record"]["body"][where_column_index]` is not `where_value`,
                - skip to next iteration
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