import cv2
from PIL import Image
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import time
import socket
import urlparse
from datetime import datetime


camera = cv2.VideoCapture(0)



class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		query_components = urlparse.parse_qs(urlparse.urlparse(self.path).query) 
		
		#/best to auto optimize 
		if (urlparse.urlparse(self.path).path == '/best'):
			self.send_response(301)
			self.send_header('Location','/?q=20&gray=true&resize=-2')
			self.end_headers()
			return
		
		self.send_response(200)
		self.send_header('Cache-Control', 'no-store, no-cache, private, max-age=0')
		self.send_header('Content-type','multipart/x-mixed-replace; boundary=--frame')
		self.send_header('Pragma', 'no-cache')
		self.end_headers()
		
		while True:
			try:
				return_value, image = camera.read()
				if not return_value:
					continue 


				if ('blue' in query_components):
					image[:,:,1] = 0
					image[:,:,2] = 0

				if ('flip' in query_components):
					image = cv2.flip(image,1)

				if ('gray' in query_components):
					image = cv2.cvtColor( image, cv2.COLOR_RGB2GRAY )

				#after set image color 
				ts =  datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
				cv2.putText(image, ts, (10, image.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

				if ('resize' in query_components):
					height, width = image.shape[:2]
					resizePercent = int( float( query_components['resize'][0] ) )
					if resizePercent > 0: 
						#make image bigger
						image = cv2.resize(image, (width*resizePercent, height*resizePercent)) 
					elif resizePercent < 0:
						#make image smaller
						resizePercent = abs(resizePercent)
						image = cv2.resize(image, (width/resizePercent, height/resizePercent)) 
					  
				if ('q' in query_components):
					r, buf = cv2.imencode(".jpg",image, [cv2.IMWRITE_JPEG_QUALITY, int(query_components['q'][0])]) 
				else:
					r, buf = cv2.imencode(".jpg",image) 


				self.wfile.write("--frame")
				self.send_header('Content-type','image/jpeg')
				self.send_header('Content-length',str(len(buf)))
				self.end_headers()
				self.wfile.write(bytearray(buf))
	
			except KeyboardInterrupt:
				#break
				pass
		return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

def GetLocalIp():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("google.com",80))
	PCip = s.getsockname()[0]
	s.close()
	return PCip


def main():
	try:
		serverport = 80

		server = ThreadedHTTPServer(('0.0.0.0', serverport), CamHandler)
		print "Server start on http://"+GetLocalIp()+':'+str(serverport)+'/'
		
		server.serve_forever()
	except KeyboardInterrupt:
		camera.release()
		server.socket.close()

if __name__ == '__main__':
	main()

