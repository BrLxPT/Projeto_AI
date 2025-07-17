# plugins/hardware_control.py
import serial
import RPi.GPIO as GPIO  # Para Raspberry Pi

def control_gpio(pin, state):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, state)