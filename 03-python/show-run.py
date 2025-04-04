#!/usr/bin/env python3
"""
Script to connect to an Arista device and retrieve the running configuration.
This is equivalent to the Ansible playbook functionality but using Netmiko directly.
"""

import os
import argparse
import time
from datetime import datetime
import netmiko
from netmiko.exceptions import NetmikoTimeoutException, AuthenticationException

def get_running_config(device_info):
    """Connect to device and get the running configuration."""
    try:
        # Establish connection to the device
        print(f"Connecting to {device_info['host']}...")
        
        # Add connection options to improve reliability
        device_info['conn_timeout'] = device_info.pop('timeout', 60)
        device_info['banner_timeout'] = 20
        device_info['auth_timeout'] = 30
        device_info['keepalive'] = 1
        
        net_connect = netmiko.ConnectHandler(**device_info)
        
        # Send command and get output
        print("Executing 'show running-config' command...")
        output = net_connect.send_command("show running-config", delay_factor=2)
        
        # Close the connection
        net_connect.disconnect()
        print("Connection closed.")
        
        return output
    
    except NetmikoTimeoutException:
        print(f"Connection timeout to {device_info['host']}")
        print("This could be due to:")
        print("1. The device is not reachable on the provided IP")
        print("2. SSH is not enabled or configured properly on the device")
        print("3. Firewall rules are blocking the connection")
        print("\nTrying to verify basic connectivity...")
        
        # Try a basic socket test to see if the port is open
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            result = s.connect_ex((device_info['host'], device_info.get('port', 22)))
            if result == 0:
                print(f"Port {device_info.get('port', 22)} is open on {device_info['host']}")
                print("The issue might be with SSH configuration or credentials")
            else:
                print(f"Port {device_info.get('port', 22)} is closed on {device_info['host']}")
                print("The device might not be reachable or SSH is not running")
        except Exception as e:
            print(f"Socket test failed: {str(e)}")
        finally:
            s.close()
        
        return None
    
    except AuthenticationException:
        print(f"Authentication failed for {device_info['host']}")
        print("Please verify your username and password")
        return None
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def save_output(output, hostname, output_dir="./command_outputs"):
    """Save the command output to a file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{output_dir}/{hostname}_running_config_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(output)
    
    print(f"Output saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Get running configuration from Arista device')
    parser.add_argument('--host', type=str, default='1.1.1.6', 
                        help='IP address or hostname of the device')
    parser.add_argument('--username', type=str, default='admin',
                        help='Username for authentication')
    parser.add_argument('--password', type=str, default='admin',
                        help='Password for authentication')
    parser.add_argument('--port', type=int, default=22,
                        help='SSH port (default: 22)')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Connection timeout in seconds (default: 120)')
    parser.add_argument('--output-dir', type=str, default='./command_outputs',
                        help='Directory to save output (default: ./command_outputs)')
    parser.add_argument('--save', action='store_true', 
                        help='Save output to file')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (more verbose output)')
    
    args = parser.parse_args()
    
    # Configure device parameters
    device = {
        'device_type': 'arista_eos',
        'host': args.host,
        'username': args.username,
        'password': args.password,
        'port': args.port,
        'timeout': args.timeout,
    }
    
    if args.debug:
        device['session_log'] = 'netmiko_session.log'
        import logging
        logging.basicConfig(filename='debug.log', level=logging.DEBUG)
        logging.getLogger("netmiko").setLevel(logging.DEBUG)
        print("Debug mode enabled. Logs will be written to debug.log and netmiko_session.log")
    
    # Get the running configuration
    output = get_running_config(device)
    
    if output:
        # Display the output
        print("\n=== RUNNING CONFIGURATION ===\n")
        print(output)
        
        # Save the output if requested
        if args.save:
            hostname = args.host.replace('.', '_')
            save_output(output, hostname, args.output_dir)

if __name__ == "__main__":
    main()