# ROS Docker Workspaces
A simple python script to manage docker workspaces for ROS

# Usage
```
usage: run.py [-h] {new,build,rm,run,stop,list} ...

Manage docker containers for ROS

positional arguments:
  {new,build,rm,run,stop,list}
    new                 Set up a workspace
    build               Build a docker container for a workspace
    rm                  Delete a workspace
    run                 Run a docker container for a workspace
    stop                Stop a docker container for a workspace
    list                List ros-docker workspaces

options:
  -h, --help            show this help message and exit
```

# nVidia cards
-  Add the GPG key:

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
&& curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-	key add - \
&& curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
```

- Install the `nvidia-docker2` package

```bash
sudo apt-get update
sudo apt-get install -y nvidia-docker2
```

- If you are on arch then install `nvidia-container-toolkit`

```bash
yay -S nvidia-container-toolkit
```

- Restart the Docker daemon

```
sudo systemctl restart docker
```
