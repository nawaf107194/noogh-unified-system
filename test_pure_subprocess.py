import subprocess
print("Running subprocess.run...")
result = subprocess.run(
    "echo 'SUCCESS' > /tmp/noogh_test_alive.txt",
    shell=True,
    capture_output=True,
    text=True,
    timeout=5
)
print("Finished. Return code:", result.returncode)
print("Stdout:", result.stdout)
print("Stderr:", result.stderr)
