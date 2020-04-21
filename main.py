from Server.AnalysisServer import AnalysisServer


def main():
    analysis_server = AnalysisServer()
    analysis_server.run_server()
    analysis_server.shutdown_server()

if __name__ == '__main__':
    main()