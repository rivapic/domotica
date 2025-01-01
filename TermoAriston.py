#!/usr/bin/python3

##pip install aquaaristonremotethermo
from aquaaristonremotethermo.aristonaqua import AquaAristonHandler
import json
import time

print("Termo")

ApiInstanceAqua = AquaAristonHandler(username='',password='',boiler_type='velis')

ApiInstanceAqua.start()

while not ApiInstanceAqua.available :
    time.sleep(1)

#### Aapagmos
#ApiInstanceAqua.set_http_data(power="False")


while True:
    jsonvar = ApiInstanceAqua.sensor_values
    print("POWER=" , jsonvar['power']['value'])
    print("HEATING=" , jsonvar['heating']['value'])
    print("Temperatura Actual= ", jsonvar['current_temperature']['value'])
    print("Temperatura Objetivo= ", jsonvar["required_temperature"]['value'])
    print("Tiempo requerido= ", jsonvar["remaining_time"]['value'])
    print("Duchas Disponibles= ", jsonvar["showers"]['value'])
    print("Modo", jsonvar["mode"]['value'])
    time.sleep(5)

#dumpvar = json.dumps(jsonvar,indent = 4)
#ApiInstanceAqua = AquaAristonHandler(username='rivapic@gmail.com',password='Estaeslaredavir1-',boiler_type='velis')print(dumpvar)


#ApiInstanceAqua.set_http_data(power=True)
# switch 
#ApiInstanceAqua.set_http_data(power=(not jsonvar['power']['value']))

#dumpvar = json.dumps(ApiInstanceAqua.sensor_values,indent = 4)
#jsonvar = json.loads(dumpvar)
#print("POWER ON=" , jsonvar['power']['value'])
#print("api stop")

time.sleep(10)
ApiInstanceAqua.stop()
