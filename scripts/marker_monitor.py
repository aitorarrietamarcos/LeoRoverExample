#!/usr/bin/env python3

import rospy
from ar_track_alvar_msgs.msg import AlvarMarkers

TARGET_ID = 0
TARGET_DISTANCE = 0.65      # metros
LATERAL_TOLERANCE = 0.12    # metros
LOST_TIMEOUT = 0.5          # segundos

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


def decide_action(x, y):
    if y > LATERAL_TOLERANCE:
        return "GIRAR IZQUIERDA"

    if y < -LATERAL_TOLERANCE:
        return "GIRAR DERECHA"

    if x > TARGET_DISTANCE:
        return "AVANZAR"

    return "PARAR: distancia objetivo"


def main():
    global last_seen, last_position

    rospy.init_node("marker_monitor")
    rospy.Subscriber("/ar_pose_marker", AlvarMarkers, callback)

    rate = rospy.Rate(10)
    last_report_time = rospy.Time(0)

    rospy.loginfo("Monitor iniciado. Buscando tag ID %d.", TARGET_ID)

    while not rospy.is_shutdown():
        now = rospy.Time.now()

        if last_seen is None or (now - last_seen).to_sec() > LOST_TIMEOUT:
            message = "TAG LOST -> PARAR"

        else:
            x, y, z = last_position
            action = decide_action(x, y)

            message = (
                "Tag %d | x=%.2f m | y=%.2f m | z=%.2f m | %s"
                % (TARGET_ID, x, y, z, action)
            )

        # Mostrar como máximo cuatro mensajes por segundo.
        if (now - last_report_time).to_sec() >= 0.25:
            rospy.loginfo(message)
            last_report_time = now

        rate.sleep()


if __name__ == "__main__":
    main()
