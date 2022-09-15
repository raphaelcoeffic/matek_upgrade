# matek_upgrade

Command line tool to upgrade Mateksys CRSF PWM converters and maybe more.

## Usage

```
python matek_upgrade.py [serial device] [firmware file]
```

When everything is alright, the output should look like this:
```
% python matek_upgrade.py /dev/cu.usbserial-DN009KYL ~/Downloads/CRSF_PWM_fw/crsf_pwm_v2.3.0.bin
Hooked into bootloader (device ID = 1)
File hash OK for device
 |████████████████████████████████████████████████████████████████████████████████████████████████████| 100.4% 
Update sucessful
```

If you see the error `ModuleNotFoundError: No module named 'serial'` run `pip install pyserial` to install the required dependency.
