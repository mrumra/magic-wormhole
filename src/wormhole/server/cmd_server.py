from __future__ import print_function, unicode_literals
import os, time
from twisted.python import usage
from twisted.scripts import twistd

class MyPlugin(object):
    tapname = "xyznode"

    def __init__(self, args):
        self.args = args

    def makeService(self, so):
        # delay this import as late as possible, to allow twistd's code to
        # accept --reactor= selection
        from .server import RelayServer
        return RelayServer(
            str(self.args.rendezvous),
            str(self.args.transit),
            self.args.advertise_version,
            self.args.relay_database_path,
            self.args.blur_usage,
            signal_error=self.args.signal_error,
            stats_file=self.args.stats_json_path,
            allow_list=self.args.allow_list,
        )

class MyTwistdConfig(twistd.ServerOptions):
    subCommands = [("XYZ", None, usage.Options, "node")]

def start_server(args):
    c = MyTwistdConfig()
    #twistd_args = tuple(args.twistd_args) + ("XYZ",)
    base_args = []
    if args.no_daemon:
        base_args.append("--nodaemon")
    twistd_args = base_args + ["XYZ"]
    c.parseOptions(tuple(twistd_args))
    c.loadedPlugins = {"XYZ": MyPlugin(args)}

    print("starting wormhole relay server")
    # this forks and never comes back. The parent calls os._exit(0)
    twistd.runApp(c)

def kill_server():
    try:
        f = open("twistd.pid", "r")
    except EnvironmentError:
        print("Unable to find twistd.pid: is this really a server directory?")
        print("oh well, ignoring 'stop'")
        return
    pid = int(f.read().strip())
    f.close()
    os.kill(pid, 15)
    print("server process %d sent SIGTERM" % pid)
    return

def stop_server(args):
    kill_server()

def restart_server(args):
    kill_server()
    time.sleep(0.1)
    timeout = 0
    while os.path.exists("twistd.pid") and timeout < 10:
        if timeout == 0:
            print(" waiting for shutdown..")
        timeout += 1
        time.sleep(1)
    if os.path.exists("twistd.pid"):
        print("error: unable to shut down old server")
        return 1
    print(" old server shut down")
    start_server(args)
