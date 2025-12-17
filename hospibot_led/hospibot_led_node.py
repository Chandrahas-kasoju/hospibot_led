#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import ColorRGBA
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

        # Initialize Pi5Neo
        try:
            self.neo = Pi5Neo(SPI_DEVICE, LED_COUNT, SPI_SPEED)
            self.get_logger().info(f'Pi5Neo initialized on {SPI_DEVICE} with {LED_COUNT} LEDs')
            self.clear_leds()
        except Exception as e:
             self.get_logger().error(f'Failed to initialize Pi5Neo: {e}. Make sure SPI is enabled and accessible.')

    def listener_callback(self, msg):
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
