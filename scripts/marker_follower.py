#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from ar_track_alvar_msgs.msg import AlvarMarkers

TARGET_ID = 0
TARGET_DISTANCE = 0.10
DISTANCE_TOLERANCE = 0.08
LATERAL_TOLERANCE = 0.08
LOST_TIMEOUT = 0.5

FORWARD_SPEED = 0.2
TURN_SPEED = 0.70

DRY_RUN = False

last_seen = None
last_position = None


def callback(msg):
    global last_seen, last_position

    for marker in msg.markers:
        if marker.id == TARGET_ID:
            p = marker.pose.pose.position
            last_position = (p.x, p.y, p.z)
            last_seen = rospy.Time.now()
            return


def calculate_command(x, y):
    cmd = Twist()

    if y > LATERAL_TOLERANCE:
        cmd.angular.z = TURN_SPEED
        action = "GIRAR IZQUIERDA"

    elif y < -LATERAL_TOLERANCE:
        cmd.angular.z = -TURN_SPEED
        action = "GIRAR DERECHA"

    elif x > TARGET_DISTANCE + DISTANCE_TOLERANCE:
        cmd.linear.x = FORWARD_SPEED
        action = "AVANZAR"

    else:
        action = "PARAR"

    return cmd, action


def main():
    global last_seen, last_position

    rospy.init_node("marker_follower")
    publisher = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
    rospy.Subscriber("/ar_pose_marker", AlvarMarkers, callback)

    rate = rospy.Rate(10)
    rospy.loginfo("Seguidor iniciado. DRY_RUN=%s", DRY_RUN)

    try:
        while not rospy.is_shutdown():
            cmd = Twist()
            action = "TAG LOST -> PARAR"

            now = rospy.Time.now()

            if last_seen is not None and (now - last_seen).to_sec() <= LOST_TIMEOUT:
                x, y, z = last_position
                cmd, action = calculate_command(x, y)

                rospy.loginfo_throttle(
                    0.5,
                    "x=%.2f, y=%.2f, z=%.2f -> %s",
                    x, y, z, action
                )
            else:
                rospy.loginfo_throttle(0.5, action)

            if not DRY_RUN:
                publisher.publish(cmd)

            rate.sleep()

    finally:
        publisher.publish(Twist())
        rospy.loginfo("Seguidor detenido: velocidad cero publicada.")


if __name__ == "__main__":
    main()
