from pymavlink import mavutil
import threading
import xmltodict
import sys

class GCSState():
    """
    Root data model item for gcsstation.

    This class contains the state of the gcs, to include lists of connections, mavs,
    and mavlink components, fleet management data, and configuration  data
    """
    def __init__(self):
        self.connections = []
        self.mavs = []
        self.components = []
        self.config = GCSConfig()

        return

class Connection:
    """
    Encapsulates a connection via serial, TCP, or UDP ports, etc.
    """
    def __init__(self, port, number):
        self.port = port
        self.number = number
        self.mavs = []
        print(self.port)
        print(self.number)
        # TODO figure out how to handle these
        if port == "UDP" or port == "TCP":
            return

        # TODO
        # The vision is to ulimately split connections and MAVs, so one connection
        # can support multiple MAVs. For now, we cheat and just build a single MAV
        # per connection, with the pymavlink.mavlink_connection() object stored in
        # the MAV object.
        newmav = MAV()
        newmav.connect(port, number)
        self.mavs.append(newmav)


    def getPortDead(self):
        """
        Returns whether the connection is alive or dead
        """
        if len(self.mavs) == 0:
            return True
        else:
            return self.mavs[0].master.portdead

class MAV:
    """
    This class encapsulates a micro air vehicle (MAV), and theoretically represents the
    state of that vehicle at any moment in time. It is the responsibility of this class to
    communicate with the MAV and keep its internal state up to date.

    My vision is to separate serial connections from MAVs, so that one connection can
    have multiple MAVs. Unfortunately pymavlink doesn't work this way... the connection
    and MAV are interwoven in one mavfile object from pymavlink.mavutil. For now I am
    wrapping the mavfile object inside the MAV class, with the hope that we can later
    separate the two. Most of that work will probably be done inside the MAV class and
    Connection class.
    """
    def __init__(self):
        self.systemid = None
        self.master = None

        # The class exposes a number of events that other code can subscribe to
        self.on_heartbeat = []
        self.on_param_received = []
        self.on_mission_event = []
        # etc... these are just placeholders for now to illustrate how this might work

    def connect(self, port, number):
        print("Connecting to " + port)
        self.master = mavutil.mavlink_connection(port, baud=number)

        self.thread = threading.Thread(target=self.process_messages)
        self.thread.setDaemon(True)
        self.thread.start()

        #self.master.message_hooks.append(self.check_heartbeat)
        #self.master.message_hooks.append(self.log_message)


    def log_message(self,caller,msg):
        if msg.get_type() != 'BAD_DATA':
            print(str(msg))
        return

    def process_messages(self):
        """
        This runs continuously. The mavutil.recv_match() function will call mavutil.post_message()
        any time a new message is received, and will notify all functions in the master.message_hooks list.
        """
        while True:
            msg = self.master.recv_match(blocking=True)
            if not msg:
                return
            if msg.get_type() == "BAD_DATA":
                if mavutil.all_printable(msg.data):
                    sys.stdout.write(msg.data)
                    sys.stdout.flush()

            mtype = msg.get_type()
            if mtype == "VFR_HUD":
                self.altitude = mavutil.evaluate_expression("VFR_HUD.alt", self.master.messages)
                self.airspeed = mavutil.evaluate_expression("VFR_HUD.airspeed", self.master.messages)
                self.heading = mavutil.evaluate_expression("VFR_HUD.heading", self.master.messages)
                print("Altitude: " + str(self.altitude))

    def check_heartbeat(self,caller,msg):
        """
        Listens for a heartbeat message

        Once this function is subscribed to the dispatcher, it listens to every
        incoming MAVLINK message and watches for a 'HEARTBEAT' message. Once
        that message is received, the function updates the GUI and then
        unsubscribes itself.
        """

        if msg.get_type() ==  'HEARTBEAT':
            print("Heartbeat received from APM (system %u component %u)\n" % (self.master.target_system, self.master.target_system))
            self.system_id = self.master.target_system
            self.master.message_hooks.remove(self.check_heartbeat)

class GCSConfig:
    def __init__(self):
        self.settings = {}
        self.perspective = {}
        self.load_settings()
        self.load_perspective(self.settings['perspective'])


    def load_settings(self):
        """
        Load application configuration from an XML file
        """
        with open('settings.xml') as fd:
            self.settings = xmltodict.parse(fd.read())['settings']
        return

    def save_settings(self):
        """
        Save application configuration to an XML file
        """
        # TODO implement
        return

    def load_perspective(self, filename):
        """
        Load a perspective from an XML file
        """
        with open(filename) as fd:
            self.perspective = xmltodict.parse(fd.read())['perspective']

        return

    def save_perspective(self, filename):
        """
        Save this perspective to an XML file
        """
        # TODO implement
        return

if __name__ == "__main__":
    mav1 = MAV()
    mav1.connect('/dev/tty.usbmodemfa141',115200)
    print("Connected")
    i = 0
    while 0 < 1:
        i = 1 - i
