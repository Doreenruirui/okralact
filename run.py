import subprocess

def run_job():
    subprocess.run('./scripts/run_train.sh', shell=True)
