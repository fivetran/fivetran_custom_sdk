# This is a simple example for how to work with the fivetran_connector_sdk module.


# See the Technical Reference documentation (https://fivetran.com/docs/connectors/connector-sdk/technical-reference#update)
# and the Best Practices documentation (https://fivetran.com/docs/connectors/connector-sdk/best-practices) for details.

from datetime import datetime  # Import datetime for handling date and time conversions.

import duckdb  # import duckdb to interact with DuckDB databases from within your Python code.
import json  # Import the json module to handle JSON data.

# Import required classes from fivetran_connector_sdk
from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Logging as log
from fivetran_connector_sdk import Operations as op


# Define the schema function which lets you configure the schema your connector delivers.
# See the technical reference documentation for more details on the schema function:
# https://fivetran.com/docs/connectors/connector-sdk/technical-reference#schema
# The schema function takes one parameter:
# - configuration: a dictionary that holds the configuration settings for the connector.

timestamp_format = "%Y-%m-%dT%H:%M:%SZ"
def schema(configuration: dict):
    return [
        {
            "table": "customers",  # Name of the table in the destination.
            "primary_key": ["customer_id"],  # Primary key column(s) for the table.
            "columns": {  # Define the columns and their data types.
                "customer_id": "INT",  # Integer column for the customer_id.
                "first_name": "STRING",  # String column for the first name.
                "last_name": "STRING",  # String column for the last name.
                "email": "STRING",  # String column for the email.
                "updated_at": "UTC_DATETIME",  # UTC date-time column for the updated_at.
            },
        }
    ]


def dt2str(incoming: datetime) -> str:
    return incoming.strftime(timestamp_format)

# Define the update function, which is a required function, and is called by Fivetran during each sync.
# See the technical reference documentation for more details on the update function
# https://fivetran.com/docs/connectors/connector-sdk/technical-reference#update
# The function takes two parameters:
# - configuration: dictionary contains any secrets or payloads you configure when deploying the connector
# - state: a dictionary contains whatever state you have chosen to checkpoint during the prior sync
# The state dictionary is empty for the first sync or for any full re-sync
def update(configuration: dict, state: dict):
    last_synced = state["last_synced"] if "last_synced" in state else '2024-01-01T00:00:00Z'
    conn = duckdb.connect("source_warehouse.db", read_only=True)
    time_based_column = "updated_at"
    log.fine(f"fetching records from `customer` table modified after {last_synced}")

    query = (f"SELECT customer_id, first_name, last_name, email, updated_at FROM customers WHERE {time_based_column} > "
             f"'{last_synced}' ORDER BY {time_based_column}")  # Replace with your actual table name
    result = conn.execute(query).fetchall()

    for row in result:
        yield op.upsert(table="customers",
                        data={
                            "customer_id": row[0],  # Customer id.
                            "first_name": row[1],  # First Name.
                            "last_name": row[2],  # Last name.
                            "email": row[3],  # Email id.
                            "updated_at": dt2str(row[4])  # record updated at.
                        })
        last_synced = dt2str(row[4])
    state["last_synced"] = last_synced
    yield op.checkpoint(state)


# This creates the connector object that will use the update and schema functions defined in this connector.py file.
connector = Connector(update=update, schema=schema)

# Check if the script is being run as the main module.
# This is Python's standard entry method allowing your script to be run directly from the command line or IDE 'run' button.
# This is useful for debugging while you write your code. Note this method is not called by Fivetran when executing your connector in production.
# Please test using the Fivetran debug command prior to finalizing and deploying your connector.
if __name__ == "__main__":
    # Open the state.json file and load its contents into a dictionary.
    with open("state.json", 'r') as f:
        state = json.load(f)
    # Adding this code to your `connector.py` allows you to test your connector by running your file directly from your IDE:
    connector.debug(state=state)

# Source table:
# ┌───────────────────┬───────────────────┬───────────────────────────────────────────┬────────────────────────────┐
# │     customer_id   │   first_name      │     last_name     │       email           │       updated_at           │
# │         int16     │      varchar      │     varchar       │       varchar         │   timestamp with time zone │
# ├───────────────────┼───────────────────┼───────────────────┼───────────────────────┤────────────────────────────│
# │         1         │       Mathew      │     Perry         │ mathew@fivetran.com   │    2023-12-31 23:59:59.000 │
# │         2         │       Joe         │     Doe           │ joe@fivetran.com      │    2024-01-31 23:04:39.000 │
# │         3         │       Jake        │     Anderson      │ jake@fivetran.com     │    2023-11-01 23:59:59.000 │
# │         4         │       John        │     William       │ john@fivetran.com     │    2024-02-14 22:59:59.000 │
# │         5         │       Ricky       │     Roma          │ ricky@fivetran.com    │    2024-03-16 16:40:29.000 │
# ├───────────────────┴───────────────────┴───────────────────┴────────────────────────────────────────────────────┤
# │ 5 rows                                                                                               5 columns │
# └────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘


# Resulting table:
# ┌─────────────────────┬───────────────────┬────────────────────────────────────────┬────────────────────────────┐
# │     customer_id     │   first_name      │     last_name     │       email        │       updated_at           │
# │         int16       │      varchar      │     varchar       │       varchar      │   timestamp with time zone │
# ├─────────────────────┼───────────────────┼───────────────────┼────────────────────┤────────────────────────────│
# │         2           │       Joe         │     Doe           │ joe@fivetran.com   │    2024-01-31T23:04:39Z    │
# │         4           │       John        │     William       │ john@fivetran.com  │    2024-02-14T22:59:59Z    │
# │         5           │       Ricky       │     Roma          │ ricky@fivetran.com │    2024-03-16T16:40:29Z    │
# ├─────────────────────┴───────────────────┴───────────────────┴─────────────────────────────────────────────────┤
# │ 3 rows                                                                                              5 columns │
# └───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘