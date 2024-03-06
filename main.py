import paramiko
import re
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from paramiko.ssh_exception import SSHException
import config

def get_gpu_usage(machine, ssh_jump_hosts, ssh_username='pu22', ssh_key_filepath='~/.ssh/id_rsa'):
    for ssh_jump_host in ssh_jump_hosts:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ssh_jump_host, username=ssh_username, key_filename=ssh_key_filepath)
            
            transport = client.get_transport()
            dest_addr = (machine + '.doc.ic.ac.uk', 22)
            local_addr = ('localhost', 22)
            channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)
            
            target_client = paramiko.SSHClient()
            target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            target_client.connect(machine + '.doc.ic.ac.uk', username=ssh_username, key_filename=ssh_key_filepath, sock=channel)
            
            stdin, stdout, stderr = target_client.exec_command(
                'nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader'
            )
            output = stdout.read().decode('utf-8')
            gpu_utilization, memory_used, memory_total = map(int, re.findall(r'\d+', output))
            memory_left = memory_total - memory_used
            memory_used_percent = (memory_used / memory_total) * 100
            
            target_client.close()
            client.close()
            
            return machine, gpu_utilization, memory_used, memory_total, memory_left, memory_used_percent
        except Exception as e:
            print(f"Attempt to connect through {ssh_jump_host} failed: {e}")
            continue

    # If all jump hosts fail, return None or a meaningful default
    print(f"All jump hosts failed for {machine}.")
    return machine, None, None, None, None, None


def print_usage_data(usage_data):
    headers = ['Machine', 'GPU Utilization (%)', 'Memory Used (MiB)', 'Total Memory (MiB)', 'Memory Left (MiB)', 'Memory Used (%)']
    
    # Sort by Memory Left (most to least)
    usage_data.sort(key=lambda x: x[4], reverse=True)
    
    column_widths = [max(len(str(x)) for x in (row[j] for row in usage_data)) for j in range(len(headers))]
    header_widths = [max(len(headers[j]), column_widths[j]) for j in range(len(headers))]
    
    header_row = "|".join(header.ljust(header_widths[k]) for k, header in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))
    
    for row in usage_data:
        row = list(row)  # Ensure row is a list for modification
        row[-1] = f"{row[-1]:.2f}"  # Format the memory used percentage
        formatted_row = "|".join(str(item).ljust(header_widths[k]) for k, item in enumerate(row))
        print(formatted_row)

def main():
    # SSH connection information
    ssh_username = config.SSH_USERNAME
    ssh_key_filepath = config.SSH_KEY_FILEPATH
    ssh_jump_hosts = config.SSH_JUMP_HOSTS
    targets = config.TARGETS

    usage_data = []
    
    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        future_to_machine = {executor.submit(get_gpu_usage, machine, ssh_jump_hosts, ssh_username, ssh_key_filepath): machine for machine in targets}
        for future in concurrent.futures.as_completed(future_to_machine):
            machine = future_to_machine[future]
            try:
                data = future.result()
                if data[1] is not None:  # Ensure data was successfully fetched
                    usage_data.append(data)
            except Exception as exc:
                print(f"{machine} generated an exception: {exc}")
    
    print_usage_data(usage_data)




if __name__ == "__main__":
    main()
