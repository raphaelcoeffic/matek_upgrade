import sys
import os
import serial
import hashlib

def verify_file_hash(data, size, deviceId):
    fileChecksum = data[size - 32:size]
    fileChecksum = fileChecksum.decode('ascii')
    # print('Hash in file: {}'.format(fileChecksum))
    h = hashlib.md5()
    h.update(data[0:size - 32])
    h.update(deviceId.to_bytes(1, byteorder='big'))
    # print('Computed hash: {}'.format(h.hexdigest()))
    return h.hexdigest() == fileChecksum

def checksum_uploader(data):
    checksum = 0
    for b in data:
        checksum += b
        checksum &= 255
    return b'\x01\x02\x03' + data + checksum.to_bytes(1, byteorder='big')

def crc16_uploader(data):
    crc = 0
    for b in data:
        crc = crc ^ b << 8
        for _n in range(0, 8):
            if crc & 32768 != 0:
                crc = crc << 1 ^ 4129
                continue
            crc = crc << 1
    crc = crc & 65535
    return b'\x01\x02\x03\x04' + data + crc.to_bytes(2, byteorder='big')

def chunked(size, data):
    for i in range(0, len(data), size):
        yield data[i:i+size]

def progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)

def upload_file(ser, data, deviceId, crcFct):

    length = len(data)
    uploaded = 0

    for pkt in chunked(256, data):

        # zero fill
        if len(pkt) < 256:
            pkt = pkt + bytes(256 - len(pkt))

        ser.write(crcFct(pkt))

        uploaded = uploaded + 256
        progress_bar(uploaded, length)

        # check reply
        rbuf = ser.read()
        if len(rbuf) != 1 or rbuf[0] != 0x06:
            print('\nError reply from device: {}'.format(rbuf[0]))
            return False

    # end of file
    ser.write(b'\x04')
    print()

    return True
        

def upgrade_crsf_converter(serial_port, fw_filename):
    ser = serial.Serial(serial_port, 115200, timeout=0.2)

    crcFct = None
    deviceId = b'\x00'

    while True:
        ser.reset_input_buffer()
        ser.write(b'upgrade')

        rbuf = ser.read(2)
        if len(rbuf) < 2:
            continue

        deviceId = rbuf[1]
        if deviceId < 0x01 or deviceId > 0xfe:
            continue

        if rbuf[0] == ord('C'):
            crcFct = crc16_uploader
        elif rbuf[0] == 0x15:
            crcFct = checksum_uploader
        else:
            continue

        break

    print('Hooked into bootloader (device ID = {})'.format(deviceId))

    fileSize = os.path.getsize(fw_filename)
    f = open(fw_filename, 'rb')
    fileData = f.read()
    f.close()

    if not verify_file_hash(fileData, fileSize, deviceId):
        print('Failed to verify file hash')
        return -1

    print('File hash OK for device')

    if upload_file(ser, fileData[0: fileSize - 32], deviceId, crcFct):
        print('Update sucessful')
        return 0
    else:
        print('Update failed')
        return -1

if __name__ == '__main__':
    upgrade_crsf_converter(sys.argv[1],sys.argv[2])
