import time
from types import TracebackType
from typing import Optional, Type

from busio import I2C
from circuitpython_typing import ReadableBuffer, WriteableBuffer


class I2CDevice:
    def __init__(self, i2c: I2C, device_address: int, probe: bool = True) -> None:

        self.i2c = i2c
        self.device_address = device_address

        if probe:
            self.__probe_for_device()

    def readinto(self, buf: WriteableBuffer, *, start: int = 0, end: Optional[int] = None) -> None:
        if end is None:
            end = len(buf)
        self.i2c.readfrom_into(self.device_address, buf, start=start, end=end)

    def write(self, buf: ReadableBuffer, *, start: int = 0, end: Optional[int] = None) -> None:
        if end is None:
            end = len(buf)
        self.i2c.writeto(self.device_address, buf, start=start, end=end)

    def write_then_readinto(
        self,
        out_buffer: ReadableBuffer,
        in_buffer: WriteableBuffer,
        *,
        out_start: int = 0,
        out_end: Optional[int] = None,
        in_start: int = 0,
        in_end: Optional[int] = None
    ) -> None:
        if out_end is None:
            out_end = len(out_buffer)
        if in_end is None:
            in_end = len(in_buffer)

        self.i2c.writeto_then_readfrom(
            self.device_address,
            out_buffer,
            in_buffer,
            out_start=out_start,
            out_end=out_end,
            in_start=in_start,
            in_end=in_end,
        )

    def __enter__(self) -> "I2CDevice":
        while not self.i2c.try_lock():
            time.sleep(0)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[type]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        self.i2c.unlock()
        return False

    def __probe_for_device(self) -> None:
        while not self.i2c.try_lock():
            time.sleep(0)
        try:
            self.i2c.writeto(self.device_address, b"")
        except OSError:
            try:
                result = bytearray(1)
                self.i2c.readfrom_into(self.device_address, result)
            except OSError:
                raise ValueError("No I2C device at address: 0x%x" % self.device_address)
        finally:
            self.i2c.unlock()
