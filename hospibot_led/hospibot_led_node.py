#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import ColorRGBA, String
from pi5neo import Pi5Neo
import time

# LED strip configuration:
LED_COUNT = 10        # Number of LED pixels.
SPI_DEVICE = '/dev/spidev0.0'
SPI_SPEED = 800       # 800kHz

class LedController(Node):

    def __init__(self):
        super().__init__('led_controller')
        self.subscription = self.create_subscription(
            ColorRGBA,
            '/led_color',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        # In Christmas mode the strip runs its own light pattern and /led_color is ignored
        self.mode = 'WORK'
        self.last_mode_time = 0.0
        self.pattern_step = 0
        self.create_subscription(String, '/tele_mode', self.mode_callback, 10)
        self.create_timer(0.3, self.christmas_pattern)

        # Initialize Pi5Neo
        try:
            self.neo = Pi5Neo(SPI_DEVICE, LED_COUNT, SPI_SPEED)
            self.get_logger().info(f'Pi5Neo initialized on {SPI_DEVICE} with {LED_COUNT} LEDs')
            self.clear_leds()
        except Exception as e:
             self.get_logger().error(f'Failed to initialize Pi5Neo: {e}. Make sure SPI is enabled and accessible.')

    def mode_callback(self, msg):
        previous, self.mode = self.mode, msg.data.strip().upper()
        self.last_mode_time = time.time()
        if previous == 'CHRISTMAS' and self.mode != 'CHRISTMAS':
            self.clear_leds()

    def christmas_pattern(self):
        """Red, white and green lights running along the strip, with a sparkle now and then."""
        if self.mode != 'CHRISTMAS':
            return
        if time.time() - self.last_mode_time > 5.0:
            # The mode manager went silent: go back to normal
            self.mode = 'WORK'
            self.clear_leds()
            return
        colours = [(200, 0, 0), (140, 140, 140), (0, 150, 0)]
        self.pattern_step += 1
        sparkle = self.pattern_step % 12 == 0
        for i in range(LED_COUNT):
            r, g, b = (220, 170, 40) if sparkle else colours[(i + self.pattern_step) % len(colours)]
            self.neo.set_led_color(i, r, g, b)
        self.neo.update_strip()

    def listener_callback(self, msg):
        if self.mode == 'CHRISTMAS':
            return
        self.get_logger().info(f'Received color: R={msg.r}, G={msg.g}, B={msg.b}, A={msg.a}')
        # Pi5Neo uses (r, g, b) integers 0-255
        # Use Alpha (0.0-1.0) to scale brightness
        r = int(msg.r * msg.a)
        g = int(msg.g * msg.a)
        b = int(msg.b * msg.a)
        self.set_color(r, g, b)

    def set_color(self, r, g, b):
        self.neo.fill_strip(r, g, b)
        self.neo.update_strip()

    def clear_leds(self):
        self.set_color(0, 0, 0)

def main(args=None):
    rclpy.init(args=args)

    led_controller = LedController()

    try:
        rclpy.spin(led_controller)
    except KeyboardInterrupt:
        pass
    finally:
        led_controller.clear_leds()
        led_controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
