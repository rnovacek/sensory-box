
# Before first run:
# >>> import upip
# >>> upip.install('micropython-uasyncio')


try:
    import uasyncio as asyncio
    from machine import Pin, ADC, PWM
    from neopixel import NeoPixel
    print('Running on ESP')
except ImportError:
    print('Running on computer')
    import asyncio


class Queue:
    def __init__(self):
        self._queue = []

    async def get(self):
        while True:
            if self._queue:
                return self._queue.pop(0)
            await asyncio.sleep_ms(1)

    def put(self, data):
        self._queue.append(data)

    async def wait_for_data(self, timeout):
        for _ in range(timeout):
            if self._queue:
                return True
            await asyncio.sleep_ms(1)
        return False


class Event:
    BUTTON_ON = 1
    BUTTON_OFF = 2
    ANALOG_VALUE = 3
    JOYSTICK = 4
    SCROLL_DIFF = 5


class Button:
    ON = 0
    OFF = 1

    def __init__(self, name, pin, queue, inverse=False):
        self.name = name
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.queue = queue
        self.inverse = inverse
        mode = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.irq = self.pin.irq(trigger=mode, handler=self._callback)
        self.loop = asyncio.get_event_loop()
        self._last_value = self.pin.value()
        self._debouncing = False

    def value(self):
        return self.pin.value()

    def _callback(self, value):
        if self._debouncing:
            return
        self.loop.create_task(self._callback_later())

    async def _callback_later(self):
        self._debouncing = True

        prev_value = self.pin.value()
        await asyncio.sleep(0.005)
        value = self.pin.value()
        if value == prev_value and value != self._last_value:
            is_on = value == self.ON
            if is_on != self.inverse:
                self.queue.put((Event.BUTTON_ON, self.name))
            else:
                self.queue.put((Event.BUTTON_OFF, self.name))
            self._last_value = value
        self._debouncing = False


class LED:
    PWM_MIN = 0
    PWM_MAX = 1023
    PWM_FREQ = 500

    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT, value=1)
        self.pwm = PWM(self.pin, freq=self.PWM_FREQ)
        # Workaround for PWM not working after restart
        self.pwm.deinit()
        self.pwm = PWM(self.pin, freq=self.PWM_FREQ)

    def set_intensity(self, value):
        if value < self.PWM_MIN or value > self.PWM_MAX:
            raise ValueError('Intensity must be between 0 and 1023')
        self.pwm.duty(value)

    def on(self):
        self.pwm.duty(self.PWM_MAX)

    def off(self):
        self.pwm.duty(self.PWM_MIN)


class Analog:
    POLLING_INTERVAL = 0.005
    THRESHOLD = 20

    def __init__(self, name, pin, queue=None):
        self.name = name
        self.pin = Pin(pin, Pin.IN)
        self.adc = ADC(self.pin)
        self.queue = queue
        if queue:
            self.loop = asyncio.get_event_loop()
            self.loop.create_task(self._read())
        self._old_value = self.value()

    def value(self):
        """Return value of Analog input, range 0 - 4096"""
        return self.adc.read()

    async def _read(self):
        while True:
            value = self.value()
            if abs(value - self._old_value) > self.THRESHOLD:
                self._old_value = value
                self.queue.put((Event.ANALOG_VALUE, self.name, value))
            await asyncio.sleep(self.POLLING_INTERVAL)


class ColorButton:
    def __init__(self, name, pin_button, pin_led, queue):
        self.led = LED(pin_led)
        self.button = Button(name, pin_button, queue)

    def button_value(self):
        return self.button.value()

    def set_intensity(self, intensity):
        self.led.set_intensity(intensity)

    def on(self):
        self.led.on()

    def off(self):
        self.led.off()


class Dial:
    ENC_STATES = (
        0,   # 00 00
        -1,  # 00 01
        1,   # 00 10
        0,   # 00 11
        1,   # 01 00
        0,   # 01 01
        0,   # 01 10
        -1,  # 01 11
        -1,  # 10 00
        0,   # 10 01
        0,   # 10 10
        1,   # 10 11
        0,   # 11 00
        1,   # 11 01
        -1,  # 11 10
        0    # 11 11
    )

    def __init__(self, name, button_pin, scroll_1_pin, scroll_2_pin, queue, scale=4):
        self.name = name
        self.queue = queue
        self.scale = scale
        self.pin_1 = Pin(scroll_1_pin, Pin.IN)
        self.pin_2 = Pin(scroll_2_pin, Pin.IN)
        mode = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.loop = asyncio.get_event_loop()
        self.irq_1 = self.pin_1.irq(trigger=mode, handler=self._callback)
        self.irq_2 = self.pin_2.irq(trigger=mode, handler=self._callback)
        self.button = Button(name, button_pin, queue)
        self._pos = 0
        self._readings = 0
        self._last = 0

    def _callback(self, line):
        self._readings = (self._readings << 2 | self.pin_1.value() << 1 | self.pin_2.value()) & 0x0f
        diff = self.ENC_STATES[self._readings]
        if diff != 0:
            self.loop.create_task(self._callback_later(diff))

    async def _callback_later(self, diff):
        self._pos += diff
        value = self._pos // self.scale
        if value != self._last:
            self.queue.put((Event.SCROLL_DIFF, self.name, value - self._last))
            self._last = value

    @property
    def value(self):
        return self._pos*self.scale

    def reset(self):
        self._pos = 0


class Joystick:
    THRESHOLD = 100

    def __init__(self, name, pin_x, pin_y, queue):
        self.name = name
        self.pin_x = Analog(None, pin_x)
        self.pin_y = Analog(None, pin_y)
        self.queue = queue
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self._read())
        self._old_x = self.get_x()
        self._old_y = self.get_y()

    def get_x(self):
        return self.pin_x.value()

    def get_y(self):
        return self.pin_y.value()

    async def _read(self):
        while True:
            x = self.get_x()
            y = self.get_y()
            if abs(x - self._old_x) > self.THRESHOLD or abs(y - self._old_y) > self.THRESHOLD:
                self._old_x = x
                self._old_y = y
                self.queue.put((Event.JOYSTICK, self.name, x, y))
            await asyncio.sleep(Analog.POLLING_INTERVAL)


class Strip(NeoPixel):
    LED_COUNT = 20

    def __init__(self, pin):
        super().__init__(Pin(pin, Pin.OUT), self.LED_COUNT)

    def set_east(self, color):
        self.set_range(0, 3, color)

    def set_south(self, color):
        self.set_range(4, 9, color)

    def set_west(self, color):
        self.set_range(10, 13, color)

    def set_north(self, color):
        self.set_range(14, 19, color)

    def set_range(self, start, stop, color):
        for i in range(start, stop + 1):
            board.strip[i] = color


class Board:
    def __init__(self, loop):
        self.loop = loop
        self.queue = Queue()

        self.switch_north = Button('switch-north', 23, self.queue, inverse=True)
        self.switch_east = Button('switch-east', 19, self.queue, inverse=True)
        self.switch_south = Button('switch-south', 22, self.queue, inverse=True)
        self.switch_west = Button('switch-west', 21, self.queue, inverse=True)

        self.color_button_red = ColorButton('colorbutton-red', 13, 12, self.queue)
        self.color_button_green = ColorButton('colorbutton-green', 27, 14, self.queue)
        self.color_button_blue = ColorButton('colorbutton-blue', 26, 25, self.queue)

        self.button_red = Button('button-red', 5, self.queue)
        self.button_green = Button('button-green', 17, self.queue)
        self.button_blue = Button('button-blue', 16, self.queue)

        self.led_red = LED(0)
        self.led_green = LED(2)
        self.led_blue = LED(15)

        self.led_picture = LED(4)
        self.light_sensor = Analog('light', 33, self.queue)

        self.dial = Dial('dial', 32, 35, 34, self.queue)

        self.joystick = Joystick('joystick', 36, 39, self.queue)

        self.strip = Strip(18)

    async def get_event(self):
        return await self.queue.get()


def set_intensity_all(value):
    for led in [
        board.color_button_red,
        board.color_button_green,
        board.color_button_blue,
        board.led_red,
        board.led_green,
        board.led_blue,
        board.led_picture,
    ]:
        led.set_intensity(value)
    for j in range(board.strip.LED_COUNT):
        board.strip[j] = value // 4, 0, 0
    board.strip.write()


async def init(board):
    for i in range(0, 200, 2):
        set_intensity_all(i)
        await asyncio.sleep(0.001)
    for i in range(200, 0, -2):
        set_intensity_all(i)
        await asyncio.sleep(0.001)
    set_intensity_all(0)


async def handler(board):
    await init(board)
    intensity = 10
    color = [False, False, False]
    no_color = 0, 0, 0
    while True:
        event, element, *data = await board.get_event()
        print('event', event, element, data)
        if event == Event.BUTTON_ON:
            if element == 'button-red':
                board.led_red.on()
                continue
            elif element == 'button-green':
                board.led_green.on()
                continue
            elif element == 'button-blue':
                board.led_blue.on()
                continue
            elif element == 'colorbutton-red':
                if color[0]:
                    board.color_button_red.off()
                    color[0] = False
                else:
                    board.color_button_red.on()
                    color[0] = True
            elif element == 'colorbutton-green':
                if color[1]:
                    board.color_button_green.off()
                    color[1] = False
                else:
                    board.color_button_green.on()
                    color[1] = True
            elif element == 'colorbutton-blue':
                if color[2]:
                    board.color_button_blue.off()
                    color[2] = False
                else:
                    board.color_button_blue.on()
                    color[2] = True
            print('switch', element, 'ON')
        elif event == Event.BUTTON_OFF:
            if element == 'button-red':
                board.led_red.off()
                continue
            elif element == 'button-green':
                board.led_green.off()
                continue
            elif element == 'button-blue':
                board.led_blue.off()
                continue
            print('switch', element, 'OFF')
        elif event == Event.SCROLL_DIFF:
            intensity -= data[0]
            if intensity < 0:
                intensity = 0
            if intensity > 255:
                intensity = 255
        elif event == Event.ANALOG_VALUE:
            if element == 'light':
                if data[0] < 30:
                    board.led_picture.on()
                else:
                    board.led_picture.off()

        c = (
            intensity if color[0] else 0,
            intensity if color[1] else 0,
            intensity if color[2] else 0,
        )

        board.strip.set_east(c if board.switch_east.value() else no_color)
        board.strip.set_south(c if board.switch_south.value() else no_color)
        board.strip.set_west(c if board.switch_west.value() else no_color)
        board.strip.set_north(c if board.switch_north.value() else no_color)
        board.strip.write()


loop = asyncio.get_event_loop()
board = Board(loop)
loop.run_until_complete(handler(board))
