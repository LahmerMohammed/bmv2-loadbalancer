OS_RELEASE=Debian
VERSION_ID=11

BUILD_DIR=build
LOG_DIR=logs
PCAP_DIR =pcaps


DEFAULT_PROG =lb.p4
DEFAULT_JSON =$(BUILD_DIR)/$(DEFAULT_PROG:.p4=.json)


BMV2_SWITCH_EXE ?= simple_switch_grpc
BMV2_SWITCH_EXE_ARGS +=  -i 0@ens4 -i 1@ens5 --device-id 0 --thrift-port 9090 --log-file ${LOG_DIR}/bmv2.log --pcap ${PCAP_DIR} --nanolog ipc:///tmp/bm-log.ipc


P4C=p4c
P4C_ARGS += --target bmv2 --arch v1model


compiled_json := $(DEFAULT_PROG:.p4=.json)

#P4_VERSION=p4c 1.2.3.6 (SHA: ce01301 BUILD: RELEASE)
# simple switch version: 1.15.0-9f76fe9b

install:
    echo "deb https://download.opensuse.org/repositories/home:/p4lang/${OS_RELEASE}_${VERSION_ID}/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
    curl -fsSL https://download.opensuse.org/repositories/home:p4lang/${OS_RELEASE}_${VERSION_ID}/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_p4lang.gpg > /dev/null
    apt update
    apt install p4lang-p4c p4lang-bmv2 -y

	pip3 install virtualenv
	python3 -m venv p4lb
	source p4lb/bin/activate
	pip3 install -r requirements.txt

	git clone -n --depth=1 --filter=tree:0 https://github.com/p4lang/tutorials.git
	cd tutorials
	git sparse-checkout set --no-cone utils
	git checkout
	cd ..
	mv tutorials/utils .
	rm -rf tutorials

	cp -r /usr/lib/python3/dist-packages/p4/ ~/projects/thesis/utils



run: build
	sudo ${BMV2_SWITCH_EXE}  ${BMV2_SWITCH_EXE_ARGS} ${DEFAULT_JSON} &

build: dirs $(compiled_json)

%.json: %.p4
	$(P4C) --std p4-16 $(P4C_ARGS) -o $(BUILD_DIR)/$@ $<

dirs:
	mkdir -p ${BUILD_DIR} ${PCAP_DIR} ${LOG_DIR}

stop:
	sudo kill $(pidof sudo $(BMV2_SWITCH_EXE)) || true


clean: stop
	rm -rf $(BUILD_DIR) $(PCAP_DIR) $(LOG_DIR)


bmv2:	
	p4c --target bmv2 --arch v1model --std p4-16 lb.p4
	sudo simple_switch lb.json \ 
	-i 0@ens4 -i 1@ens5 \
	--device-id 0 \
	--thrift-port 9090 \
	--log-file bmv2.log \
	--nanolog ipc:///tmp/bm-log.ipc  &

	./behavioral-model/tools/runtime_CLI.py --thrift-port 9090 <<EOF
	table_add MyEgress.send_frame rewrite_mac 0 => 42:01:0a:c8:00:04 
	table_add MyEgress.send_frame  rewrite_mac 1 => 42:01:0a:c6:00:05

	table_add MyIngress.ecmp_group set_ecmp_group 55555 => 55555 1
	table_add MyIngress.snat_t snat_a 55555 1 => 10.198.0.2 42:01:0a:c6:00:01 10.198.0.5 30001 1 
	table_add MyIngress.reverse_snat_t reverse_snat_a 30001 =>  41.102.236.58 30002 42:01:0a:c8:00:01 34.154.94.220 0
	EOF

