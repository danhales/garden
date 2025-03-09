"""
Postgres Module Generator

This script generates a Python module for interfacing with a PostgreSQL database,
providing dynamic query generation and type-safe operations.
"""

import os
import inspect
import datetime
import json
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional

VERSION = (0, 1, 0)

class DatabaseIntrospection:
    @staticmethod
    def get_table_columns(conn, table_name):
        """
        Retrieve column information for a specific table.
        
        Parameters
        ----------
        conn : psycopg2 connection
            Active database connection
        table_name : str
            Name of the table to introspect
        
        Returns
        -------
        List[Dict]: 
            List of column metadata dictionaries
        """
        query = """
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM 
            information_schema.columns
        WHERE 
            table_name = %s
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (table_name,))
            return cursor.fetchall()

    @staticmethod
    def get_table_constraints(conn, table_name):
        """
        Retrieve primary and foreign key constraints for a table.
        
        Parameters
        ----------
        conn : psycopg2 connection
            Active database connection
        table_name : str
            Name of the table to introspect
        
        Returns
        -------
        Dict: 
            Dictionary of constraint metadata
        """
        pk_query = """
        SELECT 
            a.attname as column_name
        FROM 
            pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE 
            i.indrelid = %s::regclass 
            AND i.indisprimary
        """
        
        fk_query = """
        SELECT 
            con.conname as constraint_name,
            a.attname as column_name,
            f_table.relname as foreign_table,
            af.attname as foreign_column
        FROM 
            pg_constraint con
            JOIN pg_class f_table ON f_table.oid = con.confrelid
            JOIN pg_class t_table ON t_table.oid = con.conrelid
            JOIN pg_attribute a ON a.attrelid = t_table.oid AND a.attnum = con.conkey[1]
            JOIN pg_attribute af ON af.attrelid = f_table.oid AND af.attnum = con.confkey[1]
        WHERE 
            t_table.relname = %s
            AND con.contype = 'f'
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Primary key
            cursor.execute(pk_query, (table_name,))
            primary_keys = [row['column_name'] for row in cursor.fetchall()]
            
            # Foreign keys
            cursor.execute(fk_query, (table_name,))
            foreign_keys = cursor.fetchall()
            
        return {
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys
        }

    @staticmethod
    def get_all_tables(conn):
        """
        Retrieve all user tables in the current schema.
        
        Parameters
        ----------
        conn : psycopg2 connection
            Active database connection
        
        Returns
        -------
        List[str]: 
            List of table names
        """
        query = """
        SELECT 
            tablename 
        FROM 
            pg_tables 
        WHERE 
            schemaname = 'public'
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            return [table[0] for table in cursor.fetchall()]

def generate_postgres_module(
    host='localhost', 
    database='postgres', 
    user='postgres', 
    password='', 
    port=5432, 
    output_directory=None
):
    """
    Generate a Python module for interfacing with a Postgres database.
    
    Parameters
    ----------
    host : str, optional
        Database host
    database : str, optional
        Database name
    user : str, optional
        Database username
    password : str, optional
        Database password
    port : int, optional
        Database port
    output_directory : str, optional
        Directory to write the generated module
    
    Returns
    -------
    str:
        Path to the generated module file
    """
    # Establish database connection
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )
    
    # Collect database metadata
    tables = DatabaseIntrospection.get_all_tables(conn)
    
    # Prepare metadata
    metadata = {
        'tables': {},
        'connection_params': {
            'host': host,
            'database': database,
            'user': user,
            'port': port
        }
    }
    
    # Introspect each table
    for table in tables:
        columns = DatabaseIntrospection.get_table_columns(conn, table)
        constraints = DatabaseIntrospection.get_table_constraints(conn, table)
        
        metadata['tables'][table] = {
            'columns': columns,
            'constraints': constraints
        }
    
    # Generate module name
    module_name = f"{database.lower()}db"
    filename = os.path.join(
        output_directory or os.getcwd(), 
        f"{module_name}.py"
    )
    
    # Write the module
    with open(filename, 'w') as f:
        # Module docstring
        f.write(f'''"""
{module_name}.py - Auto-generated PostgreSQL database interface

Generated on: {datetime.datetime.now().isoformat()}
Database: {database}
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional

# Database connection parameters
DB_CONFIG = {line}
    'host': '{host}',
    'database': '{database}',
    'user': '{user}',
    'password': '{"*" * len(password)}',
    'port': {port}
{line}

def get_connection():
    """
    Create a new database connection.
    
    Returns
    -------
    psycopg2.extensions.connection
        Active database connection
    """
    return psycopg2.connect(**DB_CONFIG)

class DatabaseOperations:
    @staticmethod
    def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a raw SQL query.
        
        Parameters
        ----------
        query : str
            SQL query to execute
        params : tuple, optional
            Query parameters
        
        Returns
        -------
        List[Dict]
            Query results
        """
        with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> Dict:
        """
        Insert a record into a table.
        
        Parameters
        ----------
        table : str
            Target table name
        data : Dict
            Dictionary of column names and values
        
        Returns
        -------
        Dict
            Inserted record
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f'%({k})s' for k in data.keys()])
        
        query = f"INSERT INTO {{table}} ({{columns}}) VALUES ({{placeholders}}) RETURNING *"
        
        with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, data)
            conn.commit()
            return cursor.fetchone()
    
    @staticmethod
    def update(table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> List[Dict]:
        """
        Update records in a table.
        
        Parameters
        ----------
        table : str
            Target table name
        data : Dict
            Columns and values to update
        condition : Dict
            Filtering conditions for update
        
        Returns
        -------
        List[Dict]
            Updated records
        """
        set_clause = ', '.join([f"{k} = %({k})s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %({k})s" for k in condition.keys()])
        
        query = f"UPDATE {{table}} SET {{set_clause}} WHERE {{where_clause}} RETURNING *"
        
        update_params = {**data, **condition}
        
        with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, update_params)
            conn.commit()
            return cursor.fetchall()

# Metadata about the database
METADATA = {json.dumps(metadata, indent=4)}
''')
    
    conn.close()
    return filename

def main():
    """
    Command-line interface for module generation
    """
    parser = argparse.ArgumentParser(description='PostgreSQL Module Generator')
    parser.add_argument('-H', '--host', default='localhost', help='Database host')
    parser.add_argument('-d', '--database', default='postgres', help='Database name')
    parser.add_argument('-u', '--user', default='postgres', help='Database username')
    parser.add_argument('-p', '--password', default='', help='Database password')
    parser.add_argument('-P', '--port', type=int, default=5432, help='Database port')
    parser.add_argument('-o', '--output', help='Output directory')
    
    args = parser.parse_args()
    
    output_file = generate_postgres_module(
        host=args.host,
        database=args.database,
        user=args.user,
        password=args.password,
        port=args.port,
        output_directory=args.output
    )
    
    print(f"Generated module: {output_file}")

if __name__ == '__main__':
    main()
""")
