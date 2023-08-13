import re, subprocess, time, threading
from datetime import datetime, timedelta

# 로그 파일 경로
log_file_path = "/var/log/auth.log"

# 차단 시도 실패 횟수
max_failed_attempts = 5


# 현재 시간 기준으로 1분 전의 시간 계산
current_time = datetime.now()
one_minute_ago = current_time - timedelta(minutes=1)

# 차단 함수
def ban(ip_address):
    iptables_cmd = f"iptables -A INPUT -s {ip_address} -j DROP"
    subprocess.run(iptables_cmd, shell=True, check=True)
    print(f"[*] Block {ip_address}..")

# 차단 해지 함수
def unban(ip_address):
    time.sleep(30)
    iptables_cmd = f"iptables -D INPUT -s {ip_address} -j DROP"
    subprocess.run(iptables_cmd, shell=True, check=True)
    print(f"[*] 5 min passed..")
    print(f"[*] Unblock {ip_address}..")

# 최근 1분 안의 로그만 파싱하는 함수
def parse_logs(log_file):
    recent_logs = []
    for log in log_file:
        log_time_str = log[:15]  # 로그에서 시간 정보 추출 (예: "Aug 13 04:29:24")
        log_time = datetime.strptime(log_time_str, "%b %d %H:%M:%S")
        temp_one_minute_ago = one_minute_ago.strftime("%b %d %H:%M:%S")
        formatted_one_minute_ago = datetime.strptime(temp_one_minute_ago, "%b %d %H:%M:%S")
        if log_time >= formatted_one_minute_ago:
            recent_logs.append(log)

    # 새로운 파일에 최근 1분 동안의 로그 저장
    with open("recent_logs.txt", 'w') as recent_log_file:
        recent_log_file.writelines(recent_logs)

    print("[*] Parse completed")
    return "recent_logs.txt"

# 로그 파일을 열어 실패한 SSH 로그인 시도를 감지하고 차단
def main():
    failed_attempts = {}

    with open(log_file_path, 'r') as log_file:
        with open(parse_logs(log_file), 'r') as recent_log_file:
            for line in recent_log_file:
                if "Failed password" in line:
                    ip_match = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        ip_address = ip_match.group(1)
                        if ip_address not in failed_attempts:
                            failed_attempts[ip_address] = 1
                        else:
                            failed_attempts[ip_address] += 1

            for ip_address, attempts in failed_attempts.items():
                if attempts >= max_failed_attempts:
                    # thread1 = threading.Thread(target=ban, args=(ip_address,))
                    ban(ip_address)
                    thread2 = threading.Thread(target=unban, args=(ip_address,))
                    # thread1.start()
                    thread2.start()
if __name__ == "__main__":
    main()
