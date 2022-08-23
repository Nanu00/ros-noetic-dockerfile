#!/bin/python3
import subprocess, argparse, json, os, sys, pwd, urllib.request, shutil

ps = subprocess.Popen(('lshw', '-C', 'display'), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
output = subprocess.check_output(('grep', 'vendor'), stdin=ps.stdout, encoding="UTF-8")
ps.wait()

if "nvidia" in output.lower():
    COMPOSE_FILE = "docker-compose-nvidia.yml"
else:
    COMPOSE_FILE = "docker-compose.yml"

EXIT_CODE = 0

def new(path):
    workspace_path = os.path.abspath(path)
    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
    elif os.path.isdir(workspace_path):
        pass
    else:
        print("Error creating workspace", file=sys.stderr)
        EXIT_CODE=1
        return

    os.chdir(workspace_path)

    user = os.environ['USER']
    with open(".env", "w") as env_file:
        env_file.write(f"UID={pwd.getpwnam(user).pw_uid}\n")
        env_file.write(f"GID={pwd.getpwnam(user).pw_gid}\n")
        env_file.write("HOSTNAME=ros-container\n")

    with urllib.request.urlopen(f"https://raw.githubusercontent.com/Nanu00/ros-noetic-dockerfile/main/{COMPOSE_FILE}") as response, open(COMPOSE_FILE, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    with urllib.request.urlopen("https://raw.githubusercontent.com/Nanu00/ros-noetic-dockerfile/main/Dockerfile") as response, open("Dockerfile", 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    print(f"Downloaded dockerfiles to {workspace_path}")

def build(info, workspace_path):
    workspace_path = os.path.abspath(workspace_path)
    os.chdir(workspace_path)
    user = os.environ['USER']
    subprocess.run(f"docker-compose -f {COMPOSE_FILE} build --build-arg UID={pwd.getpwnam(user).pw_uid} --build-arg GID={pwd.getpwnam(user).pw_gid} --build-arg UNAME={user}".split())
    if workspace_path not in info:
        info.append(workspace_path)

def list(info, running):
    print(f"Currently active workspaces: {len(info)}")
    for n, w in enumerate(info):
        if w in running:
            r = "Running"
        else:
            r = "Not running"
        print(f"{n+1} - {w} - {r}")

def run(info, running, workspace):
    if workspace.isdecimal():
        workspace = int(workspace)
        if workspace > len(info):
            print(f"Workspace #{workspace} does not exist!", file=sys.stderr)
            EXIT_CODE=1
            return
        workspace = info[workspace-1]
    else:
        workspace = os.path.abspath(workspace)

    if workspace not in info:
        print(f"Workspace \"{workspace}\" does not exist!", file=sys.stderr)
        EXIT_CODE=1
        return


    os.chdir(workspace)
    dc = subprocess.Popen(f"docker-compose -f {COMPOSE_FILE} up -d --no-build".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rcode = dc.wait()
    if rcode != 0:
        print(f"Docker error:\n{dc.stderr}", file=sys.stderr)
        EXIT_CODE=1
        return

    subprocess.run(["xhost", "+local:`docker inspect --format='{{ .Config.Hostname }}' $(docker ps -l -q)`"])

    running.append(workspace)

def stop(info, running, workspace):
    if workspace.isdecimal():
        workspace = int(workspace)
        if workspace > len(info):
            print(f"Workspace #{workspace} does not exist!", file=sys.stderr)
            EXIT_CODE=1
            return
        workspace = info[workspace-1]
    else:
        workspace = os.path.abspath(workspace)

    if workspace not in info:
        print(f"Workspace \"{workspace}\" does not exist!", file=sys.stderr)
        EXIT_CODE=1
        return

    if workspace not in running:
        print(f"Workspace \"{workspace}\" is not currently running", file=sys.stderr)
        EXIT_CODE=1
        return

    os.chdir(workspace)
    dc = subprocess.Popen(f"docker-compose -f {COMPOSE_FILE} down".split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rcode = dc.wait()
    if rcode != 0:
        print(f"Docker error:\n{dc.stderr}", file=sys.stderr)
        EXIT_CODE=1
        return

    running.remove(workspace)

def rm(info, workspace):
    if workspace.isdecimal():
        workspace = int(workspace)
        if workspace > len(info):
            print(f"Workspace #{workspace} does not exist!", file=sys.stderr)
            EXIT_CODE=1
            return
        else:
            k = info.pop(workspace-1)
            print(f"Workspace \"{k}\" removed")
    else:
        if workspace in info.keys():
            info.remove(workspace)
            print(f"Workspace \"{workspace}\" removed")
        else:
            print(f"Workspace \"{workspace}\" does not exist!", file=sys.stderr)
            EXIT_CODE=1
            return

def shell(info, running, workspace):
    if workspace.isdecimal():
        workspace = int(workspace)
        if workspace > len(info):
            print(f"Workspace #{workspace} does not exist!", file=sys.stderr)
            EXIT_CODE=1
            return
        workspace = info[workspace-1]
    else:
        workspace = os.path.abspath(workspace)

    if workspace not in info:
        print(f"Workspace \"{workspace}\" does not exist!", file=sys.stderr)
        EXIT_CODE=1
        return

    if workspace not in running:
        print(f"Workspace \"{workspace}\" is not currently running", file=sys.stderr)
        EXIT_CODE=1
        return

    os.chdir(workspace)
    f = os.fork()
    if f:
        os.execvp("docker-compose", f"docker compose -f {COMPOSE_FILE} exec -i ros_noetic /bin/$SHELL".split())
    return

if __name__ == "__main__":
    LOCK_FILE_PATH = "/tmp/ros-docker.lock"
    INFO_FILE_PATH = os.environ["HOME"] + "/.config/ros-docker/ros-docker.json"
    RUNNING_FILE_PATH = "/tmp/ros-docker"

    parser = argparse.ArgumentParser(description="Manage docker containers for ROS")
    subparsers = parser.add_subparsers(dest="subcommand")

    build_parser = subparsers.add_parser("new", help="Set up a workspace")
    build_parser.add_argument("path", metavar="PATH", help="Path to the workspace", default='.')

    build_parser = subparsers.add_parser("build", help="Build a docker container for a workspace")
    build_parser.add_argument("path", metavar="PATH", help="Path to the workspace", default='.')

    build_parser = subparsers.add_parser("rm", help="Delete a workspace")
    build_parser.add_argument("workspace", metavar="WORKSPACE", help="Remove a workspace by path or number", action="store")

    build_parser = subparsers.add_parser("run", help="Run a docker container for a workspace")
    build_parser.add_argument("workspace", metavar="WORKSPACE", help="Path or number to workspace", default='.')

    build_parser = subparsers.add_parser("stop", help="Stop a docker container for a workspace")
    build_parser.add_argument("workspace", metavar="WORKSPACE", help="Path or number to workspace", default='.')

    build_parser = subparsers.add_parser("shell", help="Start the shell for a workspace")
    build_parser.add_argument("workspace", metavar="WORKSPACE", help="Path or number to workspace", default='.')

    build_parser = subparsers.add_parser("list", help="List ros-docker workspaces")

    args = parser.parse_args()

    try:
        lock_file = open(LOCK_FILE_PATH, 'x')
    except FileExistsError:
        print(f"The file {LOCK_FILE_PATH} exists\nThis means that the program may not have successfully exited the previous time it ran")
        yn = input("Would you like to delete the file and contiinue regardless? [y/N]: ")
        if yn.lower() != 'y':
            exit(1)
        lock_file = open(LOCK_FILE_PATH)

    if not os.path.exists(os.path.dirname(INFO_FILE_PATH)):
        os.makedirs(os.path.dirname(INFO_FILE_PATH))

    info = []
    if os.path.exists(INFO_FILE_PATH):
        info_file = open(INFO_FILE_PATH, 'r')
        info = json.load(info_file)
        info_file.close()
    else:
        info_file = open(INFO_FILE_PATH, 'x+')
        json.dump([], info_file)
        info_file.close()

    running = []
    if os.path.exists(RUNNING_FILE_PATH):
        running_file = open(RUNNING_FILE_PATH, 'r')
        running = json.load(running_file)
        running_file.close()
    else:
        running_file = open(RUNNING_FILE_PATH, 'x+')
        json.dump([], running_file)
        running_file.close()

    match args.subcommand:
        case "build":
            build(info, args.path)
        case "run":
            run(info, running, args.workspace)
        case "stop":
            stop(info, running, args.workspace)
        case "list":
            list(info, running)
        case "rm":
            rm(info, args.workspace)
        case "new":
            new(args.path)
        case "shell":
            shell(info, running, args.workspace)

    info_file = open(INFO_FILE_PATH, 'w')
    json.dump(info, info_file)
    info_file.close()

    running_file = open(RUNNING_FILE_PATH, 'w')
    json.dump(running, running_file)
    running_file.close()

    lock_file.close()
    info_file.close()
    os.remove(LOCK_FILE_PATH)
    exit(EXIT_CODE)
