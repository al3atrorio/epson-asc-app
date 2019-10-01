from application import Application
import time

if __name__ == "__main__":
	
	print(" [*] Init application. To exit press CTRL+C")
	
	app = Application()

	if app.status == 'valid':
		app.run()
	else:
		print(" [x] Invalid Application Status. Exiting!")
		time.sleep(5)
		
