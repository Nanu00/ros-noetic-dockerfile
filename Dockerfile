FROM ros:noetic

ARG UNAME
ARG UID
ARG GID
USER root

RUN . /opt/ros/noetic/setup.sh && \
    apt-get update && \
    apt-get install -y wget gnupg2 lsb-release && \
    apt-get install -y python3-colcon-common-extensions && \
    sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list' && \
    wget https://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add - && \
    apt-get update && \
    sudo apt-get install -y gazebo11

RUN sudo apt-get install -y rospack-tools && \
    apt-get install -y python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential && \
    apt-get install -y python3-rosdep && \
    apt-get install -y ros-noetic-catkin python3-catkin-tools

RUN . /opt/ros/noetic/setup.sh
ENV ROS_PACKAGE_PATH="/opt/ros/noetic/share"
RUN echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections
RUN sudo apt-get install -y ros-noetic-ackermann-msgs
RUN sudo apt-get install -y ros-noetic-base-local-planner
RUN sudo apt-get install -y ros-noetic-laser-filters
RUN sudo apt-get install -y ros-noetic-gazebo-ros
RUN sudo apt-get install -y ros-noetic-joint-limits-interface
RUN sudo apt-get install -y ros-noetic-ros-control
RUN sudo apt-get install -y ros-noetic-rviz
RUN sudo apt-get install -y ros-noetic-xacro
RUN sudo apt-get install -y ros-noetic-desktop-full
RUN wget https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc -O - | sudo apt-key add - && \
    sh -c 'echo "deb [arch=$(dpkg --print-architecture)]  http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'

RUN sudo apt-get install -y zsh zsh-autosuggestions zsh-syntax-highlighting git

RUN sudo apt-get install -y software-properties-common
RUN sudo add-apt-repository ppa:neovim-ppa/stable
RUN sudo apt-get update
RUN sudo apt-get install -y neovim
RUN sudo apt-get install -y python-dev python-pip-whl python3-dev python3-pip


RUN sudo update-alternatives --install /usr/bin/vi vi /usr/bin/nvim 60
RUN sudo update-alternatives --config vi
RUN sudo update-alternatives --install /usr/bin/vim vim /usr/bin/nvim 60
RUN sudo update-alternatives --config vim
RUN sudo update-alternatives --install /usr/bin/editor editor /usr/bin/nvim 60
RUN sudo update-alternatives --config editor

RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/zsh $UNAME
RUN usermod -aG sudo $UNAME
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER $UNAME

WORKDIR /home/$UNAME

RUN wget https://starship.rs/install.sh
RUN chmod +x install.sh
RUN sudo ./install.sh --yes
RUN rm install.sh
RUN echo eval \"\$\(starship init zsh\)\" >> ~/.zshrc
RUN mkdir ~/.config && touch ~/.config/starship.toml
RUN starship preset plain-text-symbols > ~/.config/starship.toml

RUN echo source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh >> ~/.zshrc
RUN echo source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh >> ~/.zshrc

RUN git clone https://github.com/Nanu00/nvim-config.git ~/.config/nvim
RUN nvim --headless +q
RUN nvim --headless -c 'autocmd User PackerComplete quitall' -c 'PackerSync'

RUN echo 'source /opt/ros/noetic/setup.zsh' >> ~/.zshrc
