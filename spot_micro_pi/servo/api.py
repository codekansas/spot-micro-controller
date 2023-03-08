import logging
from typing import List, Optional

import busio
from board import SCL, SDA

from spot_micro_pi.servo.servo import PCA9685, Servo

logger = logging.getLogger(__name__)


class ServoSet:
    def __init__(
        self,
        *,
        num_servos: Optional[int] = None,
        servo_ids: Optional[List[int]] = None,
    ) -> None:
        logger.info("Initializing connection to PCA9685")

        # Gets the servo IDs.
        if num_servos is None and servo_ids is None:
            raise ValueError("Must specify either num_servos or servo_ids")
        if servo_ids is None:
            servo_ids = list(range(num_servos))
        else:
            assert num_servos is None or num_servos == len(servo_ids)

        self._i2c = busio.I2C(SCL, SDA)
        self._pca = PCA9685(self._i2c)
        self._pca.frequency = 50

        self._servo_ids = servo_ids
        self._servos: List[Servo] = []
        for servo_id in servo_ids:
            self._servos.append(Servo(self._pca.channels[servo_id]))

    @property
    def pca(self) -> PCA9685:
        return self._pca

    @property
    def servo_ids(self) -> List[int]:
        return self._servo_ids

    def set_angle(self, servo_id: int, angle: float) -> None:
        self._servos[servo_id].angle = angle
