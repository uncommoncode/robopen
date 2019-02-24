import serial
import time
import enum
from contextlib import contextmanager

DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD_RATE = 115200

# TODO(emmett): Get real boundaries
# TODO(emmett): eleksdraw units to mm
DRAW_WIDTH_EU = 170
DRAW_HEIGHT_EU = 255


class State(enum.Enum):
    IDLE = 0
    RUN = 1
    HOLD = 2
    JOG = 3
    ALARM = 4
    DOOR = 5
    CHECK = 6
    HOME = 7
    SLEEP = 8

STATE_MAP = {
    'idle': State.IDLE,
    'run': State.RUN,
    'hold': State.HOLD,
    'jog': State.JOG,
    'alarm': State.ALARM,
    'door': State.DOOR,
    'check': State.CHECK,
    'home': State.HOME,
    'sleep': State.SLEEP,
}


class EleksDrawDevice:
    def __init__(self, serial_port=DEFAULT_SERIAL_PORT):
        self.serial = None
        self.serial_port = serial_port

    def start(self):
        self.serial = serial.Serial(self.serial_port, baudrate=DEFAULT_BAUD_RATE)

    def stop(self):
        self.serial.close()
        self.serial = None

    def run_command(self, command, soft_error=False):
        data = (command + '\n').encode('utf-8')
        self.serial.write(data)

        buffer = b''
        has_response = False
        response = []

        while not has_response:
            if self.serial.in_waiting == 0:
                time.sleep(0.01)
                continue
            buffer += self.serial.read(self.serial.in_waiting)

            response = buffer.decode('utf-8').strip().split('\r\n')

            if response[-1] == 'ok':
                has_response = True
            elif b'error' in buffer:
                has_response = True
                if not soft_error:
                    raise RuntimeError(response[0])
            elif command == '':
                return response

        return response

    def get_state(self):
        status_str, _ = self.run_command('?')
        status = status_str.strip('<>').split(',')
        full_state = status[0]
        # Extract our state removing any substate info
        state = full_state.partition(':')[0].lower()
        if state not in STATE_MAP:
            raise RuntimeError('Invalid state: {}'.format(state))
        return STATE_MAP[state]


@contextmanager
def open_device(serial_port=DEFAULT_SERIAL_PORT):
    device = EleksDrawDevice(serial_port=serial_port)
    try:
        device.start()
        yield device
    finally:
        device.stop()
