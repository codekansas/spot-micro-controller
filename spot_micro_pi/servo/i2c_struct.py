import struct
from typing import Any, Optional, Tuple, Type

from circuitpython_typing.device_drivers import I2CDeviceDriver


class _BoundStructArray:
    def __init__(
        self,
        obj: I2CDeviceDriver,
        register_address: int,
        struct_format: str,
        count: int,
    ) -> None:
        self.format = struct_format
        self.first_register = register_address
        self.obj = obj
        self.count = count

    def _get_buffer(self, index: int) -> bytearray:
        if not 0 <= index < self.count:
            raise IndexError()
        size = struct.calcsize(self.format)
        buf = bytearray(size + 1)
        buf[0] = self.first_register + size * index
        return buf

    def __getitem__(self, index: int) -> Tuple:
        buf = self._get_buffer(index)
        with self.obj.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return struct.unpack_from(self.format, buf, 1)

    def __setitem__(self, index: int, value: Tuple) -> None:
        buf = self._get_buffer(index)
        struct.pack_into(self.format, buf, 1, *value)
        with self.obj.i2c_device as i2c:
            i2c.write(buf)

    def __len__(self) -> int:
        return self.count


class StructArray:
    def __init__(self, register_address: int, struct_format: str, count: int) -> None:
        self.format = struct_format
        self.address = register_address
        self.count = count
        self.array_id = "_structarray{}".format(register_address)

    def __get__(
        self,
        obj: Optional[I2CDeviceDriver],
        objtype: Optional[Type[I2CDeviceDriver]] = None,
    ) -> _BoundStructArray:
        if not hasattr(obj, self.array_id):
            setattr(
                obj,
                self.array_id,
                _BoundStructArray(obj, self.address, self.format, self.count),
            )
        return getattr(obj, self.array_id)


class Struct:
    def __init__(self, register_address: int, struct_format: str) -> None:
        self.format = struct_format
        self.buffer = bytearray(1 + struct.calcsize(self.format))
        self.buffer[0] = register_address

    def __get__(
        self,
        obj: Optional[I2CDeviceDriver],
        objtype: Optional[Type[I2CDeviceDriver]] = None,
    ) -> Tuple:
        with obj.i2c_device as i2c:
            i2c.write_then_readinto(self.buffer, self.buffer, out_end=1, in_start=1)
        return struct.unpack_from(self.format, memoryview(self.buffer)[1:])

    def __set__(self, obj: I2CDeviceDriver, value: Tuple) -> None:
        struct.pack_into(self.format, self.buffer, 1, *value)
        with obj.i2c_device as i2c:
            i2c.write(self.buffer)


class UnaryStruct:
    def __init__(self, register_address: int, struct_format: str) -> None:
        self.format = struct_format
        self.address = register_address

    def __get__(
        self,
        obj: Optional[I2CDeviceDriver],
        objtype: Optional[Type[I2CDeviceDriver]] = None,
    ) -> Any:
        buf = bytearray(1 + struct.calcsize(self.format))
        buf[0] = self.address
        with obj.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return struct.unpack_from(self.format, buf, 1)[0]

    def __set__(self, obj: I2CDeviceDriver, value: Any) -> None:
        buf = bytearray(1 + struct.calcsize(self.format))
        buf[0] = self.address
        struct.pack_into(self.format, buf, 1, value)
        with obj.i2c_device as i2c:
            i2c.write(buf)
