from . import eleksdraw
from . import gcode
from . import grbl
import tqdm
import halo
import time


class GCodeCommandWrapper:
    def __init__(self, device, gcode):
        self.device = device
        self.gcode = gcode

        # auto-populate commands from gcode
        for key in dir(gcode):
            if key.startswith('__'):
                continue
            func = getattr(gcode, key)
            setattr(self, key, self._make_wrapper(func))

    @staticmethod
    def _make_wrapper(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


def soft_reset(device):
    with eleksdraw.open_device(device) as device:
        device.run_command(grbl.GRBL.soft_reset())


def run_gcode(gcodes, device):
    with eleksdraw.open_device(device) as device:
        commands = GCodeCommandWrapper(device, gcode.GCode)
        with halo.Halo(text='Startup...', spinner='hearts'):
            device.run_command('', soft_error=True)
            if device.get_state() != eleksdraw.State.IDLE:
                raise RuntimeError('Device not ready to draw in state: {}'.format(device.get_state()))
            # GRBL recommends a soft reset on start.
            device.run_command(grbl.GRBL.soft_reset())
            commands.set_units_mm()
            commands.set_coordinates_absolute()
            commands.set_feed_rate(1000)

        for command in tqdm.tqdm(gcodes):
            device.run_command(command)

        with halo.Halo(text='Waiting for run to complete...', spinner='hearts'):
            while device.get_state() == eleksdraw.State.RUN:
                time.sleep(1.0)

        print('Final state: {}'.format(device.get_state()))