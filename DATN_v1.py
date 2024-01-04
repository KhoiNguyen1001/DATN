from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QTextEdit, QPushButton, QWidget
from PyQt5 import uic
from PyQt5.QtCore import QThread, QObject, pyqtSignal
import sys, time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import pymcprotocol 
pymc3e1 = pymcprotocol.Type3E()
pymc3e1.connect("192.168.3.254", 5002) 
pymc3e2 = pymcprotocol.Type3E()
pymc3e2.connect("192.168.3.39", 2500)
HOST = '192.168.3.100'  # va IP trong javascript cua html
PORT = 8000
content = """
<!DOCTYPE html>
<html>
<head>
  <title>Dieu khien va giam sat xe AGV</title>
  <style>
  .grid-container {
    display: grid;
    grid-template-columns: auto auto auto;
    padding: 20px;
  }
  .grid-item {
    background-color: rgba(255, 255, 255, 0.8);
    padding: 20px;
    font-size: 50px;
    text-align: center;
  }
  h1{
    text-align: center;
    font-size: 50px;
    margin: 10px 3px;
  }
  .button{
    border: none;
    color: white;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 30px;
    margin: 4px 2px;
    cursor: pointer;
    position: increment;
    top: 90px;
    left: 20px;
  }

  .button1{
    background-color: white;
    color: black;
    border: 2px solid #04AA6D;
  }
  .button1:hover {
    background-color: #04AA6D;
    color: white;
  }

  .button2{
    background-color: white;
    color: black;
    border: 2px solid #04AA6D;
  }
  .button2:hover {
    background-color: #04AA6D;
    color: white;
  }

  .button3{
    background-color: white;
    color: black;
    border: 2px solid #04AA6D;
  }
  .button3:hover {
    background-color: #04AA6D;
    color: white;
   }
  </style>
</head>
<body>
  <h1>Dieu khien va giam sat xe AGV</h1>
  <div class="grid-container">
  <div class="grid-item" style="grid-area: 1 / 1 / span 1 / span 3">Nut nhan goi tram</div>
  <div class="grid-item" style="grid-area: 2 / 1 / span 1 / span 1">
  	<button id="bt0" class="button button1" onclick="myFunction('Home')">Home</button>
  </div>
  <div class="grid-item" style="grid-area: 2 / 2 / span 1 / span 1">
    <button id="bt1" class="button button2" onclick="myFunction('Tram 1')">Tram 1</button>
  </div>
  <div class="grid-item" style="grid-area: 2 / 3 / span 1 / span 1">
  	<button id="bt2" class="button button3" onclick="myFunction('Tram 2')">Tram 2</button>
  </div>  
</div>

<script>
  function myFunction(command) {
    alert('Button clicked! Command: ' + command);
    fetch('http://192.168.3.100:8000', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: 'command=' + encodeURIComponent(command)
    })
    .then(response => response.text())
    .then(data => {
      console.log('Response from server:', data);
      // Handle the response from the server here
    })
    .catch(error => { console.error('Error:', error); });
  }
</script>
</body>
</html>
"""
# Auto update - Linking QCPU - Host Tasks
class Update_data(QObject):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        # define user's variable
        self.speed = 0
        self.speedLine = 0
        self.SpeedIn = 0
        self.SpeedOut = 0
        self.i = 0

    def do_work(self):
        while True: 
            ### Checking
            print(self.speed)
            
            # Shared Memory 1(host)->2(AGV)    
            Call = pymc3e1.batchread_bitunits(headdevice="M1", readsize=3)
            pymc3e2.batchwrite_bitunits(headdevice="M1", values=Call)

            # Share Memory 2(AGV)->1(host)
            Arrival = pymc3e2.batchread_bitunits(headdevice="M11", readsize=3)
            pymc3e1.batchwrite_bitunits(headdevice="M11", values=Arrival)
            
            ### Host
            Done = pymc3e1.batchread_bitunits(headdevice="M10", readsize=1)
            if((Arrival.count(1)==0)&(Done==[1])&(Call.count(1)>0)):
                pymc3e1.batchwrite_bitunits(headdevice="M10", values=[0])
                pymc3e2.batchwrite_bitunits(headdevice="Y0", values=[1])
            pymc3e2.batchwrite_wordunits(headdevice="D20", values=[self.speed, self.speedLine, self.SpeedIn, self.SpeedOut])

            ### Checking Connection between AGV QCPU - Station system (emitting - listenning ping signal)
            Connection_flag = pymc3e2.batchread_bitunits(headdevice="M101", readsize=1)
            if(Connection_flag == [1]):
                pymc3e2.batchwrite_bitunits(headdevice="M101", values=[0])

        self.stop_signal.emit()

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("E:\Mon hoc (Do an tot nghiep- TĐH)\Do an tot nghiep\DATN_ui_v1.ui",self)

        # Define
        self.button_OnDriver = self.findChild(QPushButton, "Button_OnDriver")
        self.button_OnDriver.clicked.connect(self.OnDriver)
        self.button_Stop = self.findChild(QPushButton, "Button_Stop")
        self.button_Stop.clicked.connect(self.STOP_ALL)

        self.button_Tram1 = self.findChild(QPushButton, "Button_Tram1")
        self.button_Tram2 = self.findChild(QPushButton, "Button_Tram2")
        self.button_Tram3 = self.findChild(QPushButton, "Button_Tram3")
        self.button_Tram1.clicked.connect(self.Call_Home)
        self.button_Tram2.clicked.connect(self.Call_Tram1)
        self.button_Tram3.clicked.connect(self.Call_Tram2)
        
        ### Nhap input (speed)
        self.Speed = self.findChild(QTextEdit,"textEdit_Speed")
        self.Speed.setText(f'1000')
        self.Speed_Line = self.findChild(QTextEdit,"textEdit_Speed_line")
        self.Speed_Line.setText(f'900')
        self.Speed_In = self.findChild(QTextEdit,"textEdit_Inner")
        self.Speed_In.setText(f'450')
        self.Speed_Out = self.findChild(QTextEdit,"textEdit_Outer")
        self.Speed_Out.setText(f'940')
        ### Send input (speed) ra PLC
        self.sentspeed = self.findChild(QPushButton,"Button_SendSpeed")
        self.sentspeed.clicked.connect(self.sent)

        self.Link_CPU = self.findChild(QPushButton,"Button_LinkCPU")
        # Thread:
        self.thread = QThread()
        self.update_data = Update_data()
        self.update_data.moveToThread(self.thread)
        self.thread.started.connect(self.update_data.do_work)
        self.Link_CPU.clicked.connect(self.thread.start)

        # Show the app
        self.show()

    ### ON, Setup, Stop System
    def OnDriver(self):
        pymc3e2.batchwrite_bitunits(headdevice="Y0", values=[1, 1, 1, 0, 1])
        pymc3e2.batchwrite_bitunits(headdevice="Y61", values=[1, 1])
        self.button_OnDriver.setEnabled(False)
    def STOP_ALL(self):
        pymc3e2.batchwrite_bitunits(headdevice="Y1", values=[0, 0])
        self.button_OnDriver.setEnabled(True)
    def sent(self):
        text = self.Speed.toPlainText()
        text1 = self.Speed_Line.toPlainText()
        text2 = self.Speed_In.toPlainText()
        text3 = self.Speed_Out.toPlainText()
        # Gan bien vao chuong trinh chay 
        self.update_data.speed = int(text)
        self.update_data.speedLine = int(text1)
        self.update_data.SpeedIn = int(text2)
        self.update_data.SpeedOut = int(text3)

    ### Call Station
    def Call_Home(self):
        pymc3e1.batchwrite_bitunits(headdevice="M1", values=[1])
    def Call_Tram1(self):
        pymc3e1.batchwrite_bitunits(headdevice="M2", values=[1])
    def Call_Tram2(self):
        pymc3e1.batchwrite_bitunits(headdevice="M3", values=[1])

def app_GUI():
    app = QApplication(sys.argv)
    UIWindow = UI()
    app.exec_()

class NeuralHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = parse_qs(post_data)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Access POST data and perform actions
        if 'command' in parsed_data:
            message = parsed_data['command'][0]
            print(message)
            if(message == 'Home'):
              pymc3e1.batchwrite_bitunits(headdevice="M1", values=[1])
            if(message == 'Tram 1'):
              pymc3e1.batchwrite_bitunits(headdevice="M2", values=[1])
            if(message == "Tram 2"):
              pymc3e1.batchwrite_bitunits(headdevice="M3", values=[1])
        else:
            self.wfile.write(f"No message received!")

def server_hosting():
    server = HTTPServer((HOST, PORT), NeuralHTTP)
    print("Server now running...")
    server.serve_forever()
    server.server_close()
    print("server stopped!")

if __name__ == '__main__':
    server_thread = threading.Thread(target=server_hosting)
    GUI_thread = threading.Thread(target=app_GUI)
    server_thread.start()
    GUI_thread.start()
    server_thread.join()
    GUI_thread.join()