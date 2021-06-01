import pytest
import os
import subprocess
import unittest
import time
import sys
import logging

# Create logger
logger = logging.getLogger()
fhandler = logging.FileHandler(filename='/tmp/test_integ.log', mode='a')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.setLevel(logging.DEBUG)


# I am not sure how exactly are these integ tests written and the rules of calling tests within tests, hence just declared a global variable
mounted_files = "global"
# CHANGE_PATH
fuse_mounted_files_list = "/tmp/Mounted_files.lst"
# CHANGE_NAME
mdh_core = "core-sfs"
# hardcoded the path for mounted_from for now. Can be later modified to be read from the json config file, or maybe an environment variable
# CHANGE_PATH
mounted_from="/home/sfsuser/Vaidehi/amos-rep/test_tree"

# I don't understand how to work with this "self" in python.


class TestIntegratedTool(unittest.TestCase):

    # Setup docker
    def setUp(self):
        print("/************************************* Entered setUp *************************************/")
        # Add docker stop $(docker ps -aq), docker rm $(docker ps -aq) -- may not be required now. Still keeping in comments if we have problems later and this is a resolution
        if not os.path.isfile('docker-compose.yml'):
            self.assertRaises(FileNotFoundError)

        # Check if mdh core is running
        is_core_up = subprocess.Popen(["docker", "container", "inspect", "-f",
	                              "'{{.State.Running}}'", mdh_core], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = is_core_up.communicate()
        if "true" not in out.decode():
            self.assertFalse("MDH CORE NOT RUNNING!!!")

        docker_compose_up=subprocess.Popen(["docker-compose", "up"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # docker_up_out, docker_up_err = docker_compose_up.communicate()
        # if docker_up_out.decode().find("error") == -1:
            # self.assertFalse("DOCKER-COMPOSE UP COULD NOT BE EXECUTED!!!")

        # Check if subprocess is running
        is_up=docker_compose_up.poll()

        # Returns 0 if subprocess is alive, otherwise 1
        if is_up is not None:
            docker_start = subprocess.Popen(
                ["docker", "container", "start", "synthetic-file-system"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            is_up = docker_start.poll()
            if is_up is not None:
                self.assertFalse(
                    "Container synthetic-file-system cannot be started!!")
        else:
            # Added sleep because docker takes time to be set up
            time.sleep(30)

        print("/************************************* Exiting setUp *************************************/")
    
    @pytest.mark.dependency()
    def test_mount(self):
        print("/************************************* Entered test_mount *************************************/")

        # Could be removed. More for my VM right now.
        docker_start=subprocess.Popen(
            ["docker", "container", "start", "synthetic-file-system"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        docker_start_out, docker_start_err=docker_start.communicate()
        docker_start_out = docker_start_out.decode()
        docker_start_err = docker_start_err.decode()

        # Run mount.sh
        # docker_mount = subprocess.Popen(["docker", "container", "exec", "-d", "synthetic-file-system", "./mount.sh"], capture_output=True)
        docker_mount=subprocess.Popen(["docker", "container", "exec", "-d", "synthetic-file-system",
                                         "./mount.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        docker_mount_out, docker_mount_err=docker_mount.communicate()
        docker_mount_out = docker_mount_out.decode()
        docker_mount_err = docker_mount_err.decode()
        if "failed" in docker_mount_err:
             self.assertFalse("ERROR RUNNING MOUNT.SH!!!")

        time.sleep(5)

        # goes into the container and gets a list of all files under fuse_mount and writes it to a file
        mounted_files=os.popen(
            'docker container exec synthetic-file-system /bin/sh -c "cd ..; cd /fuse_mount; find . -type f" ').read()
        f=open(fuse_mounted_files_list, 'w')
        print(mounted_files, file=f)
        f.close()

        # Throws error if file containing mounted data is empty
        if os.stat(fuse_mounted_files_list).st_size == 0:
            self.assertFalse("Mounted files list at " +
                             fuse_mounted_files_list, " empty!!!")

        print("/************************************* Exiting test_mount *************************************/")


    @pytest.mark.dependency(depends=['test_mount'])
    def test_dir_structure(self):
        print("/************************************* Entered test_dir_structure *************************************/")

        common_dir=mounted_from.split("/")

        # Read all fuse files into an array
        fuse_mounted_files=open(fuse_mounted_files_list, "r")
        fuse_abs_mount_lines=fuse_mounted_files.readlines()
        fuse_mounted_files.close()

        # transforms '/home/sfsuser/Vaidehi/amos-rep/test_tree/dir0/dir144/dir158/dir160/dir164/dir165/CNV-1699976-2.jpeg' into '/dir0/dir144/dir158/dir160/dir164/dir165/CNV-1699976-2.jpeg'
        fuse_mount_lines=[i.split(common_dir[-1], 1)[1]
                            for i in fuse_abs_mount_lines]

        # Checks if files found at mounted_from were actually mounted on the vfs
        for root, dirs, files in os.walk(mounted_from):
            for f in files:
                # /home/sfsuser/Vaidehi/amos-rep/test_tree/dir0/dir144/dir158/dir160/dir164/dir165/CNV-1699976-2.jpeg
                file_path=os.path.join(root, f)
                req_path=file_path.split(common_dir[-1])

                if (req_path[1] in fuse_mount_lines) == False:
                    self.assertRaises(FileNotFoundError)

        print("/************************************* Exiting test_dir_structure *************************************/")

    # Turn off docker services
    def tearDown(self):
        print("/************************************* Entered tearDown *************************************/")

        docker_compose_down=subprocess.Popen(["docker-compose", "down"])
        time.sleep(5)

        # Check if subprocess is running
        is_down=docker_compose_down.poll()

        # COuld do with an assertion error, I don't know which one.
        if is_down is None:
            self.assertFalse(
                "************** COULD NOT SHUT DOWN DOCKER **************")

        print("/************************************* Exiting tearDown *************************************/")
