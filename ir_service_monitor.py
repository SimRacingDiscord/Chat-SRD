import requests
import time


class ir_service_monitor:
    def __init__(self):
        self.maintenance_message = []
        self.status_url = "https://status.iracing.com/status.json"

    def fetch_status(self):
        response = requests.get(self.status_url)
        response.raise_for_status()  # Raises an exception if the response contains an HTTP error status code
        return response.json()

    def check_status(self):
        status = self.fetch_status()
        for service in status:
            if service[1][1] == 0:
                print(f"{service[0]} is down. {service[1][0]}")
            else:
                print(f"{service[0]} is up.")
        return status


maintenance_message = []
service_monitor = ir_service_monitor()
while True:
    status = service_monitor.fetch_status()

    if status["maint_messages"] != maintenance_message:
        maintenance_message = [status["maint_messages"]]
        print(f"Maintenance message has changed to: {maintenance_message}")
    else:
        print("No change in maintenance message")
        time.sleep(10)


# from response.json() each service name is a key in the dictionary, and each of those keys has a list of lists with two objects. the second object of each list will be a 1.0 or 0. If it is 1.0, the service is up
# get each service name and check the second object of each list. if it is 1.0, the service is up. if it is 0, the service is down.
# if any service is down, print the service name and the message associated with it.
# get the service name and the summary label into a dictionary
