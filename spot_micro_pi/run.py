import argparse
import time

from spot_micro_pi.servo.api import ServoSet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("servo_id", type=int, help="The servo ID to control")
    parser.add_argument("angle", type=float, help="The angle to move the servo to")
    parser.add_argument("-w", "--wait", type=float, default=1.0, help="How long to wait after running")
    args = parser.parse_args()

    servo_set = ServoSet(servo_ids=[args.servo_id])
    for _ in range(10):
        servo_set.set_angle(args.servo_id, args.angle)
        time.sleep(args.wait / 10)


if __name__ == "__main__":
    main()
