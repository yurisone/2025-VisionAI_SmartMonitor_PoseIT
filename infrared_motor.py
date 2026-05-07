from board import SCL, SDA
import busio
import time
from adafruit_pca9685 import PCA9685
import spidev

# SPI (MCP3008)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def read_adc(channel=0):
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

# I2C (PCA9685)
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# PWM 변환 함수
def angle_to_pwm(angle):
    pulse = 500 + (angle / 180) * 2000
    return int(pulse / 1000000 * 50 * 65535)

# 부드럽게 모터 움직이기
def move_servo_smooth(channel, current_angle, target_angle, delay=0.015):
    step = 1 if target_angle > current_angle else -1
    for angle in range(current_angle, target_angle + step, step):
        pca.channels[channel].duty_cycle = angle_to_pwm(angle)
        time.sleep(delay)
    return target_angle

# 초기값
motor2_channel = 0  # 35kg (IR 센서)
motor3_channel = 1  # 150kg (가변저항)
current_angle2 = 90
current_angle3 = 90

update_interval = 1.0  # 1초마다 센서 읽기
last_update = time.time()

try:
    while True:
        now = time.time()
        if now - last_update >= update_interval:
            # 적외선 센서 → 모터3
            ir_adc = read_adc(0)  # CH0
            ir_voltage = (ir_adc / 1023) * 3.3
            if ir_voltage < 0.4:
                angle2 = 180
            elif ir_voltage > 2.5:
                angle2 = 0
            else:
                angle2 = int((2.5 - ir_voltage) / 2.1 * 180)
            print(f"[150kg] 전압: {ir_voltage:.2f}V → 각도: {angle2}°")

            current_angle2 = move_servo_smooth(motor2_channel, current_angle2, angle2)

            # 가변저항 → 모터2
            pot_adc = read_adc(1)  # CH1
            pot_voltage = (pot_adc / 1023) * 3.3
            angle3 = int((pot_voltage / 3.3) * 180)
            print(f"[35kg] 거리: {pot_adc} → 각도: {angle3}°")

            current_angle3 = move_servo_smooth(motor3_channel, current_angle3, angle3)

            last_update = now

except KeyboardInterrupt:
    print("종료됨")

finally:
    pca.deinit()
    spi.close()
