from typing import Final, Union

import numpy as np
import rtlsdr
from numpy.typing import NDArray

Gain = Union[float, str]


def parse_gain(gain_str: str) -> Gain:
    """
    Parse a string containing a gain value, e.g. "3.14" or "auto".
    """
    if gain_str == "auto":
        return gain_str
    try:
        return float(gain_str)
    except TypeError as err:
        raise TypeError(f"Invalid gain string: {gain_str!r}") from err


class MockRtlSdr:
    """
    Mock version of an rtlsdr.RtlSdr device. This is used when no SDR device
    is connected so that we can still run and test the code. It has the same
    interface as `rtlsdr.RtlSdr`, except that its `read_samples()` method
    generates complex-valued Gaussian noise.
    """

    MAX_READ_SAMPLES: Final[int] = 2**24

    def __init__(self) -> None:
        # Define all members of RtlSdr that are exposed to the user
        self.sample_rate = 2.048e6  # Hz
        self.center_freq = 1420.4e6  # Hz
        self.gain = 1.0

    def close(self) -> None:
        pass

    def read_samples(self, num_samples: Union[int, float]) -> NDArray[np.complex128]:
        n = int(num_samples)
        if not n > 0:
            raise ValueError(f"Number of samples to read must be > 0")

        if n > self.MAX_READ_SAMPLES:
            raise rtlsdr.rtlsdr.LibUSBError(
                "<LIBUSB_ERROR_NO_MEM (-11): Insufficient memory> "
                f"Could not read {n} bytes"
            )

        # NOTE: scale is empirically adjusted so that the procedure of finding
        # the optimum gain takes a few trials
        scale = 0.01 * self.get_gain()
        real = np.random.normal(size=n, scale=scale)
        imag = np.random.normal(size=n, scale=scale)
        return real + 1.0j * imag

    def get_gain(self) -> float:
        if self.gain == "auto":
            return 1.0
        return self.gain


SdrDevice = Union[MockRtlSdr, rtlsdr.RtlSdr]
