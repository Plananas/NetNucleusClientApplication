import atexit
import os
import win32service
import win32serviceutil
import win32event
import servicemanager
import socket

from ClientApp import Client

SERVICE_NAME = "NetworkAutomationClient"
DISPLAY_NAME = "Network Automation Client"

class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = DISPLAY_NAME

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.client = Client()

    def SvcStop(self):
        servicemanager.LogInfoMsg(f"{SERVICE_NAME}: Stop signal received.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.client.connected = False
        win32event.SetEvent(self.stop_event)
        servicemanager.LogInfoMsg(f"{SERVICE_NAME}: Service stopped.")

    def SvcDoRun(self):
        try:
            servicemanager.LogInfoMsg(f"{SERVICE_NAME}: Service is starting...")
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

            # Notify SCM the service is running
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            servicemanager.LogInfoMsg(f"{SERVICE_NAME}: Service is now running.")

            # Main service loop
            atexit.register(self.client.cleanup)
            self.client.run(servicemanager)

        except Exception as e:
            servicemanager.LogErrorMsg(f"{SERVICE_NAME}: Service failed with error: {e}")
            self.SvcStop()

if __name__ == "__main__":
    servicemanager.Initialize(SERVICE_NAME, os.path.basename(__file__))  # Proper initialization
    win32serviceutil.HandleCommandLine(MyService)
