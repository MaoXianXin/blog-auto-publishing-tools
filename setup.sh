#!/usr/bin/env bash

# Function to display help information
display_help() {
  cat <<EOF
blog-auto-publish-tool Installation Script for POSIX operating systems.

EOF
}

# Helper function to check if variable is set and non-empty
env_var_exists() {
  if [[ -n "${!1}" ]]; then
    return 0
  else
    return 1
  fi
}


# Directory of the script
SCRIPT_DIR="$(cd -- $(dirname -- "$0") && pwd)"

DIR="$(PWD)"

# Function to install Python dependencies
install_python_dependencies() {
  local TEMP_REQUIREMENTS_FILE

  # Switch to local virtual env
  echo "Switching to virtual Python environment."
  if ! inDocker; then
    if command -v python3.10 >/dev/null; then
      python3.10 -m venv "$DIR/venv"
    elif command -v python3 >/dev/null; then
      python3 -m venv "$DIR/venv"
    else
      echo "Valid python3 or python3.10 binary not found."
      echo "Cannot proceed with the python steps."
      return 1
    fi

    # Activate the virtual environment
    source "$DIR/venv/bin/activate"
  fi

  case "$OSTYPE" in
    "lin"*)
        python "$SCRIPT_DIR/setup/setup_linux.py" --platform-requirements-file=requirements.txt
      ;;
    "darwin"*)
      if [[ "$(uname -m)" == "arm64" ]]; then
        python "$SCRIPT_DIR/setup/setup_linux.py" --platform-requirements-file=requirements.txt
      else
        python "$SCRIPT_DIR/setup/setup_linux.py" --platform-requirements-file=requirements.txt
      fi
      ;;
  esac

  if [ -n "$VIRTUAL_ENV" ] && ! inDocker; then
    if command -v deactivate >/dev/null; then
      echo "Exiting Python virtual environment."
      deactivate
    else
      echo "deactivate command not found. Could still be in the Python virtual environment."
    fi
  fi
}

# This must be set after the getopts loop to account for $DIR changes.
PARENT_DIR="$(dirname "${DIR}")"
VENV_DIR="$DIR/venv"

if [ -w "$PARENT_DIR" ] && [ ! -d "$DIR" ]; then
  echo "Creating install folder ${DIR}."
  mkdir "$DIR"
fi

if [ ! -w "$DIR" ]; then
  echo "We cannot write to ${DIR}."
  echo "Please ensure the install directory is accurate and you have the correct permissions."
  exit 1
fi

isContainerOrPod() {
  local cgroup=/proc/1/cgroup
  test -f $cgroup && (grep -qE ':cpuset:/(docker|kubepods)' $cgroup || grep -q ':/docker/' $cgroup)
}

isDockerBuildkit() {
  local cgroup=/proc/1/cgroup
  test -f $cgroup && grep -q ':cpuset:/docker/buildkit' $cgroup
}

isDockerContainer() {
  [ -e /.dockerenv ]
}

inDocker() {
  if isContainerOrPod || isDockerBuildkit || isDockerContainer; then
    return 0
  else
    return 1
  fi
}

# Start OS-specific detection and work
if [[ "$OSTYPE" == "lin"* ]]; then

  install_python_dependencies

elif [[ "$OSTYPE" == "darwin"* ]]; then
  # The initial setup script to prep the environment on macOS
  # xformers has been omitted as that is for Nvidia GPUs only

  if ! install_python_dependencies; then
    echo "You may need to install Python. The command for this is brew install python@3.10."
  fi

  echo -e "Setup finished! Run ./publish.sh to publish."
elif [[ "$OSTYPE" == "cygwin" ]]; then
  # Cygwin is a standalone suite of Linux utilities on Windows
  echo "This hasn't been validated on cygwin yet."
elif [[ "$OSTYPE" == "msys" ]]; then
  # MinGW has the msys environment which is a standalone suite of Linux utilities on Windows
  # "git bash" on Windows may also be detected as msys.
  echo "This hasn't been validated in msys 'mingw' on Windows yet."
fi
