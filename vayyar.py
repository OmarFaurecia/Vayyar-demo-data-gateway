""" 
Example reference code for EVK client 
""" 
from struct import unpack_from 
import json 
import numpy as np 
from websocket import create_connection 
from time import sleep 
import socket
import sys
import _thread

DTYPES = {
	0: np.int8,
	1: np.uint8,
	2: np.int16,
	3: np.uint16,
    4: np.int32,
    5: np.uint32,
    6: np.float32,
    7: np.float64,
 }
ASCII_RS = '\u001e'
ASCII_US = '\u001f'
server_address = ('192.168.7.7', 9000)
present = False
rPM = 0.0
activity = 0.0
running = True
def to_message(buffer): 
	 # parse MatNet messages from JSON / own binary format 
	if isinstance(buffer, str): 
		return json.loads(buffer) 
	seek = 0 
	# bufferSize = np.asscalar(np.frombuffer(buffer, np.int32, 1, seek)) 
	fields_len = np.asscalar(np.frombuffer(buffer, np.int32, 1, seek + 4)) 
	header_buff = buffer[seek + 8: seek + 8 + fields_len].decode('utf8') 
	id, keys = header_buff.split(ASCII_RS) 
	msg = {'ID': id, 'Payload': {}} 
	seek += 8 + fields_len 
	for key in keys.split(ASCII_US): 
		# fieldSize = np.asscalar(np.frombuffer(buffer, np.int32, 1, seek)) 
		dtype = DTYPES[np.asscalar(np.frombuffer(buffer, np.int32, 1, seek + 4))] 
		ndims = np.asscalar(np.frombuffer(buffer, np.int32, 1, seek + 8)) 
		dims = np.frombuffer(buffer, np.int32, ndims, seek + 12) 
		seek += 12 + ndims * np.int32().nbytes 
		data = np.frombuffer(buffer, dtype, np.prod(dims), seek) 
		seek += np.prod(dims) * dtype().nbytes
		msg['Payload'][key] = data.reshape(dims) if ndims else np.asscalar(data) 
	return msg 
	
def send_data(start_message):
	global present 
	global rPM
	global activity
	global running 
	print (start_message)

	while running :
		sleep(0.5)
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			
			print ('present = ', present,' activity level = ', activity, 'RPM = ', rPM)
			
			# Connect the socket to the port where the server is listening
			
			print('connecting to {} port {}'.format(*server_address))
			sock.connect(server_address)

			try:

				# Send data
				message = "{ \"event-name\":" + "\"radar-data\", " + "\"presence\":" + str(present).lower() + ", \"activity-level\":" + str(activity) + ", \"rpm\":"+ str(rPM) + "}"
				
				print('sending {!r}'.format(message))
				sock.sendall(str(message).encode())


			finally:
				
				print('closing socket')
				
			sock.close()
		except :
			print ("Sending thread problem, retrying")
			
	
	
def main(): 
	
	global present 
	global rPM
	global activity
	global running 
	# Create data transfer thread
			
	
	while running:
		try:
			# connect to server and echoing messages 
			listener = create_connection("ws://127.0.0.1:1234/") 
			# retrieve current configuration 
			listener.send(json.dumps({ 
				'Type': 'COMMAND', 
				'ID': 'SET_PARAMS', 
				'Payload': { 
				 
					'Cfg.Common.sensorOrientation.mode': 'advancedXYZ' ,
					'Cfg.Common.sensorOrientation.rotAxes': 'xx' ,
					'Cfg.Common.sensorOrientation.rotDeg': [180, 55] ,
					'Cfg.Common.sensorOrientation.transVec': [0,0,0] , 
					'Cfg.inCarCounting.carData.car_cabin_z_lims': [-0.6, 0.4] ,
					'Cfg.inCarCounting.carData.front_row_seat_center.foremost_position':  0.1 ,
					'Cfg.inCarCounting.carData.front_row_seat_center.rearmost_position':   0.2 ,
					'Cfg.inCarCounting.carData.rear_row_seat_center':  0.9 ,
					'Cfg.inCarCounting.carData.bench_seat_max_width': 0.4 ,
					'Cfg.SingleSeatDetection.BreathingTarget': [[0, 0.60, -0.20]] ,
					'Cfg.EVK_Breathing.phase_based.useEntireZgrid': 0 ,
					'Cfg.EVK_Breathing.phase_based.x_target_to_box_edge': 0.15 ,
					'Cfg.EVK_Breathing.phase_based.y_target_to_box_edge': 0.30 ,
					'Cfg.EVK_Breathing.phase_based.z_target_to_box_edge': 0.35 ,
					'Cfg.inCarCounting.algo_to_use': 2 ,
					'Cfg.SingleSeatDetection.presence_detection.algoType':  2 ,
					'Cfg.SingleSeatDetection.presence_detection.birth_threshold_sec':  1 ,
					'Cfg.SingleSeatDetection.presence_detection.max_life_threshold_sec':  2 ,
					'Cfg.SingleSeatDetection.breathing_detection.algoType': 1 ,
					'Cfg.EVK_Breathing.phase_based.svdLenDuration': 5 ,
					'Cfg.EVK_Breathing.phase_based.outputLenDuration': 11 ,
					'Cfg.EVK_Breathing.phase_based.rpm_estimation_rate_sec': 0.5 ,
					'Cfg.EVK_Breathing.phase_based.rpm_estimation_min_allowed_RPM': 8 ,
					'Cfg.EVK_Breathing.phase_based.rpm_estimation_max_allowed_RPM': 45 ,
				    'Cfg.SingleSeatDetection.activity.activity_buffer_duration_sec': 0.5,
					'Cfg.SingleSeatDetection.filter_breathing_output.enable': 1 ,
					'Cfg.SingleSeatDetection.filter_breathing_output.duration_sec': 5 ,
					'Cfg.SingleSeatDetection.filter_breathing_output.activity_level_threshold_to_ignore': 0.20 
					
					} 
			}))
				
			# set outputs for each frame 
			listener.send(json.dumps({ 
				'Type': 'COMMAND', 
				'ID': 'SET_OUTPUTS', 
				'Payload': { 'json_outputs': ['person_present','activity_level', 'breathing_rpm']}
			}))	 
			
			# start the engine - if WebGUI is not running 
			listener.send(json.dumps({ 
				'Type': 'COMMAND', 
				'ID': 'START', 
				'Payload': {'json_outputs': ['person_present','activity_level', 'breathing_rpm']}
			})) 
			# request for binary data. Can also request 'JSON_DATA' if 'json_outputs' were specified 
			listener.send(json.dumps({'Type': 'QUERY', 'ID': 'BINARY_DATA'}))
			listener.send(json.dumps({'Type': 'QUERY', 'ID': 'JSON_DATA'})) 
			print("Running! Waiting for messages...") 
			try:
				_thread.start_new_thread(send_data, ("Starting thread to send data ... \n ", ))
			except:
				print('Error starting thread. \n')
				
			while True:
				

				listener.send(json.dumps({'Type': 'QUERY', 'ID': 'JSON_DATA'})) 
				buffer = listener.recv() 
				data = to_message(buffer)
				# print(data)
				# json_data = json.loads(data)
				for x in data:
					if x == 'Payload':
						payload = data[x]
						for y in payload:
							if y == 'person_present':
								if payload[y] >= 1:
									present = True
								else: 
									present = False
							elif y == 'activity_level':
								activity = payload[y]
							elif y == 'breathing_rpm':
								
								if isinstance(payload[y], float) == False :
									rPM = 0.0
								else :
									rPM = payload[y]
			
				
			listener.send(json.dumps({ 'Type': 'COMMAND', 'ID': 'STOP', 'Payload': {} }))	
			print('\n Stopping engine ..')
			listener.close() 
		except:
			print('Error connecting to EVK engine...')
		
		
if __name__ == '__main__': main()
