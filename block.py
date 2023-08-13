import re
import subprocess
import time

# 로그 파일 경로
log_file_path = "/var/log/auth.log"

# 차단 시도 실패 횟수
max_failed_attempts = 5

# 차단 해제 대기 시간 (5분)
unban_wait_time = 300

# 차단 함수
def ban(ip_address):
    iptables_cmd = f"iptables -A INPUT -s {ip_address} -j DROP"
    subprocess.run(iptables_cmd, shell=True)
    print(f"Blocked IP: {ip_address}")

# 차단 해제 함수
def unban(ip_address):
    iptables_cmd = f"iptables -D INPUT -s {ip_address} -j DROP"
    subprocess.run(iptables_cmd, shell=True)
    print(f"Unblocked IP: {ip_address}")

# 로그 파일을 열어 실패한 SSH 로그인 시도를 감지하고 차단
def main():
    failed_attempts = {}

    while True:
        current_time = time.time()
        
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                if "Failed password" in line:
                    ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        ip_address = ip_match.group(1)
                        if ip_address not in failed_attempts:
                            failed_attempts[ip_address] = {'count': 1, 'timestamp': current_time}
                        else:
                            if current_time - failed_attempts[ip_address]['timestamp'] <= 60:
                                failed_attempts[ip_address]['count'] += 1
                                if failed_attempts[ip_address]['count'] >= max_failed_attempts:
                                    ban(ip_address)
                            else:
                                failed_attempts[ip_address] = {'count': 1, 'timestamp': current_time}
                
        # 차단 해제 확인
        for ip, data in failed_attempts.copy().items():
            if current_time - data['timestamp'] >= unban_wait_time:
                unban(ip)
                del failed_attempts[ip]

        time.sleep(10)  # 로그를 주기적으로 확인하기 위해 잠시 대기

if __name__ == "__main__":
    main()

