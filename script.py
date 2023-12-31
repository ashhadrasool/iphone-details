import math
import subprocess
import os
import csv

def getUUIDs():
    try:
        script = 'idevice_id'
        result = subprocess.run([script], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            text = result.stdout
            lines = text.split('\n')
            # print(lines)
            uuids = []
            for line in lines:
                result = line.split(' ')
                uuid = result[0].strip()
                if uuid != '' and (len(result) <2 or result[1]!='(Network)'):
                    uuids.append(uuid)
                    break
            return uuids

        else:
            print("Error running the script:")
            print(result.stderr)
    except Exception as e:
        print(f"An error occurred: {e}")

def getDeviceDetails(uuid):
    details = {'uuid': uuid}

    csv_file = 'details.csv'

    with open(csv_file, newline='') as file:
        csv_reader = csv.DictReader(file)

        csv_data = {}
        lastFinish = ''
        lastGen = ''

        for i,row in enumerate(csv_reader):
            data = {}
            data['Identifier'] = row.get('Identifier')
            data['Storage'] = row.get('Storage')
            generation = row.get('Generation')
            model = row.get('Model')
            finish = row.get('Finish')

            if generation == '':
                generation = lastGen
            else:
                lastGen = generation

            if finish == '':
                finish = lastFinish
                generation = lastGen
            else:
                lastFinish = finish
                lastGen = generation
            models = model.split(', ')
            for m in models:
                data['Finish'] = finish
                data['Generation'] = generation
                csv_data[m] = data
        # print(csv_data)

    try:
        command = 'ideviceinfo -u ' +uuid
        result = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            text = result.stdout
            lines = text.split('\n')
            for line in lines:
                if 'ModelNumber' in line:
                    details['salesModel'] = line.split(': ')[1]
                    if details['salesModel'].startswith('N'):
                        details['salesModel'] = 'M'+details['salesModel'][1:]
                elif 'RegionInfo' in line:
                    details['region'] = line.split(': ')[1]
                elif 'ProductType' in line:
                    details['productType'] = line.split(': ')[1]
                elif 'ProductVersion' in line:
                    details['iosVersion'] = line.split(': ')[1]
                elif 'InternationalMobileEquipmentIdentity' in line:
                    details['imei'] = line.split(': ')[1]

        else:
            print("Error running the script:")
            print(result.stderr)

        details['model'] = csv_data[details['salesModel']]['Generation']
        details['color'] = csv_data[details['salesModel']]['Finish']


        command = 'idevicediagnostics ioregentry AppleARMPMUCharger -u ' +uuid
        result = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        batteryMaxCapacity = 1
        batteryCurrentCapacity = 5000
        if result.returncode == 0:
            text = result.stdout
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line == '':
                    continue
                if 'DesignCapacity' in line:
                    batteryMaxCapacity = int(lines[i+1].split('>')[1].split('<')[0])
                elif '>nominalChargeCapacity' in line or '>NominalChargeCapacity' in line:
                    val = int(lines[i+1].split('>')[1].split('<')[0])
                    if batteryCurrentCapacity > val:
                        batteryCurrentCapacity = val

            details['batteryHealth'] = min(100, math.ceil(batteryCurrentCapacity/batteryMaxCapacity*100))
        else:
            command = 'idevicediagnostics ioregentry AppleSmartBattery -u ' +uuid
            result = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                text = result.stdout

                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line == '':
                        continue
                    if 'DesignCapacity' in line:
                        batteryMaxCapacity = int(lines[i+1].split('>')[1].split('<')[0])
                    if '>nominalChargeCapacity' in line or '>NominalChargeCapacity' in line:
                        val = int(lines[i+1].split('>')[1].split('<')[0])
                        if batteryCurrentCapacity > val:
                            batteryCurrentCapacity = val

                details['batteryHealth'] = min(100, math.ceil(batteryCurrentCapacity/batteryMaxCapacity*100))
            else:
                print("Error running the script:")
                print(result.stderr)


        command = 'ideviceinfo -q com.apple.disk_usage -u ' +uuid
        result = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            text = result.stdout
            lines = text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line == '':
                    continue
                if 'TotalDiskCapacity' in line:
                    details['storage'] = str(int(int( line.split(': ')[1])/1000000000))+ ' GB'
        else:
            print("Error running the script:")
            print(result.stderr)

    except Exception as e:
        print(f"An error occurred: {e}")



    return details

def writeToCSV(data):
    csv_file = 'output.csv'

    new = False

    if not os.path.exists(csv_file):
        new = True

    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)

        if new:
            writer.writerow(['UUID', 'Model', 'Storage', 'Color', 'iOS version', 'IMEI', 'Product Type', 'Sales Model', 'Region', 'Max Battery Life'])


        for row in data:
            writer.writerow([row['uuid'], row['model'],row['storage'], row['color'], row['iosVersion'], row['imei'], row['productType'], row['salesModel'], row['region'], row['batteryHealth']])
            print('added: '+row['uuid'])



uuids = getUUIDs()

allDevices = []
if len(uuids) == 0:
    print('No connected devices')
else:
    print('Devices connected: ')
    for uuid in uuids:
        print(uuid)

for uuid in uuids:
    details = getDeviceDetails(uuid)
    writeToCSV([details])

