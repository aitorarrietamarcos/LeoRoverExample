#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from ar_track_alvar_msgs.msg import AlvarMarkers

TARGET_ID = 0

TARGET_DISTANCE = 0.10
DISTANCE_TOLERANCE = 0.08
LATERAL_TOLERANCE = 0.08
LOST_TIMEOUT = 0.5

FORWARD_SPEED = 0.18
TURN_SPEED = 0.70

SEARCH_DURATION = 10.0
SEARCH_TURN_SPEED = 0.35

# Primero comprueba los mensajes. Cambia a False para mover el rover.
DRY_RUN = False

last_seen = None
last_position = None


def marker_callback(msg):
    global last_seen, last_position

    for marker in msg.markers:
        if marker.id == TARGET_ID:
            p = marker.pose.pose.position
            last_position = (p.x, p.y, p.z)
            last_seen = rospy.Time.now()
            return


def calculate_follow_command(x, y):
    cmd = Twist()

    if y > LATERAL_TOLERANCE:
        cmd.angular.z = TURN_SPEED
        action = "TURN LEFT"

    elif y < -LATERAL_TOLERANCE:
        cmd.angular.z = -TURN_SPEED
        action = "TURN RIGHT"

    elif x > TARGET_DISTANCE + DISTANCE_TOLERANCE:
        cmd.linear.x = FORWARD_SPEED
        action = "FORWARD"

    else:
        action = "STOP: target distance reached"

    return cmd, action


def main():
    rospy.init_node("marker_follower_search")

    cmd_publisher = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
    rospy.Subscriber("/ar_pose_marker", AlvarMarkers, marker_callback)

    rate = rospy.Rate(10)
    rospy.loginfo("Follower with search started. DRY_RUN=%s", DRY_RUN)

    try:
        while not rospy.is_shutdown():
            now = rospy.Time.now()
            cmd = Twist()

            if last_seen is None:
                action = "WAITING FOR FIRST TAG -> STOP"

            else:
                time_since_seen = (now - last_seen).to_sec()

                if time_since_seen <= LOST_TIMEOUT:
                    x, y, z = last_position
                    cmd, action = calculate_follow_command(x, y)

                    rospy.loginfo_throttle(
                        0.5,
                        "x=%.2f y=%.2f z=%.2f -> %s",
                        x,
                        y,
                        z,
                        action
                    )

                elif time_since_seen <= LOST_TIMEOUT + SEARCH_DURATION:
                    cmd.angular.z = SEARCH_TURN_SPEED
                    action = "TAG LOST -> SEARCHING"

                    rospy.loginfo_throttle(
                        0.5,
                        "%s (%.1f s)",
                        action,
                        time_since_seen - LOST_TIMEOUT
                    )

                else:
                    action = "TAG NOT FOUND AFTER 10 s -> STOP"
                    rospy.loginfo_throttle(0.5, action)

            if not DRY_RUN:
                cmd_publisher.publish(cmd)

            rate.sleep()

    finally:
        cmd_publisher.publish(Twist())
        rospy.loginfo("Stopped: zero velocity sent.")


if __name__ == "__main__":
    main()
