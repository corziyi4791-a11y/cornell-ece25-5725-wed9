import os
import sys
import math
import time
import board
import busio
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX
from constants.global_var import FILTER_BETA

# Try importing RPi.GPIO
try:
    import RPi.GPIO as GPIO
    HAVE_GPIO = True
except Exception:
    GPIO = None
    HAVE_GPIO = False

from constants.global_var import BAILOUT_GPIO

BAILOUT_PIN = 27

_bailout_triggered = False

def setup_env_for_pitft():
    os.putenv("SDL_VIDEODRIVER", "fbcon")
    os.putenv("SDL_FBDEV", "/dev/fb1")  
    os.putenv("SDL_MOUSEDRV", "TSLIB")     
    # Change '/dev/input/touchscreen' to your real path found in Phase 1:
    os.putenv("SDL_MOUSEDEV", "/dev/input/event1") 
    os.putenv("DISPLAY", "")

# ... (The rest of the file: setup_bailout_button, cleanup, etc. remains the same)
def _bailout_cb(channel):
    global _bailout_triggered
    print("[GPIO] Bailout button pressed")
    _bailout_triggered = True

def setup_bailout_button():
    if not HAVE_GPIO:
        print("[GPIO] RPi.GPIO not available, bailout button disabled")
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BAILOUT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
        BAILOUT_GPIO,
        GPIO.FALLING,
        callback=_bailout_cb,
        bouncetime=150
    )
    print(f"[GPIO] Bailout button set up on BCM {BAILOUT_GPIO}")

def check_bailout():
    return _bailout_triggered
    
def is_bailout_triggered():
    # If PUD_UP is used, input is False when pressed (connected to GND)
    return not GPIO.input(BAILOUT_PIN)

def cleanup_bailout_button():
    if not HAVE_GPIO:
        return
    try:
        GPIO.cleanup()
        print("[GPIO] Cleaned up")
    except Exception:
        pass

class Quaternion:
    def __init__(self, w, x, y, z):
        self.w, self.x, self.y, self.z = w, x, y, z
    
    def normalize(self):
        n = math.sqrt(self.w*self.w + self.x*self.x + self.y*self.y + self.z*self.z)
        if n == 0: return self
        self.w/=n; self.x/=n; self.y/=n; self.z/=n
        return self

    def __mul__(self, o):
        return Quaternion(
            self.w*o.w - self.x*o.x - self.y*o.y - self.z*o.z,
            self.w*o.x + self.x*o.w + self.y*o.z - self.z*o.y,
            self.w*o.y - self.x*o.z + self.y*o.w + self.z*o.x,
            self.w*o.z + self.x*o.y - self.y*o.x + self.z*o.w
        )

    def to_euler(self):
        sinr = 2*(self.w*self.x + self.y*self.z)
        cosr = 1 - 2*(self.x*self.x + self.y*self.y)
        roll = math.atan2(sinr, cosr)
        
        sinp = 2*(self.w*self.y - self.z*self.x)
        if abs(sinp)>=1: pitch = math.copysign(math.pi/2, sinp)
        else: pitch = math.asin(sinp)
        
        return math.degrees(roll), math.degrees(pitch)

class IMUHandler:
    def __init__(self):
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = ISM330DHCX(self.i2c)
            self.active = True
            print("[Hardware] IMU found.")
        except Exception as e:
            print(f"[Hardware] IMU Error (Running in Mock Mode): {e}")
            self.active = False
            self.q = Quaternion(1, 0, 0, 0)
            return

        self._calibrate_gyro()
        self._init_quaternion()

    def _calibrate_gyro(self):
        print("[Hardware] Calibrating Gyro...")
        self.gx_off = self.gy_off = self.gz_off = 0.0
        for _ in range(200):
            gx, gy, gz = self.sensor.gyro
            self.gx_off += gx
            self.gy_off += gy
            self.gz_off += gz
            time.sleep(0.005)
        self.gx_off /= 200
        self.gy_off /= 200
        self.gz_off /= 200
        print("[Hardware] Calibration Done.")

    def _init_quaternion(self):
        ax, ay, az = self.sensor.acceleration
        # Calculate initial roll/pitch from gravity vector
        initial_roll = math.atan2(ay, az)
        initial_pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
        
        cr = math.cos(initial_roll/2)
        sr = math.sin(initial_roll/2)
        cp = math.cos(initial_pitch/2)
        sp = math.sin(initial_pitch/2)
        
        self.q = Quaternion(cr*cp, sr*cp, cr*sp, -sr*sp).normalize()

    def update(self, dt):
        if not self.active: return 0, 0

        ax, ay, az = self.sensor.acceleration
        gx, gy, gz = self.sensor.gyro
        gx -= self.gx_off
        gy -= self.gy_off
        gz -= self.gz_off

        # Gyro integration
        q_delta = Quaternion(1.0, gx*dt*0.5, gy*dt*0.5, gz*dt*0.5)
        self.q = (self.q * q_delta).normalize()

        # Accelerometer correction (Gradient Descent step)
        accel_norm = math.sqrt(ax*ax + ay*ay + az*az)
        if accel_norm > 0.1:
            axn, ayn, azn = ax/accel_norm, ay/accel_norm, az/accel_norm
            q = self.q
            vx = 2*(q.x*q.z - q.w*q.y)
            vy = 2*(q.y*q.z + q.w*q.x)
            vz = q.w*q.w - q.x*q.x - q.y*q.y + q.z*q.z
            
            ex = (ayn*vz) - (azn*vy)
            ey = (azn*vx) - (axn*vz)
            ez = (axn*vy) - (ayn*vx)
            
            q_corr = Quaternion(1.0, FILTER_BETA*ex, FILTER_BETA*ey, FILTER_BETA*ez)
            self.q = (self.q * q_corr).normalize()

        return self.q.to_euler()
