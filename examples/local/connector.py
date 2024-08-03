# This is a simple example for how to work with the fivetran_connector_sdk module.
# It uses a local SOURCE_DATA object created at the start of the script, and demonstrates the Schema() method use.
# It also shows a way to manage state.
# See the Technical Reference documentation (https://fivetran.com/docs/connectors/connector-sdk/technical-reference#update)
# and the Best Practices documentation (https://fivetran.com/docs/connectors/connector-sdk/best-practices) for details

# Import required classes from fivetran_connector_sdk
from fivetran_connector_sdk import Connector
from fivetran_connector_sdk import Logging as log
from fivetran_connector_sdk import Operations as op

# Define the SOURCE_DATA which simulates the source data that will be upstarted to Fivetran.
SOURCE_DATA = [
    {"id": 10, "message": "Hello world"},
    {"id": 20, "message": "Hello again"},
    {"id": 30, "message": "Good bye"},
]


# Define the schema function which lets you configure the schema your connector delivers.
# See the technical reference documentation for more details on the schema function
# https://fivetran.com/docs/connectors/connector-sdk/technical-reference#schema
# The schema function takes one parameter:
# - configuration: a dictionary that holds the configuration settings for the connector.
def schema(configuration: dict):
    return [
        {
            "table": "hello_world",  # Name of the table in the destination, required.
            "primary_key": ["id"],  # Primary key column(s) for the table, optional.
            "columns": {  # Definition of columns and their types, optional.
                "message": "STRING",  # Contains a dictionary of column names and data types
            },
        }
    ]


# Define the update function, which is a required function, and is called by Fivetran during each sync.
# See the technical reference documentation for more details on the update function
# https://fivetran.com/docs/connectors/connector-sdk/technical-reference#update
# The function takes two parameters:
# - configuration: dictionary contains any secrets or payloads you configure when deploying the connector
# - state: a dictionary contains whatever state you have chosen to checkpoint during the prior sync
# The state dictionary is empty for the first sync or for any full re-sync
def update(configuration: dict, state: dict):
    # Retrieve the cursor from the state to determine the current position in the SOURCE_DATA.
    # If the cursor is not present in the state, start from the beginning (cursor = 0).
    cursor = state['cursor'] if 'cursor' in state else 0
    log.fine(f"current cursor is {repr(cursor)}")

    # Get the row of data from SOURCE_DATA using the cursor position.
    row = SOURCE_DATA[cursor]

    # Yield an upsert operation to insert/update the row in the "hello_world" table.
    yield op.upsert(table="hello_world", data=row)

    # Update the state with the new cursor position, incremented by 1.
    new_state = {
        "cursor": cursor + 1
    }
    log.fine(f"state updated, new state: {repr(new_state)}")

    # Yield a checkpoint operation to save the new state.
    yield op.checkpoint(state=new_state)


# This creates the connector object that will use the update and schema functions defined in this connector.py file.
connector = Connector(update=update, schema=schema)

# Check if the script is being run as the main module.
# This is Python's standard entry method allowing your script to be run directly from the command line or IDE 'run' button.
# This is useful for debugging while you write your code. Note this method is not called by Fivetran when executing your connector in production.
# Please test using the Fivetran debug command prior to finalizing and deploying your connector.
if __name__ == "__main__":
    # Adding this code to your `connector.py` allows you to test your connector by running your file directly from your IDE:
    result = connector.debug()
    if result:
        print("Success! You can publish your code now if you like: "
              "`DEPLOY_KEY=XXXX python -m fivetran_custom_sdk main.py --deploy`")
