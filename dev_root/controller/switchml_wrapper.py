from switchml import SwitchML
import os
import sys
import glob
import yaml
import signal
import asyncio
import argparse
import logging
from concurrent import futures

from grpc_server import GRPCServer
from cli import Cli
from common import front_panel_regex, mac_address_regex, validate_ip

# Add BF Python to search path
bfrt_location = '{}/lib/python*/site-packages/tofino'.format(
    os.environ['SDE_INSTALL'])
sys.path.append(glob.glob(bfrt_location)[0])
import bfrt_grpc.client as gc

if __name__ == '__main__':

    # Parse arguments
    argparser = argparse.ArgumentParser(description='SwitchML controller.')
    argparser.add_argument('--program',
                           type=str,
                           default='switchml',
                           help='P4 program name. Default: SwitchML')
    argparser.add_argument('--log-level',
                           default='INFO',
                           choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'],
                           help='Default: INFO')
    
    argparser.add_argument(
        '--switch-conf-meta',
        type=str,
        default=None,
        help=
        'YAML file describing hierarchical switch connection architecture and configuration. Default: None')

    args = argparser.parse_args()

    # Configure logging
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        sys.exit('Invalid log level: {}'.format(args.log_level))

    logformat = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='switchml.log',
                        filemode='w',
                        level=numeric_level,
                        format=logformat,
                        datefmt='%H:%M:%S')
    with open(args.switch_conf_meta) as f:
        confs = yaml.safe_load(f)
    ctrls = {}
    for sw_name in confs.keys():
        conf = confs[sw_name]
        args.switch_mac = conf['switch_mac'].strip().upper()
        args.switch_ip = conf['switch_ip'].strip()
        args.bfrt_ip = conf['bfrt_ip'].strip()
        args.bfrt_port = conf['bfrt_port']
        args.ports = conf['ports_file']
        args.use_multipipe = conf['use_multipipe']
        args.use_model = conf['use_model']
        args.switch_name = sw_name
        args.switch_conf_file = conf['switch_conf_file']

        if not mac_address_regex.match(args.switch_mac):
            sys.exit('Invalid Switch MAC address')
        if not validate_ip(args.switch_ip):
            sys.exit('Invalid Switch IP address')
        if not validate_ip(args.bfrt_ip):
            sys.exit('Invalid BFRuntime server IP address')

        ctrl = SwitchML()
        ctrl.setup(args.program, args.switch_mac, args.switch_ip, args.bfrt_ip,
                args.bfrt_port, args.ports, args.use_multipipe, args.use_model, args.switch_name, args.switch_conf_file)
        ctrls[sw_name] = ctrl
        # Start controller
        # ctrl.run()
    cli = Cli()
    cli.setup(ctrls, None, prompt='SwitchML', name='SwitchML controller')
    

    # Set up gRPC server
    grpc_server = GRPCServer(ip='[::]', port=50099)

    # Run event loop for gRPC server in a separate thread
    # limit concurrency to 1 to avoid synchronization problems in the BFRT interface
    grpc_executor = futures.ThreadPoolExecutor(max_workers=1)

    event_loop = asyncio.get_event_loop()

    try:
        # Start listening for RPCs
        grpc_future = grpc_executor.submit(
            grpc_server.run, event_loop, None, ctrls)

        cli.run()

        # Stop gRPC server and event loop
        event_loop.call_soon_threadsafe(grpc_server.stop)

        # Wait for gRPC thread to end
        grpc_future.result()

        # Stop event loop
        event_loop.close()

        # Close gRPC executor
        grpc_executor.shutdown()

    except Exception as e:
        pass

        

    # Flush log, stdout, stderr
    sys.stdout.flush()
    sys.stderr.flush()
    logging.shutdown()

    # Exit
    os.kill(os.getpid(), signal.SIGTERM)
