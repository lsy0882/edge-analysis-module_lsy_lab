from Server.AnalysisServer import AnalysisServer
import argparse

def main(host, port, debug, display, show_scale):
    analysis_server = AnalysisServer(host=host, port=port, debug=debug, display=display, show_scale=show_scale)
    analysis_server.run_server()
    analysis_server.shutdown_server()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check that you enter parameters and server is turned on")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Server ip")
    parser.add_argument("--port", type=int, default=10001, help="Server port")
    parser.add_argument("--debug", type=bool, default=False, help="Debug")
    parser.add_argument("--display", type=bool, default=False, help="Display")
    parser.add_argument("--show_scale", type=int, default=1, help="Show scale")

    opt = parser.parse_known_args()[0]
    main(opt.ip, opt.port, opt.debug, opt.display, opt.show_scale)