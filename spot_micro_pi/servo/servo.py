import time
from types import TracebackType
from typing import Optional, Type

from busio import I2C
from pwmio import PWMOut

from spot_micro_pi.servo.i2c_device import I2CDevice
from spot_micro_pi.servo.i2c_struct import StructArray, UnaryStruct


class _BaseServo:
    def __init__(
        self,
        pwm_out: PWMOut,
        *,
        min_pulse: int = 750,
        max_pulse: int = 2250,
    ) -> None:
        self._pwm_out = pwm_out
        self.set_pulse_width_range(min_pulse, max_pulse)

    def set_pulse_width_range(
        self,
        min_pulse: int = 750,
        max_pulse: int = 2250,
    ) -> None:
        self._min_duty = int((min_pulse * self._pwm_out.frequency) / 1000000 * 0xFFFF)
        max_duty = (max_pulse * self._pwm_out.frequency) / 1000000 * 0xFFFF
        self._duty_range = int(max_duty - self._min_duty)

    @property
    def fraction(self) -> Optional[float]:
        if self._pwm_out.duty_cycle == 0:
            return None
        return (self._pwm_out.duty_cycle - self._min_duty) / self._duty_range

    @fraction.setter
    def fraction(self, value: Optional[float]) -> None:
        if value is None:
            self._pwm_out.duty_cycle = 0
            return
        if not 0.0 <= value <= 1.0:
            raise ValueError("Must be 0.0 to 1.0")
        duty_cycle = self._min_duty + int(value * self._duty_range)
        self._pwm_out.duty_cycle = duty_cycle


class Servo(_BaseServo):
    def __init__(
        self,
        pwm_out: "PWMOut",
        *,
        actuation_range: int = 180,
        min_pulse: int = 750,
        max_pulse: int = 2250
    ) -> None:
        super().__init__(pwm_out, min_pulse=min_pulse, max_pulse=max_pulse)
        self.actuation_range = actuation_range
        self._pwm = pwm_out

    @property
    def angle(self) -> Optional[float]:
        if self.fraction is None:
            return None
        return self.actuation_range * self.fraction

    @angle.setter
    def angle(self, new_angle: Optional[int]) -> None:
        if new_angle is None:
            self.fraction = None
            return
        if new_angle < 0 or new_angle > self.actuation_range:
            raise ValueError("Angle out of range")
        self.fraction = new_angle / self.actuation_range


class PWMChannel:
    def __init__(self, pca: "PCA9685", index: int):
        self._pca = pca
        self._index = index

    @property
    def frequency(self) -> float:
        return self._pca.frequency

    @frequency.setter
    def frequency(self, _):
        raise NotImplementedError("frequency cannot be set on individual channels")

    @property
    def duty_cycle(self) -> int:
        pwm = self._pca.pwm_regs[self._index]
        if pwm[0] == 0x1000:
            return 0xFFFF
        return pwm[1] << 4

    @duty_cycle.setter
    def duty_cycle(self, value: int) -> None:
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"Out of range: value {value} not 0 <= value <= 65,535")

        if value == 0xFFFF:
            self._pca.pwm_regs[self._index] = (0x1000, 0)
        else:
            value = (value + 1) >> 4
            self._pca.pwm_regs[self._index] = (0, value)


class PCAChannels:
    def __init__(self, pca: "PCA9685") -> None:
        self._pca = pca
        self._channels = [None] * len(self)

    def __len__(self) -> int:
        return 16

    def __getitem__(self, index: int) -> PWMChannel:
        if not self._channels[index]:
            self._channels[index] = PWMChannel(self._pca, index)
        return self._channels[index]


class PCA9685:
    mode1_reg = UnaryStruct(0x00, "<B")
    mode2_reg = UnaryStruct(0x01, "<B")
    prescale_reg = UnaryStruct(0xFE, "<B")
    pwm_regs = StructArray(0x06, "<HH", 16)

    def __init__(
        self,
        i2c_bus: I2C,
        *,
        address: int = 0x40,
        reference_clock_speed: int = 25000000,
    ) -> None:
        self.i2c_device = I2CDevice(i2c_bus, address)
        self.channels = PCAChannels(self)
        self.reference_clock_speed = reference_clock_speed
        self.reset()

    def reset(self) -> None:
        self.mode1_reg = 0x00

    @property
    def frequency(self) -> float:
        prescale_result = self.prescale_reg
        if prescale_result < 3:
            raise ValueError("The device pre_scale register (0xFE) was not read or returned a value < 3")
        return self.reference_clock_speed / 4096 / prescale_result

    @frequency.setter
    def frequency(self, freq: float) -> None:
        prescale = int(self.reference_clock_speed / 4096.0 / freq + 0.5)
        if prescale < 3:
            raise ValueError("PCA9685 cannot output at the given frequency")
        old_mode = self.mode1_reg
        self.mode1_reg = (old_mode & 0x7F) | 0x10
        self.prescale_reg = prescale
        self.mode1_reg = old_mode
        time.sleep(0.005)
        self.mode1_reg = old_mode | 0xA0

    def __enter__(self) -> "PCA9685":
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[type]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.deinit()

    def deinit(self) -> None:
        self.reset()
