#-------------------------------------------------------------------------------------------------------#
# Copyright (c) 2023 by <Company/Name>                                                                  #
#                                                                                                       #
# Licensed under the MIT License                                                                        #
#                                                                                                       #
#-------------------------------------------------------------------------------------------------------#

"""

scheduler.py
Description:
Schedules and manages periodic tasks. Typically used to run tasks at regular intervals, such as sending reminders or processing data.

Content Overview:
Task Scheduling: Defines and schedules tasks.
Task Execution: Runs tasks based on the schedule and handles task execution.

"""


import schedule
import threading
import time
import app.db_update as db_update

# Call to the python script which will update the database from blob
def run_blob_update():
    """
    Executes the `blob_update` script to synchronize the database with the latest data from blob storage.

    This function serves as a wrapper that calls the main function of the `blob_update` module.
    It is typically scheduled to run periodically to keep the database updated with new data from
    the blob storage.
    """
    db_update.main()

# Five minutes based scheduler for blob_update.py run
def schedule_blob_update():
    """
    Schedules the `run_blob_update` function to execute every 5 minutes.

    This function uses the `schedule` library to set up a recurring task that calls `run_blob_update`.
    It enters an infinite loop where it continuously checks for pending scheduled tasks and executes them.
    The sleep interval is set to 1 second to reduce CPU usage.

    This scheduling mechanism ensures that the database is regularly updated with data from blob storage.

    Note:
    - Ensure that the `schedule` and `time` libraries are imported.
    - This function is intended to be run in a separate thread to avoid blocking the main program.
    """
    schedule.every(2).minutes.do(run_blob_update)
    print("It is updating the blob")
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    update_thread = threading.Thread(target=schedule_blob_update)
    update_thread.daemon = True
    update_thread.start()


if __name__ == "__main__":
    # Start the scheduler in a separate daemon thread to allow it to run in the background.
    update_thread = threading.Thread(target=schedule_blob_update)
    update_thread.daemon = False
    update_thread.start()
