#!/usr/bin/env python3
"""
logic.py
Logic functions which allow the robot to perform tasks autonomously

Mechatronics 2
~ Callum Morrison, 2020
"""

import json
import time

import redis

from mars import coords, logs, settings
from mars.comms import commands

log = logs.create_log(__name__)

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def update_ui():
    """
    Passes general information to the UI.
    """
    from mars.webapp import ws_send

    doors_state = json.loads(r.get("doors_state"))

    # Send current data to the UI
    ws_send("update_logic", json.dumps(
        {
            "engineer": {
                "current_task": int(r.get("engineer_current_task")),
                "current_marker": int(r.get("engineer_current_marker"))
            },
            "alien": {
                "current_marker": int(r.get("alien_current_marker"))
            },
            "doors": {
                "A": doors_state[0],
                "B": doors_state[1],
                "C": doors_state[2],
                "D": doors_state[3]}
        }
    ))


class engineer:
    def __init__(self):
        # General route the Engineer wishes to take:
        # - Start at launch pad
        # - Complete tasks in order: 1, 2, 3
        # - Return to launch pad
        self.desired_path = [2, 17, 9, 12, 2]

    def setup(self):
        """
        Setup database keys and initial values.
        """
        # Index of the task which needs to be completed
        r.set("engineer_current_task", 0)

        # Last known position in the compound
        r.set("engineer_current_marker", 2)

        r.set("engineer_tasks_enabled", 0)

    def engineer_complete_tasks(self):
        """
        Function to go through all tasks and complete them in sequence.
        """
        # Toggle to cancel tasks
        r.set("engineer_tasks_enabled", 0)
        time.sleep(2 / settings.FRAMERATE)
        r.set("engineer_tasks_enabled", 1)

        while int(r.get("engineer_tasks_enabled")):
            self.next_task()

    def next_task(self):
        """
        Aims to complete the next task in the task list for the Engineer.
        """

        update_ui()

        # Determine route to get to next task
        r.set("engineer_current_marker",
              self.desired_path[int(r.get("engineer_current_task"))])

        target_marker = self.desired_path[int(
            r.get("engineer_current_task")) + 1]

        target_route = coords.route().pathfinder(
            int(r.get("engineer_current_marker")), target_marker)

        log.info(f"Engineer working on next task: {target_route}")

        reached_target = False

        while not reached_target:

            reached_marker = False

            while not reached_marker:
                # Break from loops if required
                if not int(r.get("engineer_tasks_enabled")):
                    return

                # Save start time to synchronise framerate
                start_time = time.time()

                try:
                    # Calculate distance to next marker in route
                    magnitude, direction = coords.coords().calculate_vector(
                        "engineer", target_route[0])

                except TypeError:
                    log.error("Invalid target route supplied")
                    return

                # If within target radius of target marker
                if magnitude < settings.MARKER_RADIUS:
                    log.info("Engineer within target marker radius!")
                    log.info("Moving to next marker...")

                    # Update current position
                    r.set("engineer_current_marker", target_route[0])

                    # Remove from route
                    target_route.pop(0)
                    reached_marker = True

                else:
                    # Calculate distance to alien
                    alien_distance, _ = coords.coords().calculate_vector(
                        "engineer", "alien")

                    # If within hearing distance, re-calculate route with alien avoidance
                    if alien_distance < settings.DETECTION_RADIUS:
                        log.debug("Engineer within hearing distance of alien!")
                        new_target_route = coords.route().pathfinder(
                            int(r.get("engineer_current_marker")), target_marker, avoid=alien.current_marker)

                        # Check if no route has been found, if so throw a fit
                        if not new_target_route:
                            log.error(
                                f"The engineer can't find any route to it's target: {target_marker}!")
                            continue

                        # Check if new route is in the same direction, or a new direction
                        if target_route[1] == new_target_route[1]:
                            # Continue in same direction; remove the first element to prevent backgracking
                            new_target_route.pop(0)

                        target_route = new_target_route

                    else:
                        # Send a command to go to the first marker in the route
                        # commands.move("engineer", magnitude, direction)
                        pass

                # Wait until the next frame is required
                end_time = time.time()
                time_remain = start_time + 1 / settings.FRAMERATE - end_time

                if time_remain > 0:
                    time.sleep(time_remain)

                update_ui()

            if not target_route:
                # Route is complete
                reached_target = True

        # Move to next task
        r.incr("engineer_current_task")


class alien:
    """
    Used for functions and states specific to the Alien.
    """

    def setup(self):
        """
        Setup database keys and initial values.
        """
        # Last known position in the compound
        r.set("alien_enabled", 0)
        r.set("alien_current_marker", 9)

    def alien_follow(self):
        """
        Start the Alien following the Engineer.
        """
        # Toggle to cancel existing tasks
        r.set("alien_enabled", 0)
        time.sleep(2 / settings.FRAMERATE)
        r.set("alien_enabled", 1)

        while int(r.get("alien_enabled")):
            # Determine route to get to next task
            target_marker = int(r.get("engineer_current_marker"))

            target_route = coords.route().pathfinder(
                int(r.get("alien_current_marker")), target_marker, shortcuts=True)

            log.info(f"Alien following route: {target_route}")

            reached_marker = False

            while not reached_marker:
                # Break from loops if required
                if not int(r.get("alien_enabled")):
                    return

                # Save start time to synchronise framerate
                start_time = time.time()

                try:
                    # Calculate distance to next marker in route
                    magnitude, direction = coords.coords().calculate_vector(
                        "alien", target_route[0])

                except TypeError:
                    log.error("Invalid target route supplied")
                    return

                # If within target radius of target marker
                if magnitude < settings.MARKER_RADIUS:
                    log.info("Alien within target marker radius!")
                    log.info("Moving to next marker...")

                    # Update current position
                    r.set("alien_current_marker", target_route[0])

                    # Remove from route
                    target_route.pop(0)
                    reached_marker = True

                else:
                    # Send a command to go to the first marker in the route
                    # commands.move("engineer", magnitude, direction)
                    pass

                # Wait until the next frame is required
                end_time = time.time()
                time_remain = start_time + 1 / settings.FRAMERATE - end_time

                if time_remain > 0:
                    time.sleep(time_remain)

                update_ui()
