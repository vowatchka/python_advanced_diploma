# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.define "dev" do |dev|
    dev.vm.box = "ubuntu/focal64"

    dev.vm.hostname = "dev"
    dev.vm.network "private_network", ip: "192.168.1.33"

    dev.vm.provider "virtualbox" do |v|
      v.memory = 1024
      v.cpus = 1
    end

    dev.vm.provision "ansible_local" do |ansible|
        ansible.verbose = "vv"
        ansible.install_mode = "pip"
        ansible.pip_install_cmd = "curl https://bootstrap.pypa.io/get-pip.py | sudo python3"
        ansible.playbook = "./ansible_scripts/provision/provision-dev.yml"
    end
  end
end
