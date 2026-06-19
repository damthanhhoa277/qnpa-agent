"""
Khởi động tất cả agents QNPA song song:
- Agent Linh: tư vấn Pancake inbox
- Agent Hải Marketing: theo dõi Meta Ads
"""
import subprocess
import sys
import os

agents = [
    {
        "name": "Linh",
        "cmd": [sys.executable, "qnpa_agent.py"],
        "log": "agent_linh.log"
    },
    {
        "name": "Hai_Marketing",
        "cmd": [sys.executable, "hai_marketing/hai_marketing_agent.py"],
        "log": "hai_marketing.log"
    }
]

processes = []
for agent in agents:
    log_file = open(agent["log"], "a", encoding="utf-8")
    p = subprocess.Popen(
        agent["cmd"],
        stdout=log_file,
        stderr=log_file,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    processes.append((agent["name"], p))
    print(f"[START] {agent['name']} — PID {p.pid}")

print("Tat ca agents da chay. Ctrl+C de dung.")
try:
    for name, p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nDung tat ca agents...")
    for name, p in processes:
        p.terminate()
        print(f"[STOP] {name}")
